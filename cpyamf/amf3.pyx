# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE for details.

"""
Python C-extensions for L{PyAMF<pyamf>}.

@since: 0.4
"""

cdef extern from "Python.h":
    ctypedef unsigned long size_t
    void *PyMem_Malloc(size_t n)
    void PyMem_Free(void *p)
    object PyString_FromStringAndSize(char *buffer, Py_ssize_t length)
    object PyInt_FromLong(long v)

cdef Py_ssize_t _encode_int(long n, char **buf):
    if n < 0:
        n += 0x20000000

    cdef Py_ssize_t size = 0
    cdef long real_value = n
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

cdef long _decode_int(object stream, int sign=0):
    cdef int n = 0
    cdef long result = 0
    cdef unsigned char b = <unsigned char>stream.read_uchar()

    while b & 0x80 != 0 and n < 3:
        result <<= 7
        result |= b & 0x7f
        b = <unsigned char>stream.read_uchar()
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

    return result

def encode_int(long n):
    if n >= 0x40000000:
        raise OverflowError("Out of range")

    cdef char *buf
    cdef Py_ssize_t size = _encode_int(n, &buf)
    cdef object o = PyString_FromStringAndSize(buf, size)

    PyMem_Free(buf)

    return o

def decode_int(stream, sign=False):
    return PyInt_FromLong(_decode_int(stream, <int>sign))
