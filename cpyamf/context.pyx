# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
C-extension for L{pyamf.amf3} Python module in L{PyAMF<pyamf>}.

@since: 0.4
"""

from python cimport *


from cpyamf.util cimport IndexedCollection
import pyamf
from pyamf import util


cdef class BaseContext:
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
        self.class_aliases = {}
        self.objects = IndexedCollection()
        self.proxied_objects = {}
        self.unicodes = {}
        self.extra_context = {}

    property extra_context:
        def __get__(self):
            return self.extra_context

        def __set__(self, value):
            self.extra_context = value

    cpdef int clear(self) except? -1:
        self.objects.clear()

        self.class_aliases = {}
        self.proxied_objects = {}
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
        cdef object alias

        ret = PyDict_GetItem(self.class_aliases, klass)

        if ret != NULL:
            return <object>ret

        try:
            alias = pyamf.get_class_alias(klass)
        except pyamf.UnknownClassAlias:
            # no alias has been found yet .. check subclasses
            alias = util.get_class_alias(klass)

        self.class_aliases[klass] = alias(klass)

        return alias

    cpdef object getProxyForObject(self, object obj):
        """
        Returns the proxied version of C{obj} as stored in the context, or
        creates a new proxied object and returns that.

        @see: L{pyamf.flex.proxy_object}
        @since: 0.6
        """
        cdef PyObject *ret = PyDict_GetItem(self.proxied_objects, PyLong_FromVoidPtr(<void *>obj))

        if ret != NULL:
            return <object>ret

        from pyamf import flex

        proxied = flex.proxy_object(obj)

        self.addProxyObject(obj, proxied)

        return proxied

    cpdef object getObjectForProxy(self, object proxy):
        """
        Returns the unproxied version of C{proxy} as stored in the context, or
        unproxies the proxy and returns that 'raw' object.

        @see: L{pyamf.flex.unproxy_object}
        @since: 0.6
        """
        cdef PyObject *ret = PyDict_GetItem(self.proxied_objects, PyLong_FromVoidPtr(<void *>proxy))

        if ret != NULL:
            return <object>ret

        from pyamf import flex

        obj = flex.unproxy_object(proxy)

        self.addProxyObject(obj, proxy)

        return obj

    cpdef int addProxyObject(self, object obj, object proxied) except? -1:
        """
        Stores a reference to the unproxied and proxied versions of C{obj} for
        later retrieval.

        @since: 0.6
        """
        self.proxied_objects[PyLong_FromVoidPtr(<void *>obj)] = proxied
        self.proxied_objects[PyLong_FromVoidPtr(<void *>proxied)] = obj

        return 0

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
