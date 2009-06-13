# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE for details.

"""
C-extension for L{pyamf.util} Python module in L{PyAMF<pyamf>}.

@since: 0.4
"""

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
cdef int complete_init = 0

cdef unsigned char *NaN = <unsigned char *>'\xff\xf8\x00\x00\x00\x00\x00\x00'
cdef unsigned char *NegInf = <unsigned char *>'\xff\xf0\x00\x00\x00\x00\x00\x00'
cdef unsigned char *PosInf = <unsigned char *>'\x7f\xf0\x00\x00\x00\x00\x00\x00'

cdef double system_nan
cdef double system_posinf
cdef double system_neginf

cdef double platform_nan
cdef double platform_posinf
cdef double platform_neginf

cdef object pyamf_NaN
cdef object pyamf_NegInf
cdef object pyamf_PosInf


cdef int dump(void *p, int size):
    cdef int i
    cdef unsigned char *buf

    buf = <unsigned char *>p

    for i from 0 <= i < size:
        print buf[i]


cdef int build_platform_exceptional_floats() except? -1:
    global platform_nan, platform_posinf, platform_neginf
    global system_nan, system_posinf, system_neginf

    cdef unsigned char *buf = <unsigned char *>PyMem_Malloc(sizeof(unsigned char *) * sizeof(double))

    if buf == NULL:
        raise MemoryError

    memcpy(buf, NaN, 8)

    if not is_big_endian(SYSTEM_ENDIAN):
        swap_bytes(buf, 8)

    memcpy(&system_nan, buf, 8)

    memcpy(buf, NegInf, 8)

    if not is_big_endian(SYSTEM_ENDIAN):
        swap_bytes(buf, 8)

    memcpy(&system_neginf, buf, 8)

    memcpy(buf, PosInf, 8)

    if not is_big_endian(SYSTEM_ENDIAN):
        swap_bytes(buf, 8)

    memcpy(&system_posinf, buf, 8)

    if float_broken == 1:
        if _PyFloat_Unpack8(<unsigned char *>&NaN, not is_big_endian(SYSTEM_ENDIAN)) == -1:
            PyMem_Free(buf)

            return -1

        memcpy(&platform_nan, buf, 8)

        if _PyFloat_Unpack8(<unsigned char *>&PosInf, not is_big_endian(SYSTEM_ENDIAN)) == -1:
            PyMem_Free(buf)

            return -1

        memcpy(&platform_posinf, buf, 8)

        if _PyFloat_Unpack8(<unsigned char *>&NegInf, not is_big_endian(SYSTEM_ENDIAN)) == -1:
            PyMem_Free(buf)

            return -1

        memcpy(&platform_neginf, buf, 8)

    PyMem_Free(buf)


cdef int complete_import() except? -1:
    """
    This function is internal - do not call it yourself. It is used to
    finalise the cpyamf.util module to improve startup time.
    """
    global complete_init, float_broken
    global pyamf_NaN, pyamf_NegInf, pyamf_PosInf

    complete_init = 1

    SYSTEM_ENDIAN = get_native_endian()

    if is_broken_float():
        float_broken = 1

    build_platform_exceptional_floats()

    from pyamf import util

    pyamf_NaN = util.NaN
    pyamf_NegInf = util.NegInf
    pyamf_PosInf = util.PosInf

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
    cdef double test = _PyFloat_Unpack8(NaN, 0)

    cdef int result
    cdef unsigned char *buf = <unsigned char *>&test

    if is_big_endian(SYSTEM_ENDIAN):
        swap_bytes(buf, 8)

    result = memcmp(NaN, buf, 8)

    return result != 0


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
        """
        Returns the position of the stream pointer.
        """
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
        """
        Writes the content of the specified C{buf} into this buffer.
        """
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
        """
        Reads up to the specified number of bytes from the stream into
        the specified byte array of specified length.
        """
        if self.complain_if_closed() == -1:
            return -1

        if size == -1:
            size = self.remaining()

            if size == 0:
                size = 1

        if self.has_available(size) == -1:
            return -1

        buf[0] = <char *>PyMem_Malloc(sizeof(char *) * size)

        if buf[0] == NULL:
            raise MemoryError

            return -1

        memcpy(buf[0], self.buffer + self.pos, size)
        self.pos += size

        return 0

    cdef inline int at_eof(self) except? -1:
        """
        Returns C{True} if the internal pointer is at the end of the stream.

        @rtype: C{bool}
        """
        if self.complain_if_closed() == -1:
            return -1

        return self.length == self.pos

    cdef inline Py_ssize_t remaining(self) except? -1:
        """
        Returns number of remaining bytes.
        """
        if self.complain_if_closed() == -1:
            return -1

        return self.length - self.pos

    cdef int seek(self, Py_ssize_t pos, int mode=0) except? -1:
        """
        Sets the file-pointer offset, measured from the beginning of this stream,
        at which the next write operation will occur.

        @param pos:
        @type pos: C{int}
        @param mode: mode 0: absolute; 1: relative; 2: relative to EOF
        @type mode: C{int}
        """
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
        """
        Get raw data from buffer.
        """
        if self.complain_if_closed() == -1:
            return None

        return PyString_FromStringAndSize(self.buffer, self.length)

    cdef int peek(self, char **buf, Py_ssize_t size) except? -1:
        """
        Looks C{size} bytes ahead in the stream, returning what it finds,
        returning the stream pointer to its initial position.
        """
        if self.complain_if_closed() == -1:
            return -1

        cdef Py_ssize_t cur_pos = self.pos

        if self.read(buf, size) == -1:
            return -1

        self.pos = cur_pos

        return 0

    cdef int truncate(self, Py_ssize_t size) except? -1:
        """
        Truncates the stream to the specified length.

        @param size: The length of the stream, in bytes.
        @type size: C{int}
        """
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
        """
        Chops the tail off the stream starting at 0 and ending at C{tell()}.
        The stream pointer is set to 0 at the end of this function.
        """
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
        """
        Packs a long.

        @raise OverflowError: integer out of range
        """
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

        @raise OverflowError: integer out of range
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
        """
        Reads an C{unsigned char} from the stream.
        """
        return self.unpack_uint(1, <unsigned long *>ret)

    cdef int read_char(self, char *ret) except? -1:
        """
        Reads a C{char} from the stream.
        """
        return self.unpack_int(1, <long *>ret)

    cdef int read_ushort(self, unsigned short *ret) except? -1:
        """
        Reads a 2 byte unsigned integer from the stream.
        """
        return self.unpack_uint(2, <unsigned long *>ret)

    cdef int read_short(self, short *ret) except? -1:
        """
        Reads a 2 byte integer from the stream.
        """
        return self.unpack_int(2, <long *>ret)

    cdef int read_ulong(self, unsigned long *ret) except? -1:
        """
        Reads a 4 byte unsigned integer from the stream.
        """
        return self.unpack_uint(4, ret)

    cdef int read_long(self, long *ret) except? -1:
        """
        Reads a 4 byte integer from the stream.
        """
        return self.unpack_int(4, ret)

    cdef int read_24bit_uint(self, unsigned long *ret) except? -1:
        """
        Reads a 24 bit unsigned integer from the stream.
        """
        return self.unpack_uint(3, <unsigned long *>ret)

    cdef int read_24bit_int(self, long *ret) except? -1:
        """
        Reads a 24 bit integer from the stream.
        """
        return self.unpack_int(3, <long *>ret)

    cdef int write_uchar(self, unsigned char ret) except? -1:
        """
        Writes an C{unsigned char} to the stream.

        @param ret: Unsigned char
        @type ret: C{int}
        """
        return self.pack_uint(1, <unsigned long>ret)

    cdef int write_char(self, char ret) except? -1:
        """
        Write a C{char} to the stream.

        @param ret: char
        @type ret: C{int}
        """
        return self.pack_int(1, <long>ret)

    cdef int write_ushort(self, unsigned short ret) except? -1:
        """
        Writes a 2 byte unsigned integer to the stream.

        @param ret: 2 byte unsigned integer
        @type ret: C{int}
        """
        return self.pack_uint(2, <unsigned long>ret)

    cdef int write_short(self, short ret) except? -1:
        """
        Writes a 2 byte integer to the stream.

        @param ret: 2 byte integer
        @type ret: C{int}
        """
        return self.pack_int(2, <long>ret)

    cdef int write_ulong(self, unsigned long ret) except? -1:
        """
        Writes a 4 byte unsigned integer to the stream.

        @param ret: 4 byte unsigned integer
        @type ret: C{int}
        """
        return self.pack_uint(4, ret)

    cdef int write_long(self, long ret) except? -1:
        """
        Writes a 4 byte integer to the stream.

        @param ret: 4 byte integer
        @type ret: C{int}
        """
        return self.pack_int(4, ret)

    cdef int write_24bit_uint(self, unsigned long ret) except? -1:
        """
        Writes a 24 bit unsigned integer to the stream.

        @param ret: 24 bit unsigned integer
        @type ret: C{int}
        """
        return self.pack_uint(3, ret)

    cdef int write_24bit_int(self, long ret) except? -1:
        """
        Writes a 24 bit integer to the stream.

        @param ret: 24 bit integer
        @type ret: C{int}
        """
        return self.pack_int(3, ret)

    cdef object read_utf8_string(self, unsigned int l):
        """
        Reads a UTF-8 string from the stream.

        @rtype: C{unicode}
        """
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
        """
        Writes a unicode object to the stream in UTF-8.

        @param obj: unicode object
        @raise TypeError: Unexpected type for str C{u}.
        """
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
        """
        Reads an 8 byte float from the stream.
        """
        cdef unsigned char *buf = NULL
        cdef int done = 0

        if self.read(<char **>&buf, 8) == -1:
            if buf != NULL:
                PyMem_Free(buf)

            return -1

        if float_broken == 1:
            if is_big_endian(SYSTEM_ENDIAN):
                if not is_big_endian(self._endian):
                    swap_bytes(buf, 8)
            else:
                if is_big_endian(self._endian):
                    swap_bytes(buf, 8)

            if memcmp(buf, &system_nan, 8) == 0:
                memcpy(obj, &system_nan, 8)

                done = 1
            elif memcmp(buf, &system_posinf, 8) == 0:
                memcpy(obj, &system_posinf, 8)

                done = 1
            elif memcmp(buf, &system_neginf, 8) == 0:
                memcpy(obj, &system_neginf, 8)

                done = 1

            if done == 1:
                PyMem_Free(buf)

                return 0

            if is_big_endian(SYSTEM_ENDIAN):
                if not is_big_endian(self._endian):
                    swap_bytes(buf, 8)
            else:
                if is_big_endian(self._endian):
                    swap_bytes(buf, 8)

        obj[0] = _PyFloat_Unpack8(buf, not is_big_endian(self._endian))
        PyMem_Free(buf)

        return 0

    cdef int write_double(self, double val) except? -1:
        """
        Writes an 8 byte float to the stream.

        @param val: 8 byte float
        @type val: C{float}
        """
        cdef unsigned char *buf
        cdef unsigned char *foo
        cdef int done = 0

        buf = <unsigned char *>PyMem_Malloc(sizeof(unsigned char *) * 8)

        if buf == NULL:
            raise MemoryError

        if float_broken == 1:
            if memcmp(&val, &system_nan, 8) == 0:
                memcpy(buf, &val, 8)

                done = 1
            elif memcmp(&val, &system_posinf, 8) == 0:
                memcpy(buf, &val, 8)

                done = 1
            elif memcmp(&val, &system_neginf, 8) == 0:
                memcpy(buf, &val, 8)

                done = 1

            if done == 1:
                if is_big_endian(SYSTEM_ENDIAN):
                    if not is_big_endian(self._endian):
                        swap_bytes(buf, 8)
                else:
                    if is_big_endian(self._endian):
                        swap_bytes(buf, 8)

        if done == 0:
            if _PyFloat_Pack8(val, <unsigned char *>buf, not is_big_endian(self._endian)) == -1:
                PyMem_Free(buf)

                return -1

        if self.write(<char *>buf, 8) == -1:
            PyMem_Free(buf)

            return -1

        PyMem_Free(buf)

        return 0

    cdef int read_float(self, float *x):
        """
        Reads a 4 byte float from the stream.
        """
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
        """
        Writes a 4 byte float to the stream.

        @param c: 4 byte float
        @type c: C{float}
        """
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

    cdef int append(self, object obj) except? -1:
        cdef int i = self.pos

        self.pos = self.length

        if hasattr(obj, 'getvalue'):
            self.write_utf8_string(obj.getvalue())
        else:
            self.write_utf8_string(obj)

        self.pos = i


cdef class BufferedByteStream(cBufferedByteStream):
    """
    An extension of C{StringIO}.

    @see: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
    """

    def __init__(self, buf=None):
        """
        @raise TypeError: Unable to coerce buf -> StringIO
        """
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
        """
        Reads C{size} bytes from the stream.
        """
        cdef Py_ssize_t s
        cdef object cls

        if size != -1:
            s = <Py_ssize_t>size
        else:
            s = cBufferedByteStream.remaining(self)

            if s == 0:
                s = 1

        cdef char *buf = NULL

        cBufferedByteStream.read(self, &buf, s)

        r = PyString_FromStringAndSize(buf, s)
        PyMem_Free(buf)

        return r

    def write(self, x):
        """
        Writes the content of the specified C{x} into this buffer.

        @param x:
        @type x:
        """
        cBufferedByteStream.write_utf8_string(self, x)

    def close(self):
        """
        Close the stream.
        """
        cBufferedByteStream.close(self)

    def flush(self):
        # no-op
        pass

    def tell(self):
        """
        Returns the position of the stream pointer.
        """
        return self.pos

    def remaining(self):
        """
        Returns number of remaining bytes.

        @rtype: C{number}
        @return: Number of remaining bytes.
        """
        return cBufferedByteStream.remaining(self)

    def __len__(self):
        return self.length

    def getvalue(self):
        """
        Get raw data from buffer.
        """
        return cBufferedByteStream.getvalue(self)

    def at_eof(self):
        """
        Returns C{True} if the internal pointer is at the end of the stream.

        @rtype: C{bool}
        """
        cdef int result = cBufferedByteStream.at_eof(self)

        return (result == 1)

    def seek(self, pos, mode=0):
        """
        Sets the file-pointer offset, measured from the beginning of this stream,
        at which the next write operation will occur.

        @param pos:
        @type pos: C{int}
        @param mode:
        @type mode: C{int}
        """
        cBufferedByteStream.seek(self, pos, mode)

    def peek(self, size=1):
        """
        Looks C{size} bytes ahead in the stream, returning what it finds,
        returning the stream pointer to its initial position.

        @param size: Default is 1.
        @type size: C{int}

        @rtype:
        @return: Bytes.
        """
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
        """
        Truncates the stream to the specified length.

        @param size: The length of the stream, in bytes.
        @type size: C{int}
        """
        cBufferedByteStream.truncate(self, size)

    def consume(self):
        """
        Chops the tail off the stream starting at 0 and ending at C{tell()}.
        The stream pointer is set to 0 at the end of this function.
        """
        cBufferedByteStream.consume(self)

    def read_uchar(self):
        """
        Reads an C{unsigned char} from the stream.
        """
        cdef unsigned char *i = NULL
        cdef object ret

        i = <unsigned char *>PyMem_Malloc(1 * sizeof(unsigned char))

        if i == NULL:
            raise MemoryError

        cBufferedByteStream.read_uchar(self, i)

        ret = <unsigned char>(i[0])
        PyMem_Free(i)

        return ret

    def read_char(self):
        """
        Reads a C{char} from the stream.
        """
        cdef char *i = NULL
        cdef object ret

        i = <char *>PyMem_Malloc(1 * sizeof(char))

        if i == NULL:
            raise MemoryError

        cBufferedByteStream.read_char(self, i)

        ret = <char>(i[0])
        PyMem_Free(i)

        return ret

    def read_ushort(self):
        """
        Reads a 2 byte unsigned integer from the stream.
        """
        cdef unsigned short *i = NULL
        cdef object ret

        i = <unsigned short *>PyMem_Malloc(1 * sizeof(unsigned short))

        if i == NULL:
            raise MemoryError

        cBufferedByteStream.read_ushort(self, i)

        ret = <unsigned short>(i[0])
        PyMem_Free(i)

        return ret

    def read_short(self):
        """
        Reads a 2 byte integer from the stream.
        """
        cdef short *i = NULL
        cdef object ret

        i = <short *>PyMem_Malloc(1 * sizeof(short))

        if i == NULL:
            raise MemoryError

        cBufferedByteStream.read_short(self, i)

        ret = <short>(i[0])
        PyMem_Free(i)

        return ret

    def read_ulong(self):
        """
        Reads a 4 byte unsigned integer from the stream.
        """
        cdef unsigned long *i = NULL
        cdef object ret

        i = <unsigned long *>PyMem_Malloc(1 * sizeof(unsigned long))

        if i == NULL:
            raise MemoryError

        cBufferedByteStream.read_ulong(self, i)

        ret = <unsigned long>(i[0])
        PyMem_Free(i)

        return ret

    def read_long(self):
        """
        Reads a 4 byte integer from the stream.
        """
        cdef long *i = NULL
        cdef object ret

        i = <long *>PyMem_Malloc(1 * sizeof(long))

        if i == NULL:
            raise MemoryError

        cBufferedByteStream.read_long(self, i)

        ret = <long>(i[0])
        PyMem_Free(i)

        return ret

    def read_24bit_uint(self):
        """
        Reads a 24 bit unsigned integer from the stream.
        """
        cdef unsigned long *i = NULL
        cdef object ret

        i = <unsigned long *>PyMem_Malloc(1 * sizeof(unsigned long))

        if i == NULL:
            raise MemoryError

        cBufferedByteStream.read_24bit_uint(self, i)

        ret = <long>(i[0])
        PyMem_Free(i)

        return ret

    def read_24bit_int(self):
        """
        Reads a 24 bit integer from the stream.
        """
        cdef long *i = NULL
        cdef object ret

        i = <long *>PyMem_Malloc(1 * sizeof(long))

        if i == NULL:
            raise MemoryError

        cBufferedByteStream.read_24bit_int(self, i)

        ret = <long>(i[0])
        PyMem_Free(i)

        return ret

    def write_uchar(self, x):
        """
        Writes an C{unsigned char} to the stream.

        @param x: Unsigned char
        @type x: C{int}
        @raise TypeError: Unexpected type for int C{x}.
        """
        if PyInt_Check(x) == 0 and PyLong_Check(x) == 0:
            raise TypeError('expected int for x')

        cBufferedByteStream.write_uchar(self, <unsigned char>x)

    def write_char(self, x):
        """
        Write a C{char} to the stream.

        @param x: char
        @type x: C{int}
        @raise TypeError: Unexpected type for int C{x}.
        """
        if PyInt_Check(x) == 0 and PyLong_Check(x) == 0:
            raise TypeError('expected int for x')

        cBufferedByteStream.write_char(self, <char>x)

    def write_ushort(self, x):
        """
        Writes a 2 byte unsigned integer to the stream.

        @param x: 2 byte unsigned integer
        @type x: C{int}
        @raise TypeError: Unexpected type for int C{x}.
        """
        if PyInt_Check(x) == 0 and PyLong_Check(x) == 0:
            raise TypeError('expected int for x')

        cBufferedByteStream.write_ushort(self, <unsigned short>x)

    def write_short(self, x):
        """
        Writes a 2 byte integer to the stream.

        @param x: 2 byte integer
        @type x: C{int}
        @raise TypeError: Unexpected type for int C{x}.
        """
        if PyInt_Check(x) == 0 and PyLong_Check(x) == 0:
            raise TypeError('expected int for x')

        cBufferedByteStream.write_short(self, <short>x)

    def write_ulong(self, x):
        """
        Writes a 4 byte unsigned integer to the stream.

        @param x: 4 byte unsigned integer
        @type x: C{int}
        @raise TypeError: Unexpected type for int C{x}.
        """
        if PyInt_Check(x) == 0 and PyLong_Check(x) == 0:
            raise TypeError('expected int for x')

        if x > 4294967295L or x < 0:
            raise OverflowError

        cBufferedByteStream.write_ulong(self, <unsigned long>x)

    def write_long(self, long x):
        """
        Writes a 4 byte integer to the stream.

        @param x: 4 byte integer
        @type x: C{int}
        """
        cBufferedByteStream.write_long(self, x)

    def write_24bit_uint(self, unsigned long x):
        """
        Writes a 24 bit unsigned integer to the stream.

        @param x: 24 bit unsigned integer
        @type x: C{int}
        """
        cBufferedByteStream.write_24bit_uint(self, x)

    def write_24bit_int(self, long x):
        """
        Writes a 24 bit integer to the stream.

        @param x: 24 bit integer
        @type x: C{int}
        """
        cBufferedByteStream.write_24bit_int(self, x)

    def read_utf8_string(self, unsigned int size):
        """
        Reads a UTF-8 string from the stream.

        @rtype: C{unicode}
        """
        return cBufferedByteStream.read_utf8_string(self, size)

    def write_utf8_string(self, obj):
        """
        Writes a unicode object to the stream in UTF-8.

        @param obj: unicode object
        """
        cBufferedByteStream.write_utf8_string(self, obj)

    def read_double(self):
        """
        Reads an 8 byte float from the stream.
        """
        cdef double x

        if cBufferedByteStream.read_double(self, &x) == -1:
            return

        if float_broken == 1:
            if memcmp(&x, &system_nan, 8) == 0:
                return pyamf_NaN
            elif memcmp(&x, &system_neginf, 8) == 0:
                return pyamf_NegInf
            elif memcmp(&x, &system_posinf, 8) == 0:
                return pyamf_PosInf

        return PyFloat_FromDouble(x)

    def write_double(self, val):
        """
        Writes an 8 byte float to the stream.

        @param val: 8 byte float
        @type val: C{float}
        @raise TypeError: Unexpected type for float C{val}.
        """
        if PyFloat_Check(val) == 0:
            raise TypeError('Expecting float for val')

        cdef double d = PyFloat_AsDouble(val)

        if float_broken == 1:
            if memcmp(&d, &platform_nan, 8) == 0:
                done = 1
            elif memcmp(&d, &platform_neginf, 8) == 0:
                done = 1
            elif memcmp(&d, &platform_posinf, 8) == 0:
                done = 1

            if done == 1:
                if is_big_endian(SYSTEM_ENDIAN):
                    if not is_big_endian(self._endian):
                        swap_bytes(<unsigned char *>&d, 8)
                else:
                    if is_big_endian(self._endian):
                        swap_bytes(<unsigned char *>&d, 8)

                cBufferedByteStream.write(self, <char *>&d, 8)

                return

        cBufferedByteStream.write_double(self, d)

    def read_float(self):
        """
        Reads a 4 byte float from the stream.
        """
        cdef float x

        if cBufferedByteStream.read_float(self, &x) == -1:
            return

        return PyFloat_FromDouble(x)

    def write_float(self, x):
        """
        Writes a 4 byte float to the stream.

        @param x: 4 byte float
        @type x: C{float}
        """
        if PyFloat_Check(x) == 0:
            raise TypeError('Expecting float for val')

        cBufferedByteStream.write_float(self, <float>x)

    def append(self, data):
        """
        Append data to the end of the stream. The pointer will not move if
        this operation is successful.

        @param data: The data to append to the stream.
        @type data: C{str} or C{unicode}
        @raise TypeError: data is not C{str} or C{unicode}
        """
        cBufferedByteStream.append(self, data)

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
