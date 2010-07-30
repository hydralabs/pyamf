# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
C-extension for L{pyamf.amf3} Python module in L{PyAMF<pyamf>}.

@since: 0.4
"""

from cpython cimport *

cdef extern from "datetime.h":
    void PyDateTime_IMPORT()
    int PyDateTime_CheckExact(object)
    int PyDate_CheckExact(object)
    int PyTime_CheckExact(object)

cdef extern from "Python.h":
    PyObject *Py_True
    PyObject *Py_None

    bint PyClass_Check(object)
    bint PyType_CheckExact(object)

from cpyamf.util cimport cBufferedByteStream, BufferedByteStream

import types
import pyamf
from pyamf import util, xml
import datetime


cdef object MixedArray = pyamf.MixedArray
cdef object Undefined = pyamf.Undefined
cdef PyObject *BuiltinFunctionType = <PyObject *>types.BuiltinFunctionType
cdef PyObject *GeneratorType = <PyObject *>types.GeneratorType

Py_INCREF(<object>BuiltinFunctionType)
Py_INCREF(<object>GeneratorType)

PyDateTime_IMPORT


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

    def __cinit__(self):
        self.objects = IndexedCollection()

        self.clear()

    def __init__(self):
        self.clear()

    cpdef int clear(self) except -1:
        self.objects.clear()

        self.class_aliases = {}
        self.unicodes = {}
        self.extra = {}

        return 0

    cpdef inline object getObject(self, Py_ssize_t ref):
        return self.objects.getByReference(ref)

    cpdef inline Py_ssize_t getObjectReference(self, object obj) except -2:
        return self.objects.getReferenceTo(obj)

    cpdef inline Py_ssize_t addObject(self, object obj) except -1:
        return self.objects.append(obj)

    cpdef object getClassAlias(self, object klass):
        """
        Gets a class alias based on the supplied C{klass}.

        @param klass: The class object.
        @return: The L{ClassAlias} that is linked to C{klass}
        """
        cdef PyObject *ret
        cdef object alias, x

        try:
            return self.class_aliases[klass]
        except KeyError:
            pass

        try:
            alias = pyamf.get_class_alias(klass)
        except pyamf.UnknownClassAlias:
            if isinstance(klass, basestring):
                raise

            # no alias has been found yet .. check subclasses
            alias = util.get_class_alias(klass) or pyamf.ClassAlias
            meta = util.get_class_meta(klass)
            alias = alias(klass, defer=True, **meta)

            self.class_aliases[klass] = alias

        return alias

    cpdef unicode getStringForBytes(self, object s):
        """
        Returns the corresponding unicode object for a given string. If there
        is no unicode object, one is created.

        :since: 0.6
        """
        cdef object h = hash(s)
        cdef PyObject *ret = PyDict_GetItem(self.unicodes, h)

        if ret != NULL:
            return <object>ret

        cdef unicode u = s.decode('utf-8')

        self.unicodes[h] = u

        return u

    cpdef str getBytesForString(self, object u):
        """
        Returns the corresponding utf-8 encoded string for a given unicode
        object. If there is no string, one is encoded.

        :since: 0.6
        """
        cdef object h = hash(u)
        cdef PyObject *ret = PyDict_GetItem(self.unicodes, h)

        if ret != NULL:
            return <object>ret

        cdef str s = u.encode('utf-8')

        self.unicodes[h] = s

        return s


cdef class Codec(object):
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

    def __cinit__(self):
        self.stream = None
        self.strict = 0
        self.timezone_offset = None

    def __init__(self, stream=None, strict=False, timezone_offset=None):
        if not isinstance(stream, BufferedByteStream):
            stream = BufferedByteStream(stream)

        self.stream = <cBufferedByteStream>stream
        self.strict = strict

        self.timezone_offset = timezone_offset


cdef class Decoder(Codec):
    """
    Base AMF decoder.
    """

    cdef object readDate(self):
        raise NotImplementedError

    cpdef object readString(self, bint bytes=0):
        raise NotImplementedError

    cdef object readObject(self):
        raise NotImplementedError

    cdef object readNumber(self):
        raise NotImplementedError

    cdef inline object readNull(self):
        return None

    cdef inline object readUndefined(self):
        return Undefined

    cdef object readList(self):
        raise NotImplementedError

    cdef object readXML(self):
        raise NotImplementedError

    cpdef object readElement(self):
        """
        Reads an element from the data stream.
        """
        cdef Py_ssize_t pos = self.stream.tell()
        cdef char t

        if self.stream.at_eof():
            raise pyamf.EOStream

        self.stream.read_char(&t)

        try:
            return self.readConcreteElement(t)
        except IOError:
            self.stream.seek(pos)

            raise

        raise pyamf.DecodeError("Unsupported ActionScript type")

    cdef object readConcreteElement(self, char t):
        """
        The workhorse function. Overridden in subclasses
        """
        raise NotImplementedError


cdef class Encoder(Codec):
    """
    Base AMF encoder.
    """

    def __cinit__(self):
        self.func_cache = {}
        self.use_write_object = []

    cpdef int serialiseString(self, u) except -1:
        raise NotImplementedError

    cdef inline int writeType(self, char type) except -1:
        return self.stream.write(<char *>&type, 1)

    cdef int writeNull(self, object o) except -1:
        raise NotImplementedError

    cdef int writeUndefined(self, object o) except -1:
        raise NotImplementedError

    cdef int writeString(self, object o) except -1:
        raise NotImplementedError

    cdef int writeBytes(self, object o) except -1:
        raise NotImplementedError

    cdef int writeBoolean(self, object o) except -1:
        raise NotImplementedError

    cdef int writeInt(self, object o) except -1:
        raise NotImplementedError

    cdef int writeLong(self, object o) except -1:
        raise NotImplementedError

    cdef int writeNumber(self, object o) except -1:
        raise NotImplementedError

    cdef int writeDateTime(self, object o) except -1:
        raise NotImplementedError

    cdef int writeDate(self, object o) except -1:
        o = datetime.datetime.combine(o, datetime.time(0, 0, 0, 0))

        self.writeDateTime(o)

    cdef int writeXML(self, object o) except -1:
        raise NotImplementedError

    cpdef int writeList(self, object o, bint is_proxy=0) except -1:
        raise NotImplementedError

    cdef int writeTuple(self, object o) except -1:
        raise NotImplementedError

    cdef int writeDict(self, object o) except -1:
        raise NotImplementedError

    cdef int writeSequence(self, object iterable) except -1:
        """
        Encodes an iterable. The default is to write If the iterable has an al
        """
        try:
            alias = self.context.getClassAlias(iterable.__class__)
        except (AttributeError, pyamf.UnknownClassAlias):
            return self.writeList(iterable)

        if alias.external:
            # a is a subclassed list with a registered alias - push to the
            # correct method
            PyList_Append(self.use_write_object, type(iterable))

            return self.writeObject(iterable)

        return self.writeList(iterable)

    cpdef int writeObject(self, object o, bint is_proxy=0) except -1:
        raise NotImplementedError

    cdef int writeMixedArray(self, object o) except -1:
        raise NotImplementedError

    cdef inline int handleBasicTypes(self, object element, object py_type) except -1:
        """
        @return: 0 = handled, -1 = error, 1 = not handled
        """
        cdef int ret = 1

        if PyString_CheckExact(element):
            ret = self.writeBytes(element)
        elif PyUnicode_CheckExact(element):
            ret = self.writeString(element)
        elif <PyObject *>element == Py_None:
            ret = self.writeNull(element)
        elif PyBool_Check(element):
            ret = self.writeBoolean(element)
        elif PyInt_CheckExact(element):
            ret = self.writeInt(element)
        elif PyLong_CheckExact(element):
            ret = self.writeLong(element)
        elif PyFloat_CheckExact(element):
            ret = self.writeNumber(element)
        elif PyList_CheckExact(element):
            ret = self.writeList(element)
        elif PyTuple_CheckExact(element):
            ret = self.writeTuple(element)
        elif element is Undefined:
            ret = self.writeUndefined(element)
        elif PyDict_CheckExact(element):
            ret = self.writeDict(element)
        elif PyDateTime_CheckExact(element):
            ret = self.writeDateTime(element)
        elif PyDate_CheckExact(element):
            ret = self.writeDate(element)
        elif py_type is MixedArray:
            ret = self.writeMixedArray(element)
        elif PySequence_Contains(self.use_write_object, py_type):
            ret = self.writeObject(element)
        elif isinstance(element, (list, tuple)):
            ret = self.writeSequence(element)
        elif xml.is_xml(element):
            ret = self.writeXML(element)

        return ret

    cdef int checkBadTypes(self, object element, object py_type) except -1:
        if PyModule_CheckExact(element):
            raise pyamf.EncodeError("Cannot encode modules")
        elif PyMethod_Check(element):
            raise pyamf.EncodeError("Cannot encode methods")
        elif PyFunction_Check(element) or <PyObject *>py_type == BuiltinFunctionType:
            raise pyamf.EncodeError("Cannot encode functions")
        elif <PyObject *>py_type == GeneratorType:
            raise pyamf.EncodeError("Cannot encode generators")
        elif PyClass_Check(element) or PyType_CheckExact(element):
            raise pyamf.EncodeError("Cannot encode class objects")
        elif PyTime_CheckExact(element):
            raise pyamf.EncodeError('A datetime.time instance was found but '
                'AMF has no way to encode time objects. Please use '
                'datetime.datetime instead')

        return 0

    cdef PyObject *getCustomTypeFunc(self, data) except? NULL:
        cdef _CustomTypeFunc ret

        for type_, func in pyamf.TYPE_MAP.iteritems():
            try:
                if isinstance(data, type_):
                    ret = _CustomTypeFunc(self, func)

                    break
            except TypeError:
                if callable(type_) and type_(data):
                    ret = _CustomTypeFunc(self, func)

                    break

        if ret is None:
            return NULL

        Py_INCREF(ret)

        return <PyObject *>ret

    cpdef int writeElement(self, object element) except -1:
        cdef int ret = 0
        cdef object py_type = type(element)
        cdef PyObject *func = NULL
        cdef int use_proxy

        ret = self.handleBasicTypes(element, py_type)

        if ret == 1:
            func = PyDict_GetItem(self.func_cache, py_type)

            if func == NULL:
                func = self.getCustomTypeFunc(element)

                if func == NULL:
                    self.checkBadTypes(element, py_type)

                    PyList_Append(self.use_write_object, py_type)

                    return self.writeObject(element)

                PyDict_SetItem(self.func_cache, py_type, <object>func)

            (<object>func)(element)

        return ret


cdef class _CustomTypeFunc(object):
    """
    Support for custom type mappings when encoding.
    """

    cdef Encoder encoder
    cdef object func

    def __cinit__(self, Encoder encoder, func):
        self.encoder = encoder
        self.func = func

    def __call__(self, data, **kwargs):
        ret = self.func(data, encoder=self.encoder)

        if ret is not None:
            self.encoder.writeElement(ret)
