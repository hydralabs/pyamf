from cpyamf cimport codec

cdef class Codec(codec.Codec):
    cdef bint use_proxies

cdef class Encoder(Codec):
    cdef object _func_cache
    cdef object _use_write_object # list of types that are okay to short circuit to writeObject

    cpdef int writeString(self, object u, int writeType=*) except -1
    cdef int writeUnicode(self, object u, int writeType=*) except -1
    cdef inline int writeType(self, char type) except -1
    cdef int writeInt(self, object n) except -1
    cdef int writeLong(self, object n) except -1
    cdef int writeNumber(self, object n) except -1
    cdef int writeList(self, object n, int use_proxies=*) except -1
    cdef int writeTuple(self, object n) except -1
    cpdef int writeLabel(self, str e) except -1
    cpdef int writeMixedArray(self, object n, int use_proxies=*) except? -1
    cpdef int writeObject(self, object obj, int use_proxies=*) except -1
    cdef int writeByteArray(self, object obj) except -1
    cpdef int writeXML(self, obj, use_proxies) except -1
    cdef int writeDateTime(self, obj) except -1
    cdef int writeProxy(self, obj) except -1
    cpdef int writeElement(self, object element, object use_proxies=*) except -1
