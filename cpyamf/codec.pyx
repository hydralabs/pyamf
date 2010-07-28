# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
C-extension for L{pyamf.amf3} Python module in L{PyAMF<pyamf>}.

@since: 0.4
"""

from python cimport *

from cpyamf.util cimport cBufferedByteStream, BufferedByteStream


import pyamf
from pyamf import util


cdef class IndexedCollection(object):
    """
    Provides reference functionality for amf contexts.

    @see: L{pyamf.codec.IndexedCollection} for complete documentation
    """

    def __cinit__(self, bint use_hash=0):
        self.use_hash = use_hash

        self.data = NULL
        self.refs = {}
        self.size = -1
        self.length = -1

    def __init__(self, use_hash=False):
        self.use_hash = use_hash

        self.clear()

    property use_hash:
        def __get__(self):
            return self.use_hash

        def __set__(self, value):
            self.use_hash = value

    cdef void _clear(self):
        cdef Py_ssize_t i

        if self.data != NULL:
            for i from 0 <= i < self.length:
                Py_DECREF(<object>self.data[i])

            PyMem_Free(self.data)
            self.data = NULL

    def __dealloc__(self):
        self._clear()

    cdef int _actually_increase_size(self) except -1:
        cdef Py_ssize_t new_len = self.length
        cdef Py_ssize_t current_size = self.size
        cdef PyObject **cpy

        while new_len >= current_size:
            current_size *= 2

        if current_size != self.size:
            self.size = current_size

            cpy = <PyObject **>PyMem_Realloc(self.data, sizeof(PyObject *) * self.size)

            if cpy == NULL:
                self._clear()

                PyErr_NoMemory()

            self.data = cpy

        return 0

    cdef inline int _increase_size(self) except -1:
        if self.length < self.size:
            return 0

        return self._actually_increase_size()

    cpdef int clear(self) except -1:
        self._clear()

        self.length = 0
        self.size = 64

        self.data = <PyObject **>PyMem_Malloc(sizeof(PyObject *) * self.size)

        if self.data == NULL:
            PyErr_NoMemory()

        self.refs = {}

        return 0

    cpdef object getByReference(self, Py_ssize_t ref):
        if ref < 0 or ref >= self.length:
            return None

        return <object>self.data[ref]

    cdef inline object _ref(self, object obj):
        if self.use_hash:
            return hash(obj)

        return PyLong_FromVoidPtr(<void *>obj)

    cpdef Py_ssize_t getReferenceTo(self, object obj) except -2:
        cdef PyObject *p = <PyObject *>PyDict_GetItem(self.refs, self._ref(obj))

        if p == NULL:
            return -1

        return <Py_ssize_t>PyInt_AS_LONG(<object>p)

    cpdef Py_ssize_t append(self, object obj) except -1:
        self._increase_size()

        cdef object h = self._ref(obj)

        self.refs[h] = <object>self.length
        self.data[self.length] = <PyObject *>obj
        Py_INCREF(obj)

        self.length += 1

        return self.length - 1

    def __iter__(self):
        cdef list x = []
        cdef Py_ssize_t idx

        for idx from 0 <= idx < self.length:
            x.append(<object>self.data[idx])

        return iter(x)

    def __len__(self):
        return self.length

    def __richcmp__(self, object other, int op):
        cdef int equal
        cdef Py_ssize_t i
        cdef IndexedCollection s = self # this is necessary because cython does not see the c-space vars of the class for this func

        if PyDict_Check(other) == 1:
            equal = s.refs == other
        elif PyList_Check(other) != 1:
            equal = 0
        else:
            equal = 0

            if PyList_GET_SIZE(other) == s.length:
                equal = 1

                for i from 0 <= i < s.length:
                    if <object>PyList_GET_ITEM(other, i) != <object>s.data[i]:
                        equal = 0

                        break

        if op == 2: # ==
            return equal
        elif op == 3: # !=
            return not equal
        else:
            raise NotImplementedError

    def __getitem__(self, idx):
        return self.getByReference(idx)

    def __copy__(self):
        cdef IndexedCollection n = IndexedCollection(self.use_hash)

        return n


cdef class Context(object):
    """
    I hold the AMF context for en/decoding streams.

    @ivar objects: An indexed collection of referencable objects encountered
        during en/decoding.
    @type objects: L{util.IndexedCollection}
    @ivar class_aliases: A L{dict} of C{class} to L{ClassAlias}
    """

    property objects:
        def __get__(self):
            return self.objects

    def __cinit__(self):
        self.objects = IndexedCollection()

        self.clear()

    def __init__(self):
        self.clear()

    property extra_context:
        def __get__(self):
            return self.extra_context

        def __set__(self, value):
            self.extra_context = value

    cpdef int clear(self) except -1:
        self.objects.clear()

        self.class_aliases = {}
        self.unicodes = {}
        self.extra_context = {}

        return 0

    cpdef object getObject(self, Py_ssize_t ref):
        return self.objects.getByReference(ref)

    cpdef Py_ssize_t getObjectReference(self, object obj) except -2:
        return self.objects.getReferenceTo(obj)

    cpdef Py_ssize_t addObject(self, object obj) except -1:
        return self.objects.append(obj)

    cpdef object getClassAlias(self, object klass):
        """
        Gets a class alias based on the supplied C{klass}.

        @param klass: The class object.
        @return: The L{ClassAlias} that is linked to C{klass}
        """
        cdef PyObject *ret
        cdef object alias, x

        ret = PyDict_GetItem(self.class_aliases, klass)

        if ret != NULL:
            return <object>ret

        try:
            alias = pyamf.get_class_alias(klass)
        except pyamf.UnknownClassAlias:
            if isinstance(klass, basestring):
                raise

            # no alias has been found yet .. check subclasses
            alias = util.get_class_alias(klass) or pyamf.ClassAlias

            x = alias(klass)
            alias = x

            self.class_aliases[klass] = alias

        return alias

    cpdef object getUnicodeForString(self, object s):
        """
        Returns the corresponding unicode object for a given string. If there
        is no unicode object, one is created.

        :since: 0.6
        """
        cdef object h = hash(s)
        cdef PyObject *ret = PyDict_GetItem(self.unicodes, h)

        if ret != NULL:
            return <object>ret

        cdef unicode u = unicode(s, 'utf-8')

        self.unicodes[h] = u

        return u

    cpdef object getStringForUnicode(self, object u):
        """
        Returns the corresponding utf-8 encoded string for a given unicode
        object. If there is no string, one is encoded.

        :since: 0.6
        """
        cdef object h = hash(u)
        cdef PyObject *ret = PyDict_GetItem(self.unicodes, h)

        if ret != NULL:
            return <object>ret

        cdef object s = u.encode('utf-8')

        self.unicodes[h] = s

        return s


cdef class Codec:
    """
    Base class for Encoder/Decoder classes. Provides base functionality for
    managing codecs.
    """

    property stream:
        def __get__(self):
            return <BufferedByteStream>self.stream

        def __set__(self, value):
            if not isinstance(value, BufferedByteStream):
                value = BufferedByteStream(value)

            self.stream = <cBufferedByteStream>value

    property strict:
        def __get__(self):
            return self.strict

        def __set__(self, value):
            self.strict = value

    property timezone_offset:
        def __get__(self):
            return self.timezone_offset

        def __set__(self, value):
            self.timezone_offset = value

    property context:
        def __get__(self):
            return self.context

    def __init__(self, stream=None, context=None, strict=False, timezone_offset=None):
        if not isinstance(stream, BufferedByteStream):
            stream = BufferedByteStream(stream)

        if context is None:
            context = self.buildContext()

        self.stream = <cBufferedByteStream>stream
        self.context = context
        self.strict = strict

        self.timezone_offset = timezone_offset

    cdef Context buildContext(self):
        return Context()

    cdef PyObject *getCustomTypeFunc(self, data):
        cdef object ret = None

        for type_, func in pyamf.TYPE_MAP.iteritems():
            try:
                if isinstance(data, type_):
                    ret = CustomTypeFunc(self, func)

                    break
            except TypeError:
                if callable(type_) and type_(data):
                    ret = CustomTypeFunc(self, func)

                    break

        if ret is None:
            return NULL

        Py_INCREF(ret)

        return <PyObject *>ret

    cdef object getTypeMapFunc(self, data):
        cdef char *buf

        for t, method in self.type_map.iteritems():
            if not isinstance(data, t):
                continue

            if callable(method):
                return TypeMappedCallable(self, method)

            return getattr(self, method)

        return None


cdef class TypeMappedCallable:
    """
    A convienience class that provides the encoder instance to the typed
    callable.
    """

    cdef Codec encoder
    cdef object method

    def __init__(self, Codec dec, method):
        self.codec = dec
        self.method = method

    def __call__(self, *args, **kwargs):
        self.method(self.codec, *args, **kwargs)


class CustomTypeFunc(object):
    """
    Support for custom type mappings when encoding.
    """

    def __init__(self, encoder, func):
        self.encoder = encoder
        self.func = func

    def __call__(self, data, **kwargs):
        ret = self.func(data, encoder=self.encoder)

        if ret is not None:
            self.encoder.writeElement(ret)