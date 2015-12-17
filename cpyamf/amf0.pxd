from cpyamf cimport codec, util, amf3


cdef class Context(codec.Context):
    cdef amf3.Context amf3_context


cdef class Decoder(codec.Decoder):
    cdef public bint use_amf3
    cdef readonly Context context
    cdef amf3.Decoder amf3_decoder

    cdef object readAMF3(self)
    cdef object readLongString(self, bint bytes=?)
    cdef object readMixedArray(self)
    cdef object readReference(self)
    cdef object readTypedObject(self)
    cdef void readObjectAttributes(self, object obj_attrs)
    cdef object readBytes(self)
    cdef object readBoolean(self)


cdef class Encoder(codec.Encoder):
    cdef public bint use_amf3
    cdef readonly Context context
    cdef amf3.Encoder amf3_encoder

    cdef inline int _writeEndObject(self) except -1
    cdef int writeAMF3(self, o) except -1
    cdef int _writeDict(self, dict attrs) except -1
    cdef inline int writeReference(self, o) except -2
