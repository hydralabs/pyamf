# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE for details.

cdef extern from "stdlib.h":
    ctypedef unsigned long size_t

    int memcmp(void *dest, void *src, size_t)
    void *memcpy(void *, void *, size_t)

cdef extern from "stdio.h":
    int SIZEOF_LONG

cdef extern from "Python.h":
    ctypedef struct PyObject:
        pass

    PyObject *PyErr_Occurred()

    void Py_INCREF(PyObject *)
    void Py_DECREF(PyObject *)

    void *PyMem_Malloc(size_t)
    void *PyMem_Realloc(void *, size_t)
    void *PyMem_Free(void *)

    void PyErr_SetNone(object)
    void PyErr_SetString(object,char *)
    void PyErr_Clear()

    int PyUnicode_Check(object)
    int PyString_Check(object)
    int PyList_Check(object)
    int PyDict_Check(object)
    int PyInt_Check(object)
    int PyFloat_Check(object)
    int PyLong_Check(object)

    object PyString_FromStringAndSize(char *buf, Py_ssize_t size)
    int PyString_AsStringAndSize(object, char **buf, Py_ssize_t *size)

    object PyString_AsEncodedObject(object, char *, char *)
    object PyUnicode_DecodeUTF8(char *, Py_ssize_t, char *)
    object PyUnicode_AsUTF8String(object)
    char *PyString_AsString(object)

    int _PyFloat_Pack4(float, unsigned char *, int)
    int _PyFloat_Pack8(double, unsigned char *, int)
    float _PyFloat_Unpack4(unsigned char *, int)
    double _PyFloat_Unpack8(unsigned char *, int)
    object PyFloat_FromDouble(double)
    double PyFloat_AsDouble(object)

    PyObject *PyDict_GetItem(object, object)
    int PyDict_SetItem(object, object, object)
    long PyInt_AS_LONG(object)
    PyObject *PyList_GetItem(object, Py_ssize_t)
    Py_ssize_t PyList_GET_SIZE(object)
    int PyList_Append(object, object)
    int PyDict_DelItem(object, objec)
    object PyInt_FromSsize_t(Py_ssize_t)
    object PyList_GET_ITEM(object, Py_ssize_t)


# module constant declarations
DEF ENDIAN_NETWORK = "!"
DEF ENDIAN_NATIVE = "@"
DEF ENDIAN_LITTLE = "<"
DEF ENDIAN_BIG = ">"

cdef char SYSTEM_ENDIAN

cdef int float_broken = -1
cdef double NaN = float('nan')
cdef double NegInf = float('-inf')
cdef double PosInf = float('inf')
cdef double system_nan = float('nan')
cdef double system_posinf = float('inf')
cdef double system_neginf = float('-inf')

cdef int complete_init = 0

import fpconst

cdef int complete_import() except? -1:
    # this will be filled out later ..
    complete_init = 1

    return 0


cdef char get_native_endian():
    """
    A quick hack to determine the system's endian-ness ...

    @return: Either L{ENDIAN_LITTLE} or L{ENDIAN_BIG}
    """
    cdef unsigned int one = 1
    cdef int big_endian = (<char*>&one)[0] != 1

    if big_endian == 1:
        return ENDIAN_BIG
    else:
        return ENDIAN_LITTLE


cdef inline int is_big_endian(char endian):
    """
    Returns a boolean value whether the supplied C{endian} is big.
    """
    if endian == ENDIAN_NATIVE:
        return SYSTEM_ENDIAN == ENDIAN_BIG

    return endian == ENDIAN_NETWORK or endian == ENDIAN_BIG


cdef inline int is_native_endian(char endian):
    if endian == ENDIAN_NATIVE:
        return 1

    if endian == ENDIAN_NETWORK:
        endian = ENDIAN_BIG

    return endian == SYSTEM_ENDIAN


cdef inline int swap_bytes(unsigned char *buffer, Py_ssize_t size) except? -1:
    cdef unsigned char *buf = <unsigned char *>PyMem_Malloc(sizeof(unsigned char *) * size)

    if buf == NULL:
        raise MemoryError

    cdef Py_ssize_t i

    for i from 0 <= i < size:
        buf[i] = buffer[size - i - 1]

    memcpy(buffer, buf, size)
    PyMem_Free(buf)

    return 0


cdef int is_broken_float() except? -1:
    cdef double test = _PyFloat_Unpack8(<unsigned char *>&NaN, not is_big_endian(SYSTEM_ENDIAN))

    if test == -1.0 and PyErr_Occurred() != NULL:
        return -1

    return memcmp(&NaN, <unsigned char *>&test, 8) != 0


cdef class cBufferedByteStream:
    def __cinit__(self):
        if complete_init == 0:
            complete_import()

        self._endian = ENDIAN_NETWORK
        self.pos = 0
        self.length = 0
        self.size = 1024
        self.closed = 0

        self.buffer = <char *>PyMem_Malloc(sizeof(char *) * self.size)

        if self.buffer == NULL:
            raise MemoryError

    def __dealloc__(self):
        if self.buffer != NULL:
            PyMem_Free(self.buffer)

        self.buffer = NULL

    cdef int close(self) except? -1:
        self.closed = 1

        return 0

    cdef inline int complain_if_closed(self) except? -1:
        if self.closed == 1:
            raise IOError('Buffer closed')

        return 0

    cdef inline Py_ssize_t tell(self) except? -1:
        return self.pos

    cdef int _increase_buffer(self, Py_ssize_t size) except? -1:
        cdef unsigned long new_len = self.length + size
        cdef unsigned long current_size = self.size

        while new_len > current_size:
            current_size *= 2

        if current_size != self.size:
            self.size = current_size

            self.buffer = <char *>PyMem_Realloc(self.buffer, sizeof(char *) * self.size)

            if self.buffer == NULL:
                raise MemoryError

        return 0

    cdef int write(self, char *buf, Py_ssize_t size) except? -1:
        if self.complain_if_closed() == -1:
            return -1

        if size == 0:
            return 0

        if self._increase_buffer(size) == -1:
            return -1

        memcpy(self.buffer + self.pos, buf, size)

        if self.pos + size > self.length:
            self.length = self.pos + size

        self.pos += size

        return 0

    cdef inline int has_available(self, Py_ssize_t size) except? -1:
        if size == 0:
            return 0

        if self.length == self.pos:
            raise IOError

        if self.pos + size > self.length:
            if size == 1:
                raise IOError

            raise IOError

        return 0

    cdef int read(self, char **buf, Py_ssize_t size) except? -1:
        if self.complain_if_closed() == -1:
            return -1

        if size == -1:
            size = self.remaining()

            if size == 0:
                size = 1

        if self.has_available(size) == -1:
            return -1

        buf[0] = <char *>PyMem_Malloc(sizeof(char *) * size)

        if not buf[0]:
            raise MemoryError

            return -1

        memcpy(buf[0], self.buffer + self.pos, size)
        self.pos += size

        return 0

    cdef inline int at_eof(self) except? -1:
        if self.complain_if_closed() == -1:
            return -1

        return self.length == self.pos

    cdef inline Py_ssize_t remaining(self) except? -1:
        if self.complain_if_closed() == -1:
            return -1

        return self.length - self.pos

    cdef int seek(self, Py_ssize_t pos, int mode=0) except? -1:
        # mode 0: absolute; 1: relative; 2: relative to EOF

        if self.complain_if_closed() == -1:
            return -1

        if mode == 0:
            if pos < 0 or pos > self.length:
                raise IOError()

            self.pos = pos
        elif mode == 1:
            if pos + self.pos < 0 or pos + self.pos > self.length:
                raise IOError()

            self.pos += pos
        elif mode == 2:
            if pos + self.length < 0 or pos + self.length > self.length:
                raise IOError()

            self.pos = self.length + pos
        else:
            raise ValueError('Bad value for mode')

        return 0

    cdef object getvalue(self):
        if self.complain_if_closed() == -1:
            return None

        return PyString_FromStringAndSize(self.buffer, self.length)

    cdef int peek(self, char **buf, Py_ssize_t size) except? -1:
        if self.complain_if_closed() == -1:
            return -1

        cdef Py_ssize_t cur_pos = self.pos

        if self.read(buf, size) == -1:
            return -1

        self.pos = cur_pos

        return 0

    cdef int truncate(self, Py_ssize_t size) except? -1:
        if self.complain_if_closed() == -1:
            return -1

        if size > self.length:
            raise IOError()

        if size == 0:
            PyMem_Free(self.buffer)

            self.pos = 0
            self.length = 0
            self.size = 1024

            self.buffer = <char *>PyMem_Malloc(sizeof(char *) * self.size)

            if self.buffer == NULL:
                raise MemoryError()

            return 0

        cdef char *buf = NULL
        cdef Py_ssize_t cur_pos = self.pos

        if self.seek(0) == -1:
            return -1

        if self.peek(&buf, size) == -1:
            return -1

        PyMem_Free(self.buffer)
        self.size = 1024
        self.length = 0
        self.buffer = <char *>PyMem_Malloc(sizeof(char *) * self.size)

        if self.buffer == NULL:
            raise MemoryError

        if self.write(buf, size) == -1:
            return -1

        PyMem_Free(buf)

        if self.length > cur_pos:
            self.pos = self.length
        else:
            if self.seek(cur_pos, 0) == -1:
                return -1

        return 0

    cdef int consume(self) except? -1:
        if self.complain_if_closed() == -1:
            return -1

        cdef char *buf = NULL
        cdef Py_ssize_t size = self.remaining()

        if size > 0:
            if self.peek(&buf, size) == -1:
                return -1

        PyMem_Free(self.buffer)
        self.size = 1024
        self.length = 0
        self.buffer = <char *>PyMem_Malloc(sizeof(char *) * self.size)
        self.pos = 0

        if self.buffer == NULL:
            raise MemoryError

        if size > 0:
            if self.write(buf, size) == -1:
                return -1

            PyMem_Free(buf)

        self.pos = 0

        return 0

    cdef int unpack_int(self, int num_bytes, long *ret) except? -1:
        """
        Unpacks a long from C{buf}.
        """
        if self.has_available(num_bytes) == -1:
            return -1

        cdef int nb = num_bytes
        cdef long x = 0
        cdef int bytes_left = num_bytes
        cdef unsigned char *bytes = <unsigned char *>(self.buffer + self.pos)

        if is_big_endian(self._endian):
            while bytes_left > 0:
                x = (x << 8) | bytes[0]
                bytes += 1
                bytes_left -= 1
        else:
            while bytes_left > 0:
                x = (x << 8) | bytes[bytes_left - 1]
                bytes_left -= 1

        if SIZEOF_LONG > num_bytes:
            x |= -(x & (1L << ((8 * num_bytes) - 1)))

        self.pos += nb

        ret[0] = x

        return 0

    cdef int unpack_uint(self, int num_bytes, unsigned long *ret) except? -1:
        """
        Unpacks an unsigned long from C{buf}.
        """
        cdef int nb = num_bytes

        if self.has_available(num_bytes) == -1:
            return -1

        cdef unsigned long x = 0
        cdef unsigned char *bytes = <unsigned char *>(self.buffer + self.pos)

        if is_big_endian(self._endian):
            while num_bytes > 0:
                x = (x << 8) | bytes[0]
                bytes += 1
                num_bytes -= 1
        else:
            while num_bytes > 0:
                x = (x << 8) | bytes[num_bytes - 1]
                num_bytes -= 1

        self.pos += nb

        ret[0] = x

        return 0

    cdef int pack_int(self, int num_bytes, long x) except? -1:
        cdef long maxint = 1
        cdef long minint = -1

        if num_bytes != SIZEOF_LONG:
            maxint = (maxint << (num_bytes * 8 - 1)) - 1
            minint = (-maxint) - 1

            if x > maxint or x < minint:
                raise OverflowError('integer out of range')

        cdef char *buf = <char *>PyMem_Malloc(num_bytes)

        if buf == NULL:
            raise MemoryError

        cdef long i = num_bytes

        if is_big_endian(self._endian):
            while i > 0:
                i -= 1
                buf[i] = <char>x
                x >>= 8
        else:
            while i > 0:
                buf[num_bytes - i] = <char>x
                i -= 1
                x >>= 8

        self.write(buf, num_bytes)
        PyMem_Free(buf)

        return 0

    cdef int pack_uint(self, int num_bytes, unsigned long x) except? -1:
        """
        Packs an unsigned long into a buffer.
        """
        cdef unsigned long maxint = 1

        if num_bytes != SIZEOF_LONG:
            maxint <<= <unsigned long>(num_bytes * 8)

            if x >= maxint:
                raise OverflowError('integer out of range')

        cdef char *buf = <char *>PyMem_Malloc(sizeof(char *) * num_bytes)

        if not buf:
            raise MemoryError

        cdef long i = num_bytes

        if is_big_endian(self._endian):
            while i > 0:
                i -= 1
                buf[i] = <char>x
                x >>= 8
        else:
            while i > 0:
                buf[num_bytes - i] = <char>x
                i -= 1
                x >>= 8

        self.write(buf, num_bytes)
        PyMem_Free(buf)

        return 0

    cdef int read_uchar(self, unsigned char *ret) except? -1:
        return self.unpack_uint(1, <unsigned long *>ret)

    cdef int read_char(self, char *ret) except? -1:
        return self.unpack_int(1, <long *>ret)

    cdef int read_ushort(self, unsigned short *ret) except? -1:
        return self.unpack_uint(2, <unsigned long *>ret)

    cdef int read_short(self, short *ret) except? -1:
        return self.unpack_int(2, <long *>ret)

    cdef int read_ulong(self, unsigned long *ret) except? -1:
        return self.unpack_uint(4, ret)

    cdef int read_long(self, long *ret) except? -1:
        return self.unpack_int(4, ret)

    cdef int read_24bit_uint(self, unsigned long *ret) except? -1:
        return self.unpack_uint(3, <unsigned long *>ret)

    cdef int read_24bit_int(self, long *ret) except? -1:
        return self.unpack_int(3, <long *>ret)

    cdef int write_uchar(self, unsigned char ret) except? -1:
        return self.pack_uint(1, <unsigned long>ret)

    cdef int write_char(self, char ret) except? -1:
        return self.pack_int(1, <long>ret)

    cdef int write_ushort(self, unsigned short ret) except? -1:
        return self.pack_uint(2, <unsigned long>ret)

    cdef int write_short(self, short ret) except? -1:
        return self.pack_int(2, <long>ret)

    cdef int write_ulong(self, unsigned long ret) except? -1:
        return self.pack_uint(4, ret)

    cdef int write_long(self, long ret) except? -1:
        return self.pack_int(4, ret)

    cdef int write_24bit_uint(self, unsigned long ret) except? -1:
        return self.pack_uint(3, ret)

    cdef int write_24bit_int(self, long ret) except? -1:
        return self.pack_int(3, ret)

    cdef object read_utf8_string(self, unsigned int l):
        cdef char* buf = NULL
        cdef object ret

        if l == 0:
            return unicode('')

        if self.read(&buf, l) == -1:
            if buf != NULL:
                PyMem_Free(buf)

            return

        ret = PyUnicode_DecodeUTF8(buf, l, 'strict')
        PyMem_Free(buf)

        return ret

    cdef int write_utf8_string(self, object obj) except? -1:
        cdef object encoded_string
        cdef char *buf = NULL
        cdef Py_ssize_t l = -1

        if PyUnicode_Check(obj) == 1:
            encoded_string = PyUnicode_AsUTF8String(obj)
        elif PyString_Check(obj) == 1:
            encoded_string = obj
        else:
            raise TypeError('value must be Unicode or str')

        if <PyObject *>encoded_string == NULL:
            return -1

        if PyString_AsStringAndSize(encoded_string, &buf, &l) == -1:
            return -1

        if self.write(buf, l) == -1:
            return -1

        return 0

    cdef int read_double(self, double *obj) except? -1:
        cdef char *buf = NULL
        cdef int done = 0

        if self.read(&buf, 8) == -1:
            if buf != NULL:
                PyMem_Free(buf)

            return -1

        if float_broken:
            if not is_native_endian(self._endian):
                swap_bytes(<unsigned char *>buf, 8)

            if memcmp(buf, &NaN, 8) == 0:
                memcpy(obj, &NaN, 8)
                done = 1
            elif memcmp(obj, &PosInf, 8) == 0:
                memcpy(obj, &PosInf, 8)
                done = 1
            elif memcmp(obj, &NegInf, 8) == 0:
                memcpy(obj, &NegInf, 8)
                done = 1

            if done == 1:
                return 0

            if not is_native_endian(self._endian):
                swap_bytes(<unsigned char *>buf, 8)

        obj[0] = _PyFloat_Unpack8(<unsigned char *>buf, not is_big_endian(self._endian))
        PyMem_Free(buf)

        return 0

    cdef int write_double(self, double val) except? -1:
        cdef unsigned char *buf
        cdef int done = 0

        buf = <unsigned char *>PyMem_Malloc(sizeof(unsigned char *) * 8)

        if buf == NULL:
            raise MemoryError

        if float_broken:
            if memcmp(&val, &system_nan, 8) == 0:
                memcpy(buf, &NaN, 8)
                done = 1
            elif memcmp(&val, &system_neginf, 8) == 0:
                memcpy(buf, &NegInf, 8)
                done = 1
            elif memcmp(&val, &system_posinf, 8) == 0:
                memcpy(buf, &PosInf, 8)
                done = 1

            if done == 1 and not is_big_endian(self._endian):
                swap_bytes(<unsigned char *>buf, 8)

        if done == 0:
            if _PyFloat_Pack8(val, <unsigned char *>buf, not is_big_endian(self._endian)) == -1:
                PyMem_Free(buf)

                return -1

        if self.write(<char *>buf, 8) == -1:
            return -1

        PyMem_Free(buf)

        return 0

    cdef int read_float(self, float *x):
        cdef char *buf = NULL
        cdef unsigned char le = 0

        if self.read(&buf, 4) == -1:
            if buf != NULL:
                PyMem_Free(buf)

            return -1

        if not is_big_endian(self._endian):
            le = 1

        x[0] = _PyFloat_Unpack4(<unsigned char *>buf, le)
        PyMem_Free(buf)

        return 0

    cdef int write_float(self, float c):
        cdef unsigned char *buf
        cdef unsigned char le = 1

        buf = <unsigned char *>PyMem_Malloc(sizeof(unsigned char *) * 4)

        if buf == NULL:
            raise MemoryError()

        if is_big_endian(self._endian):
            le = 0

        if _PyFloat_Pack4(c, <unsigned char *>buf, le) == -1:
            PyMem_Free(buf)

            return -1

        if self.write(<char *>buf, 4) == -1:
            return -1

        PyMem_Free(buf)

        return 0


cdef class BufferedByteStream(cBufferedByteStream):

    def __init__(self, buf=None):
        cdef Py_ssize_t i
        cdef cBufferedByteStream x

        if isinstance(buf, cBufferedByteStream):
            x = <cBufferedByteStream>buf
            self.write(x.getvalue())
        elif isinstance(buf, (str, unicode)):
            self.write(buf)
        elif hasattr(buf, 'getvalue'):
            self.write(buf.getvalue())
        elif hasattr(buf, 'read') and hasattr(buf, 'seek') and hasattr(buf, 'tell'):
            old_pos = buf.tell()
            buf.seek(0)
            self.write(buf.read())
            buf.seek(old_pos)
        elif buf is None:
            pass
        else:
            raise TypeError("Unable to coerce buf->StringIO")

        self.seek(0)

    property endian:
        def __set__(self, value):
            if PyString_Check(value) == 0:
                raise TypeError('String value expected')

            if value not in [ENDIAN_NETWORK, ENDIAN_NATIVE, ENDIAN_LITTLE, ENDIAN_BIG]:
                raise ValueError('Not a valid endian type')

            self._endian = PyString_AsString(value)[0]

        def __get__(self):
            return PyString_FromStringAndSize(&self._endian, 1)

    def read(self, size=-1):
        cdef Py_ssize_t s
        cdef object cls

        if size != -1:
            s = <Py_ssize_t>size
        else:
            s = cBufferedByteStream.remaining(self)

            if s == 0:
                s = 1

        cdef char *buf = NULL

        if cBufferedByteStream.read(self, &buf, s) == -1:
            if buf != NULL:
                PyMem_Free(buf)

            cls = <object>PyErr_Occurred()
            raise cls()

        r = PyString_FromStringAndSize(buf, s)
        PyMem_Free(buf)

        return r

    def write(self, x):
        cBufferedByteStream.write_utf8_string(self, x)

    def close(self):
        cBufferedByteStream.close(self)

    def flush(self):
        # no-op
        pass

    def tell(self):
        return self.pos

    def remaining(self):
        return cBufferedByteStream.remaining(self)

    def __len__(self):
        return self.length

    def getvalue(self):
        return cBufferedByteStream.getvalue(self)

    def at_eof(self):
        cdef int result = cBufferedByteStream.at_eof(self)

        return (result == 1)

    def seek(self, pos, mode=0):
        cBufferedByteStream.seek(self, pos, mode)

    def peek(self, size=1):
        cdef char *buf = NULL
        cdef Py_ssize_t l

        if size == -1:
            l = cBufferedByteStream.remaining(self)
        else:
            l = <int>size

        cBufferedByteStream.peek(self, &buf, l)

        r = PyString_FromStringAndSize(buf, l)
        PyMem_Free(buf)

        return r

    def truncate(self, int size=0):
        cBufferedByteStream.truncate(self, size)

    def consume(self):
        cBufferedByteStream.consume(self)

    def read_uchar(self):
        cdef unsigned char ret

        cBufferedByteStream.read_uchar(self, &ret)

        return ret

    def read_char(self):
        cdef char ret

        cBufferedByteStream.read_char(self, &ret)

        return ret

    def read_ushort(self):
        cdef unsigned short ret

        cBufferedByteStream.read_ushort(self, &ret)

        return ret

    def read_short(self):
        cdef short ret

        cBufferedByteStream.read_short(self, &ret)

        return ret

    def read_ulong(self):
        cdef unsigned long ret

        cBufferedByteStream.read_ulong(self, &ret)

        return ret

    def read_long(self):
        cdef long ret

        cBufferedByteStream.read_long(self, &ret)

        return ret

    def read_24bit_uint(self):
        cdef unsigned long ret

        cBufferedByteStream.read_24bit_uint(self, &ret)

        return ret

    def read_24bit_int(self):
        cdef long ret

        cBufferedByteStream.read_24bit_int(self, &ret)

        return ret

    def write_uchar(self, x):
        if PyInt_Check(x) == 0 and PyLong_Check(x) == 0:
            raise TypeError('expected int for val')

        cBufferedByteStream.write_uchar(self, <unsigned char>x)

    def write_char(self, x):
        if PyInt_Check(x) == 0 and PyLong_Check(x) == 0:
            raise TypeError('expected int for val')

        cBufferedByteStream.write_char(self, <char>x)

    def write_ushort(self, x):
        if PyInt_Check(x) == 0 and PyLong_Check(x) == 0:
            raise TypeError('expected int for val')

        cBufferedByteStream.write_ushort(self, <unsigned short>x)

    def write_short(self, x):
        if PyInt_Check(x) == 0 and PyLong_Check(x) == 0:
            raise TypeError('expected int for val')

        cBufferedByteStream.write_short(self, <short>x)

    def write_ulong(self, x):
        if PyInt_Check(x) == 0 and PyLong_Check(x) == 0:
            raise TypeError('expected int for val')

        if x > 4294967295L or x < 0:
            raise OverflowError

        cBufferedByteStream.write_ulong(self, <unsigned long>x)

    def write_long(self, long x):
        cBufferedByteStream.write_long(self, x)

    def write_24bit_uint(self, unsigned long x):
        cBufferedByteStream.write_24bit_uint(self, x)

    def write_24bit_int(self, long x):
        cBufferedByteStream.write_24bit_int(self, x)

    def read_utf8_string(self, unsigned int size):
        return cBufferedByteStream.read_utf8_string(self, size)

    def write_utf8_string(self, obj):
        cBufferedByteStream.write_utf8_string(self, obj)

    def read_double(self):
        cdef double x

        if cBufferedByteStream.read_double(self, &x) == -1:
            return

        if float_broken:
            if memcmp(&x, &NaN, 8) == 0:
                return fpconst.NaN
            elif memcmp(&x, &NegInf, 8) == 0:
                return fpconst.NegInf
            elif memcmp(&x, &PosInf, 8) == 0:
                return fpconst.PosInf

        return PyFloat_FromDouble(x)

    def write_double(self, val):
        if PyFloat_Check(val) == 0:
            raise TypeError('Expecting float for val')

        cdef double x = PyFloat_AsDouble(val)
        cdef int done = 0

        if float_broken:
            if memcmp(&x, &NaN, 8) == 0:
                done = 1
            elif memcmp(&x, &NegInf, 8) == 0:
                done = 1
            elif memcmp(&x, &PosInf, 8) == 0:
                done = 1

            if done == 1:
                if is_big_endian(SYSTEM_ENDIAN):
                    if not is_big_endian(self._endian):
                        swap_bytes(<unsigned char *>&x, 8)
                else:
                    if is_big_endian(self._endian):
                        swap_bytes(<unsigned char *>&x, 8)

                cBufferedByteStream.write(self, <char *>&x, 8)

                return

        cBufferedByteStream.write_double(self, x)

    def read_float(self):
        cdef float x

        if cBufferedByteStream.read_float(self, &x) == -1:
            return

        return PyFloat_FromDouble(x)

    def write_float(self, x):
        if PyFloat_Check(x) == 0:
            raise TypeError('Expecting float for val')

        cBufferedByteStream.write_float(self, <float>x)

    def __add__(self, other):
        cdef long old_pos = <long>self.tell()
        cdef long old_other_pos = <long>other.tell()

        new = BufferedByteStream(self)

        other.seek(0)
        new.seek(0, 2)
        new.write(other.read())

        self.seek(old_pos)
        other.seek(old_other_pos)
        new.seek(0)

        return new

    def __str__(self):
        return cBufferedByteStream.getvalue(self)


# init module here
SYSTEM_ENDIAN = get_native_endian()

if is_broken_float():
    float_broken = 1

    system_nan = _PyFloat_Unpack8(<unsigned char *>&NaN, not is_big_endian(SYSTEM_ENDIAN))
    system_posinf = _PyFloat_Unpack8(<unsigned char *>&PosInf, not is_big_endian(SYSTEM_ENDIAN))
    system_neginf = _PyFloat_Unpack8(<unsigned char *>&NegInf, not is_big_endian(SYSTEM_ENDIAN))
