# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE for details.

"""
C-extension for L{pyamf.amf3} Python module in L{PyAMF<pyamf>}.

@since: 0.4
"""

cdef extern from "Python.h":
    ctypedef unsigned long size_t
    void *PyMem_Malloc(size_t n)
    void PyMem_Free(void *p)
    object PyString_FromStringAndSize(char *buffer, Py_ssize_t length)
    object PyInt_FromLong(long v)


from cpyamf.util cimport cBufferedByteStream


cdef Py_ssize_t _encode_int(long i, char **buf) except? -1:
    # Use typecasting to get the twos complement representation of i
    cdef unsigned long n = (<unsigned long*>(<void *>(&i)))[0]

    cdef Py_ssize_t size = 0
    cdef unsigned long real_value = n
    cdef char changed = 0
    cdef unsigned char count = 0
    cdef char *bytes = NULL

    if n > 0x1fffff:
        size = 4
        bytes = <char *>PyMem_Malloc(size)
        changed = 1
        n = n >> 1
        bytes[count] = 0x80 | ((n >> 21) & 0xff)
        count += 1

    if n > 0x3fff:
        if size == 0:
            size = 3
            bytes = <char *>PyMem_Malloc(size)

        bytes[count] = 0x80 | ((n >> 14) & 0xff)
        count += 1

    if n > 0x7f:
        if size == 0:
            size = 2
            bytes = <char *>PyMem_Malloc(size)

        bytes[count] = 0x80 | ((n >> 7) & 0xff)
        count += 1

    if changed == 1:
        n = real_value

    if size == 0:
        size = 1

        bytes = <char *>PyMem_Malloc(size)

    if n > 0x1fffff:
        bytes[count] = n & 0xff
    else:
        bytes[count] = n & 0x7f

    buf[0] = bytes

    return size

cdef int _decode_int(cBufferedByteStream stream, long *ret, int sign=0) except? -1:
    cdef int n = 0
    cdef long result = 0
    cdef unsigned char b

    if stream.read_uchar(&b) == -1:
        return -1

    while b & 0x80 != 0 and n < 3:
        result <<= 7
        result |= b & 0x7f

        if stream.read_uchar(&b) == -1:
            return -1

        n += 1

    if n < 3:
        result <<= 7
        result |= b
    else:
        result <<= 8
        result |= b

        if result & 0x10000000 != 0:
            if sign == 1:
                result -= 0x20000000
            else:
                result <<= 1
                result += 1

    ret[0] = result

    return 0


def encode_int(long n):
    """
    Encode C{int}.

    @raise OverflowError: Out of range.
    """
    if n >= 0x10000000 or n < -0x10000000:
        raise OverflowError("Out of range")

    cdef char *buf = NULL
    cdef Py_ssize_t size = _encode_int(n, &buf)
    cdef object o = PyString_FromStringAndSize(buf, size)

    PyMem_Free(buf)

    return o

def decode_int(stream, sign=False):
    """
    Decode C{int}.
    """
    cdef long *result = NULL
    cdef object ret

    result = <long *>PyMem_Malloc(sizeof(long *))

    if result == NULL:
        raise MemoryError

    if _decode_int(<cBufferedByteStream>stream, result, <int>sign) == -1:
        PyMem_Free(result)

        raise RuntimeError('Unable to decode int')

    ret = PyInt_FromLong(result[0])

    PyMem_Free(result)

    return ret

