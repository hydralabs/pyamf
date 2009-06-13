# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE for details.

cdef extern from "Python.h":
    ctypedef struct PyObject:
        pass


cdef class cBufferedByteStream:
    cdef char _endian
    cdef char *buffer
    cdef int closed
    cdef Py_ssize_t pos
    cdef Py_ssize_t size # total size of the alloc'd buffer
    cdef Py_ssize_t length

    cdef inline Py_ssize_t tell(self) except? -1
    cdef int close(self) except? -1
    cdef int write(self, char *buf, Py_ssize_t size) except? -1
    cdef inline int complain_if_closed(self) except? -1
    cdef int _increase_buffer(self, Py_ssize_t size) except? -1
    cdef inline int has_available(self, Py_ssize_t size) except? -1
    cdef int read(self, char **buf, Py_ssize_t size) except? -1
    cdef int at_eof(self) except? -1
    cdef inline Py_ssize_t remaining(self) except? -1
    cdef int seek(self, Py_ssize_t pos, int mode=*) except? -1
    cdef object getvalue(self)
    cdef int peek(self, char **buf, Py_ssize_t size) except? -1
    cdef int truncate(self, Py_ssize_t size) except? -1
    cdef int consume(self) except? -1
    cdef int unpack_int(self, int num_bytes, long *ret) except? -1
    cdef int unpack_uint(self, int num_bytes, unsigned long *ret) except? -1
    cdef int pack_int(self, int num_bytes, long x) except? -1
    cdef int pack_uint(self, int num_bytes, unsigned long x) except? -1
    cdef int read_uchar(self, unsigned char *ret) except? -1
    cdef int read_char(self, char *ret) except? -1
    cdef int read_ushort(self, unsigned short *ret) except? -1
    cdef int read_short(self, short *ret) except? -1
    cdef int read_ulong(self, unsigned long *ret) except? -1
    cdef int read_long(self, long *ret) except? -1
    cdef int read_24bit_uint(self, unsigned long *ret) except? -1
    cdef int read_24bit_int(self, long *ret) except? -1
    cdef int write_uchar(self, unsigned char ret) except? -1
    cdef int write_char(self, char ret) except? -1
    cdef int write_ushort(self, unsigned short ret) except? -1
    cdef int write_short(self, short ret) except? -1
    cdef int write_ulong(self, unsigned long ret) except? -1
    cdef int write_long(self, long ret) except? -1
    cdef int write_24bit_uint(self, unsigned long ret) except? -1
    cdef int write_24bit_int(self, long ret) except? -1
    cdef object read_utf8_string(self, unsigned int l)
    cdef int write_utf8_string(self, object obj) except? -1
    cdef int read_double(self, double *obj) except? -1
    cdef int write_double(self, double val) except? -1
    cdef int read_float(self, float *x) except? -1
    cdef int write_float(self, float c) except? -1
    cdef int append(self, object obj) except? -1