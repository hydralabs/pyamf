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

    cdef public bint use_hash
    cdef PyObject **data
    cdef dict refs
    cdef Py_ssize_t size
    cdef Py_ssize_t length

    cdef int _actually_increase_size(self) except -1
    cdef int _increase_size(self) except -1
    cdef void _clear(self)
    cpdef int clear(self) except -1
    cdef object _ref(self, object obj)
    cpdef object getByReference(self, Py_ssize_t ref)
    cpdef Py_ssize_t getReferenceTo(self, object obj) except -2
    cpdef Py_ssize_t append(self, object obj) except -1


cdef class ByteStringReferenceCollection(IndexedCollection):
    """
    There have been rare hash collisions within a single AMF payload causing
    corrupt payloads.

    Which strings cause collisions is dependent on the python runtime, each
    platform might have a slightly different implementation which means that
    testing is extremely difficult.
    """


cdef class Context(object):
    """
    C based version of ``pyamf.BaseContext``
    """

    cdef dict class_aliases
    cdef IndexedCollection objects
    cdef dict unicodes
    cdef dict _strings
    cdef public dict extra
    cdef public bint forbid_dtd
    cdef public bint forbid_entities

    cpdef int clear(self) except -1
    cpdef object getClassAlias(self, object klass)

    cpdef object getObject(self, Py_ssize_t ref)
    cpdef Py_ssize_t getObjectReference(self, object obj) except -2
    cpdef Py_ssize_t addObject(self, object obj) except -1

    cpdef unicode getStringForBytes(self, object s)
    cpdef str getBytesForString(self, object u)


cdef class Codec(object):
    """
    Base class for Encoder/Decoder classes. Provides base functionality for
    managing codecs.
    """

    cdef util.cBufferedByteStream stream
    cdef public bint strict
    cdef public object timezone_offset


cdef class Decoder(Codec):
    cdef unsigned int depth

    cdef object readDate(self)
    cpdef object readString(self)
    cdef object readObject(self)
    cdef object readNumber(self)
    cdef object readNull(self)
    cdef object readUndefined(self)
    cdef object readList(self)
    cdef object readXML(self)

    cdef object _readElement(self)
    cpdef object readElement(self)
    cdef object readConcreteElement(self, char t)

    cpdef int send(self, data) except -1
    cdef object finalise(self, object payload)


cdef class Encoder(Codec):
    """
    """

    cdef dict func_cache
    cdef list use_write_object
    cdef list bucket

    cpdef int serialiseString(self, u) except -1
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
    cdef int writeDate(self, object o) except -1
    cdef int writeXML(self, object o) except -1
    cpdef int writeList(self, object o, bint is_proxy=?) except -1
    cdef int writeTuple(self, object o) except -1
    cdef int writeSequence(self, object iterable) except -1
    cpdef int writeObject(self, object o, bint is_proxy=?) except -1
    cdef int writeDict(self, dict o) except -1
    cdef int writeMixedArray(self, object o) except -1
    cdef int writeGenerator(self, object) except -1

    cdef int handleBasicTypes(self, object element, object py_type) except -1
    cdef int checkBadTypes(self, object element, object py_type) except -1
    cpdef int writeElement(self, object element) except -1

    cpdef int send(self, data) except -1
