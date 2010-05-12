# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

cdef extern from "Python.h":
    ctypedef struct PyObject:
        pass

from cpyamf.util cimport IndexedCollection


cdef class BaseContext:
    """
    C based version of ``pyamf.BaseContext``
    """

    cdef dict class_aliases
    cdef IndexedCollection objects
    cdef dict proxied_objects
    cdef dict unicodes
    cdef dict extra_context

    cpdef int clear(self) except? -1
    cpdef object getObject(self, Py_ssize_t ref)
    cpdef Py_ssize_t getObjectReference(self, object obj) except -2
    cpdef Py_ssize_t addObject(self, object obj) except -1
    cpdef object getClassAlias(self, object klass)

    cpdef int addProxyObject(self, object obj, object proxied) except? -1
    cpdef object getProxyForObject(self, object obj)
    cpdef object getObjectForProxy(self, object proxy)

    cpdef object getUnicodeForString(self, object s)
    cpdef object getStringForUnicode(self, object u)
