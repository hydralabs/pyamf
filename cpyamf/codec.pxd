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


cdef class Codec(object):
    """
    Base class for Encoder/Decoder classes. Provides base functionality for
    managing codecs.
    """

    cdef util.cBufferedByteStream stream
    cdef Context context
    cdef bint strict
    cdef object timezone_offset

    cdef Context buildContext(self)
    cdef PyObject *getTypeFunc(self, data)


cdef class Encoder(Codec):
    """
    """

    cdef dict _func_cache
    cdef list _use_write_object

    cdef inline int writeType(self, char type) except -1
    cdef int writeNull(self, object o) except -1
    cdef int writeUndefined(self, object o) except -1
    cdef int writeString(self, object o) except -1
    cdef int writeBytes(self, object o) except -1
    cdef int writeBoolean(self, object o) except -1
    cdef int writeInt(self, object o) except -1
    cdef int writeLong(self, object o) except -1
    cdef int writeNumber(self, object o) except -1
    cdef int writeDateTime(self, object o) except -1
    cdef int writeXML(self, object o) except -1
    cdef int writeList(self, object o) except -1
    cdef int writeTuple(self, object o) except -1
    cdef int writeSequence(self, object iterable) except -1
    cdef int writeObject(self, object o) except -1
    cdef int writeMixedArray(self, object o) except -1

    cdef inline int handleBasicTypes(self, object element, object py_type) except -1
    cdef int checkBadTypes(self, object element, object py_type) except -1
    cdef PyObject *getCustomTypeFunc(self, data) except? NULL
    cpdef int writeElement(self, object element) except -1
