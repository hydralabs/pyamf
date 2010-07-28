# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
C-extension for L{pyamf.amf3} Python module in L{PyAMF<pyamf>}.

:since: 0.6
"""

from python cimport *

cdef extern from "math.h":
    float floor(float)

cdef extern from "stdlib.h" nogil:
    ctypedef unsigned long size_t

    int memcmp(void *dest, void *src, size_t)
    void *memcpy(void *, void *, size_t)


from cpyamf cimport codec, util
import pyamf


cdef char TYPE_NUMBER      = '\x00'
cdef char TYPE_BOOL        = '\x01'
cdef char TYPE_STRING      = '\x02'
cdef char TYPE_OBJECT      = '\x03'
cdef char TYPE_MOVIECLIP   = '\x04'
cdef char TYPE_NULL        = '\x05'
cdef char TYPE_UNDEFINED   = '\x06'
cdef char TYPE_REFERENCE   = '\x07'
cdef char TYPE_MIXEDARRAY  = '\x08'
cdef char TYPE_OBJECTTERM  = '\x09'
cdef char TYPE_ARRAY       = '\x0A'
cdef char TYPE_DATE        = '\x0B'
cdef char TYPE_LONGSTRING  = '\x0C'
cdef char TYPE_UNSUPPORTED = '\x0D'
cdef char TYPE_RECORDSET   = '\x0E'
cdef char TYPE_XML         = '\x0F'
cdef char TYPE_TYPEDOBJECT = '\x10'
cdef char TYPE_AMF3        = '\x11'


cdef class Encoder(codec.Encoder):
    """
    The AMF0 Encoder.
    """

    cdef bint use_amf3
    #cdef amf3.Encoder amf3_encoder

    property use_amf3:
        def __get__(self):
            return self.use_amf3

        def __set__(self, value):
            self.use_amf3 = value

    def __cinit__(self):
        self.use_amf3 = 0

    def __init__(self, *args, **kwargs):
        self.use_amf3 = kwargs.pop('use_amf3', 0)

        codec.Codec.__init__(self, *args, **kwargs)

    cdef inline int writeReference(self, o) except -2:
        """
        Write reference to the data stream.
        """
        cdef Py_ssize_t idx = self.context.getObjectReference(o)

        if idx == -1 or idx > 65535:
            return -1

        self.writeType(TYPE_REFERENCE)

        return self.stream.write_ushort(idx)

    cdef int writeBoolean(self, b) except -1:
        self.writeType(TYPE_BOOL)

        if b is True:
            return self.writeType('\x01')
        else:
            return self.writeType('\x00')

    cdef int writeUndefined(self, data) except -1:
        return self.writeType(TYPE_UNDEFINED)

    cdef int writeNull(self, n) except -1:
        """
        Write null type to data stream.
        """
        return self.writeType(TYPE_NULL)

    cdef int writeList(self, object a) except -1:
        """
        Write array to the stream.
        """
        cdef Py_ssize_t size, i

        if self.writeReference(a) != -1:
            return 0

        self.context.addObject(a)

        self.writeType(TYPE_ARRAY)
        size = PyList_GET_SIZE(a)

        self.stream.write_ulong(size)

        for i from 0 <= i < size:
            x = PyList_GET_ITEM(a, i)

            self.writeElement(<object>x)

        return 0

    cdef int writeTuple(self, object a) except -1:
        cdef Py_ssize_t size, i

        if self.writeReference(a) != -1:
            return 0

        self.context.addObject(a)

        self.writeType(TYPE_ARRAY)
        size = PyTuple_GET_SIZE(a)

        self.stream.write_ulong(size)

        for i from 0 <= i < size:
            x = PyTuple_GET_ITEM(a, i)

            self.writeElement(<object>x)

        return 0

    cdef int writeInt(self, object a) except -1:
        self.writeType(TYPE_NUMBER)

        return self.stream.write_double(a)

    cdef int writeNumber(self, n) except -1:
        self.writeType(TYPE_NUMBER)

        return self.stream.write_double(n)

    cdef int writeLong(self, object a):
        self.writeType(TYPE_NUMBER)

        return self.stream.write_double(a)

    cdef int writeBytes(self, s) except -1:
        """
        Write a string of bytes to the data stream.
        """
        cdef Py_ssize_t l = PyString_GET_SIZE(s)

        if l > 0xffff:
            self.writeType(TYPE_LONGSTRING)
        else:
            self.writeType(TYPE_STRING)

        if l > 0xffff:
            self.stream.write_ulong(l)
        else:
            self.stream.write_ushort(l)

        return self.stream.write(PyString_AS_STRING(s), l)

    cdef int writeString(self, u) except -1:
        """
        Write a unicode to the data stream.
        """
        cdef object s = self.context.getBytesForString(u)

        return self.writeBytes(s)

    cpdef int serialiseString(self, u) except -1:
        """
        Similar to L{writeString} but does not encode a type byte.
        """
        if PyUnicode_CheckExact(u):
            u = self.context.getBytesForString(u)

        cdef Py_ssize_t l = PyString_GET_SIZE(u)

        if l > 0xffff:
            self.stream.write_ulong(l)
        else:
            self.stream.write_ushort(l)

        return self.stream.write(PyString_AS_STRING(u), l)

    cdef int _writeDict(self, attrs) except -1:
        """
        Write C{dict} to the data stream.

        @param o: The C{dict} data to be encoded to the AMF0 data stream.
        """
        cdef Py_ssize_t ref = 0
        cdef PyObject *key = NULL
        cdef PyObject *value = NULL

        while PyDict_Next(attrs, &ref, &key, &value):
            self.serialiseString(<object>key)
            self.writeElement(<object>value)

        return 0

    cdef inline int _writeEndObject(self) except -1:
        return self.stream.write('\x00\x00\x09', 3)

    cdef int writeObject(self, o) except -1:
        """
        Write a Python object to the stream.

        @param o: The object data to be encoded to the AMF0 data stream.
        """
        if self.writeReference(o) != -1:
            return 0

        self.context.addObject(o)
        alias = self.context.getClassAlias(o.__class__)

        alias.compile()

        if alias.amf3:
            return self.writeAMF3(o)

        if alias.anonymous:
            self.writeType(TYPE_OBJECT)
        else:
            self.writeType(TYPE_TYPEDOBJECT)
            self.serialiseString(alias.alias)

        attrs = alias.getEncodableAttributes(o, codec=self)

        if not PyDict_CheckExact(attrs):
            raise TypeError('Expected dict from getEncodableAttributes')

        if alias.static_attrs and attrs:
            for key in alias.static_attrs:
                value = attrs.pop(key)

                self.serialiseString(key)
                self.writeElement(value)

        if attrs:
            self._writeDict(attrs)

        return self._writeEndObject()
