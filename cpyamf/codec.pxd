# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

cdef extern from "Python.h":
    ctypedef struct PyObject:
        pass


from cpyamf cimport util

cdef class IndexedCollection(object):
    """
    Provides reference functionality for amf contexts.
    """

    cdef bint use_hash
    cdef PyObject **data
    cdef object refs
    cdef Py_ssize_t size
    cdef Py_ssize_t length

    cdef int _actually_increase_size(self) except -1
    cdef int _increase_size(self) except? -1
    cdef void _clear(self)
    cpdef int clear(self) except -1
    cdef object _ref(self, object obj)
    cpdef object getByReference(self, Py_ssize_t ref)
    cpdef Py_ssize_t getReferenceTo(self, object obj) except -2
    cpdef Py_ssize_t append(self, object obj) except -1


cdef class Context(object):
    """
    C based version of ``pyamf.BaseContext``
    """

    cdef dict class_aliases
    cdef IndexedCollection objects
    cdef dict unicodes
    cdef dict extra_context

    cpdef int clear(self) except? -1
    cpdef object getClassAlias(self, object klass)

    cpdef object getObject(self, Py_ssize_t ref)
    cpdef Py_ssize_t getObjectReference(self, object obj) except -2
    cpdef Py_ssize_t addObject(self, object obj) except -1

    cpdef object getStringForBytes(self, object s)
    cpdef object getBytesForString(self, object u)
