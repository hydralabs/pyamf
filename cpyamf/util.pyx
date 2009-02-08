# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE for details.

"""
Python C-extensions for L{PyAMF<pyamf>}.

@since: 0.4
"""

cdef extern from *:
    ctypedef unsigned long size_t
    int memcmp(void *, void *, size_t)
    void *memcpy(void *, void *, size_t)

cdef extern from "Python.h":
    void *PyMem_Malloc(Py_ssize_t n)
    void PyMem_Free(void *p)

    unsigned char PyString_Check(object)
    object PyString_FromStringAndSize(char *buffer, Py_ssize_t)
    int PyString_AsStringAndSize(object, char **, Py_ssize_t *)
    char *PyString_AsString(object)

    int PyUnicode_Check(object)
    object PyUnicode_AsUTF8String(object)
    object PyString_AsEncodedObject(object, char *, char *)
    object PyUnicode_DecodeUTF8(char *, Py_ssize_t, char *)

    long PyNumber_Long(object)
    object PyInt_FromLong(long)
    long PyInt_AsLong(object)

    int _PyFloat_Pack4(double, unsigned char *, int)
    void _PyFloat_Pack8(double, unsigned char *, int)
    double _PyFloat_Unpack4(unsigned char *, int)
    double _PyFloat_Unpack8(unsigned char *, int)
    object PyFloat_FromDouble(double)
    double PyFloat_AsDouble(object)

cdef extern from "stdio.h":
    int SIZEOF_LONG

cdef extern from "cStringIO.h":
    void PycString_IMPORT()

    object StringIO_NewOutput "PycStringIO->NewOutput" (int)
    object StringIO_NewInput "PycStringIO->NewInput" (object)
    int StringIO_cread "PycStringIO->cread" (object, char **, Py_ssize_t)
    int StringIO_creadline "PycStringIO->creadline" (object, char **)
    int StringIO_cwrite "PycStringIO->cwrite" (object, char *, Py_ssize_t)
    object StringIO_cgetvalue "PycStringIO->cgetvalue" (obj)

import fpconst

# module constant declarations
DEF ENDIAN_NETWORK = "!"
DEF ENDIAN_NATIVE = "@"
DEF ENDIAN_LITTLE = "<"
DEF ENDIAN_BIG = ">"

# forward declarations for module
cdef char SYSTEM_ENDIAN
cdef int float_broken = -1
cdef unsigned char *NaN = <unsigned char *>'\xff\xf8\x00\x00\x00\x00\x00\x00'
cdef unsigned char *NegInf = <unsigned char *>'\xff\xf0\x00\x00\x00\x00\x00\x00'
cdef unsigned char *PosInf = <unsigned char *>'\x7f\xf0\x00\x00\x00\x00\x00\x00'

cdef inline char _get_native_endian():
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

    return endian == SYSTEM_ENDIAN

cdef inline void swap_bytes(unsigned char *buffer, Py_ssize_t size):
    cdef unsigned char *buf = <unsigned char *>PyMem_Malloc(size)
    cdef Py_ssize_t i

    for i from 0 <= i < size:
        buf[i] = buffer[size - i - 1]

    memcpy(buffer, buf, size)

    PyMem_Free(buf)

cdef int is_broken_float():
    cdef double test = _PyFloat_Unpack8(NaN, 0)

    cdef int result
    cdef unsigned char *buf = <unsigned char *>&test

    if is_big_endian(SYSTEM_ENDIAN):
        result = memcmp(NaN, &test, 8) != 0
    else:
        swap_bytes(buf, 8)
        result = memcmp(NaN, buf, 8)

    return result != 0

cdef class BufferedByteStream:
    cdef char _endian
    cdef object buffer
    cdef unsigned long length
    cdef unsigned char len_changed

    def __new__(self):
        self._endian = ENDIAN_NETWORK
        self.length = 0
        self.len_changed = 0

    def __init__(self, buf=None):
        if not self.buffer:
            self.buffer = StringIO_NewOutput(128)

        if buf is None:
            return

        cdef char *s = NULL
        cdef long t = 0
        cdef long l = 0
        cdef BufferedByteStream other = <BufferedByteStream>buf

        if isinstance(buf, BufferedByteStream):
            t = <long>other.tell()
            other.seek(0)
            l = StringIO_cread(other.buffer, &s, -1)
            StringIO_cwrite(self.buffer, s, l)
            self.length = l
            other.seek(t)
        elif isinstance(buf, basestring):
            self.write(buf)
        elif hasattr(buf, 'getvalue'):
            self.write(buf.getvalue())
        elif hasattr(buf, 'read') and hasattr(buf, 'seek') and hasattr(buf, 'tell'):
            old_pos = buf.tell()
            buf.seek(0)
            self.write(buf.read())
            buf.seek(old_pos)
        else:
            raise TypeError("Unable to coerce buf->StringIO")

        self.buffer.seek(0)

    property endian:
        def __set__(self, value):
            if PyString_Check(value) == 0:
                raise TypeError('String value expected')

            if value not in [ENDIAN_NETWORK, ENDIAN_NATIVE, ENDIAN_LITTLE, ENDIAN_BIG]:
                raise ValueError('Not a valid endian type')

            self._endian = PyString_AsString(value)[0]

        def __get__(self):
            return PyString_FromStringAndSize(&self._endian, 1)

    cdef long c_length(self):
        if self.len_changed == 0:
            return self.length

        cdef long cur_pos = <long>self.buffer.tell()

        self.buffer.seek(0, 2)

        self.length = <long>self.buffer.tell()
        self.len_changed = 0

        self.buffer.seek(cur_pos, 0)

        return self.length

    cdef long unpack_int(self, char *buf, long num_bytes):
        """
        Unpacks a long from C{buf}.
        """
        cdef long x = 0
        cdef long bytes_left = num_bytes
        cdef unsigned char *bytes = <unsigned char *>buf

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

        return x

    cdef unsigned long unpack_uint(self, char *buf, long num_bytes):
        """
        Unpacks an unsigned long from C{buf}.
        """
        cdef unsigned long x = 0
        cdef unsigned char *bytes = <unsigned char *>buf

        if is_big_endian(self._endian):
            while num_bytes > 0:
                x = (x << 8) | bytes[0]
                bytes += 1
                num_bytes -= 1
        else:
            while num_bytes > 0:
                x = (x << 8) | bytes[num_bytes - 1]
                num_bytes -= 1

        return x

    cdef void pack_int(self, long x, long num_bytes):
        cdef long maxint = 1
        cdef long minint = -1

        if num_bytes != SIZEOF_LONG:
            maxint <<= <long>(num_bytes * 8)
            minint = (-maxint)

            if x >= maxint or x < minint:
                raise OverflowError('integer out of range')

        cdef char *buf = <char *>PyMem_Malloc(num_bytes)
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

        StringIO_cwrite(self.buffer, buf, num_bytes)
        PyMem_Free(buf)

    cdef void pack_uint(self, unsigned long x, long num_bytes):
        """
        Packs an unsigned long into a buffer.
        """
        cdef unsigned long maxint = 1

        if num_bytes != SIZEOF_LONG:
            maxint <<= <unsigned long>(num_bytes * 8)

            if x >= maxint:
                raise OverflowError('integer out of range')

        cdef char *buf = <char *>PyMem_Malloc(num_bytes)
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

        StringIO_cwrite(self.buffer, buf, num_bytes)

        PyMem_Free(buf)

    def tell(self):
        if not self.buffer:
            raise ValueError('buffer is closed')

        return self.buffer.tell()

    def seek(self, int pos, int mode=0):
        if not self.buffer:
            raise ValueError('buffer is closed')

        return self.buffer.seek(pos, mode)

    cdef int c_at_eof(self):
        if not self.buffer:
            raise ValueError('buffer is closed')

        return <long>self.remaining() == 0

    def at_eof(self):
        if not self.buffer:
            raise ValueError('buffer is closed')

        cdef long remaining = self.c_remaining()

        if remaining == 0:
            return True

        return False

    cdef long c_remaining(self):
        if not self.buffer:
            raise ValueError('buffer is closed')

        if self.len_changed == 1:
            self.c_length()

        return self.length - <long>self.tell()

    def remaining(self):
        if not self.buffer:
            raise ValueError('buffer is closed')

        cdef long cur_pos = PyInt_AsLong(self.tell())

        if self.len_changed == 1:
            self.c_length()

        return PyInt_FromLong(self.length - cur_pos)

    def getvalue(self):
        if not self.buffer:
            raise ValueError('buffer is closed')

        return self.buffer.getvalue()

    def read(self, int n=-1):
        if not self.buffer:
            raise ValueError('buffer is closed')

        cdef char *buf = NULL
        cdef int chars_read = StringIO_cread(self.buffer, &buf, n)

        if n > chars_read:
            if chars_read > 0:
                raise IOError

            raise EOFError

        return PyString_FromStringAndSize(buf, chars_read);

    def read_uchar(self):
        if not self.buffer:
            raise ValueError('buffer is closed')

        cdef char *buf = NULL

        if StringIO_cread(self.buffer, &buf, 1) != 1:
            raise EOFError

        result = <unsigned char>buf[0]

        return PyInt_FromLong(<long>result)

    def read_char(self):
        if not self.buffer:
            raise ValueError('buffer is closed')

        cdef char *buf = NULL

        if StringIO_cread(self.buffer, &buf, 1) != 1:
            raise EOFError

        return PyInt_FromLong(<long>buf[0])

    def read_ushort(self):
        if not self.buffer:
            raise ValueError('buffer is closed')

        cdef char *buf = NULL
        cdef unsigned short result = 0

        if StringIO_cread(self.buffer, &buf, 2) != 2:
            raise EOFError

        result = <unsigned short>self.unpack_uint(buf, 2)

        return PyInt_FromLong(<long>result)

    def read_short(self):
        if not self.buffer:
            raise ValueError('buffer is closed')

        cdef char *buf = NULL
        cdef short result = 0

        if StringIO_cread(self.buffer, &buf, 2) != 2:
            raise EOFError

        result = <short>self.unpack_uint(buf, 2)

        return PyInt_FromLong(<long>result)

    def read_ulong(self):
        if not self.buffer:
            raise ValueError('buffer is closed')

        cdef char *buf = NULL

        if StringIO_cread(self.buffer, &buf, 4) != 4:
            raise EOFError

        return self.unpack_uint(buf, 4)

    def read_long(self):
        if not self.buffer:
            raise ValueError('buffer is closed')

        cdef char *buf = NULL
        cdef short result = 0

        if StringIO_cread(self.buffer, &buf, 4) != 4:
            raise EOFError

        return PyInt_FromLong(self.unpack_int(buf, 4))

    def read_24bit_uint(self):
        """
        Reads a 24 bit unsigned integer from the stream.

        @since: 0.4
        """
        if not self.buffer:
            raise ValueError('buffer is closed')

        cdef char *buf = NULL

        if StringIO_cread(self.buffer, &buf, 3) != 3:
            raise EOFError

        return PyInt_FromLong(self.unpack_uint(buf, 3))

    def read_24bit_int(self):
        """
        Reads a 24 bit integer from the stream.

        @since: 0.4
        """
        if not self.buffer:
            raise ValueError('buffer is closed')

        cdef char *buf = NULL

        if StringIO_cread(self.buffer, &buf, 3) != 3:
            raise EOFError

        return PyInt_FromLong(self.unpack_int(buf, 3))

    def write(self, object obj):
        if not self.buffer:
            raise ValueError('buffer is closed')

        cdef char *buffer
        cdef Py_ssize_t length

        if PyString_AsStringAndSize(obj, &buffer, &length):
            return

        StringIO_cwrite(self.buffer, buffer, length)
        self.len_changed = 1

    def write_uchar(self, long val):
        if not self.buffer:
            raise ValueError('buffer is closed')

        if val < 0 or val > 255:
            raise OverflowError('uchar not in range')

        StringIO_cwrite(self.buffer, <char *>&val, 1);
        self.len_changed = 1

    def write_char(self, long val):
        if not self.buffer:
            raise ValueError('buffer is closed')

        if val < -128 or val > 127:
            raise OverflowError('char not in range')

        StringIO_cwrite(self.buffer, <char *>&val, 1);
        self.len_changed = 1

    def write_ushort(self, long val):
        if not self.buffer:
            raise ValueError('buffer is closed')

        if val < 0 or val > 65535:
            raise OverflowError('ushort not in range')

        self.pack_uint(val, 2)
        self.len_changed = 1

    def write_short(self, long val):
        if not self.buffer:
            raise ValueError('buffer is closed')

        if val < -32768 or val > 32767:
            raise OverflowError('short not in range')

        self.pack_int(val, 2)
        self.len_changed = 1

    def write_ulong(self, val):
        if not self.buffer:
            raise ValueError('buffer is closed')

        if val < 0 or val > 4294967295L:
            raise OverflowError

        self.pack_uint(<unsigned long>val, 4)
        self.len_changed = 1

    def write_long(self, val):
        if not self.buffer:
            raise ValueError('buffer is closed')

        if not -2147483648 <= val <= 2147483647:
            raise OverflowError

        self.pack_int(<long>val, 4)
        self.len_changed = 1

    def write_24bit_uint(self, unsigned long n):
        """
        Writes a 24 bit unsigned integer to the stream.
        """
        if not self.buffer:
            raise ValueError('buffer is closed')

        if not 0 <= n <= 0xffffff:
            raise OverflowError("n is out of range")

        self.pack_uint(n, 3)
        self.len_changed = 1

    def write_24bit_int(self, long n):
        """
        Writes a 24 bit integer to the stream.
        """
        if not self.buffer:
            raise ValueError('buffer is closed')

        if not -8388608 <= n <= 8388607:
            raise OverflowError("n is out of range")

        self.pack_int(n, 3)
        self.len_changed = 1

    def read_utf8_string(self, unsigned int l):
        if not self.buffer:
            raise ValueError('buffer is closed')

        cdef char* buf = NULL
        cdef long n

        n = StringIO_cread(self.buffer, &buf, l)

        if n != l:
            raise EOFError

        return PyUnicode_DecodeUTF8(buf, n, '')

    def write_utf8_string(self, object s):
        if not self.buffer:
            raise ValueError('buffer is closed')

        cdef object encoded_string
        cdef char *buf = NULL
        cdef Py_ssize_t l = -1

        if PyUnicode_Check(s):
            encoded_string = PyUnicode_AsUTF8String(s)
        elif PyString_Check(s):
            encoded_string = PyString_AsEncodedObject(s, "utf8", "strict")
        else:
            raise TypeError('value must be Unicode or str')

        if not encoded_string:
            return

        if (PyString_AsStringAndSize(encoded_string, &buf, &l) == -1):
            return

        StringIO_cwrite(self.buffer, buf, l)
        self.len_changed = 1

    def read_double(self):
        if not self.buffer:
            raise ValueError('buffer is closed')

        cdef double x
        cdef char *buf = NULL
        cdef unsigned char le = 1

        if StringIO_cread(self.buffer, &buf, 8) != 8:
            raise EOFError

        if float_broken:
            le = 0
            if not is_big_endian(self._endian):
                swap_bytes(<unsigned char *>buf, 8)

            if memcmp(NaN, buf, 8) == 0:
                return fpconst.NaN
            elif memcmp(NegInf, buf, 8) == 0:
                return fpconst.NegInf
            elif memcmp(PosInf, buf, 8) == 0:
                return fpconst.PosInf
        elif is_big_endian(self._endian):
            le = 0

        x = _PyFloat_Unpack8(<unsigned char *>buf, le)

        return PyFloat_FromDouble(x)

    def write_double(self, val):
        if not self.buffer:
            raise ValueError('buffer is closed')

        cdef char *buf = <char *>PyMem_Malloc(8)
        cdef int le = 0
        cdef int done = 0

        if float_broken:
            if fpconst.isNaN(val):
                memcpy(buf, NaN, 8)
                done = 1
            elif fpconst.isNegInf(val):
                memcpy(buf, NegInf, 8)
                done = 1
            elif fpconst.isPosInf(val):
                memcpy(buf, PosInf, 8)
                done = 1

            if done == 1 and not is_big_endian(self._endian):
                swap_bytes(<unsigned char *>buf, 8)

        if done == 0:
            if not is_big_endian(self._endian):
                le = 1

            _PyFloat_Pack8(val, <unsigned char *>buf, le)

        StringIO_cwrite(self.buffer, buf, 8)
        PyMem_Free(buf)
        self.len_changed = 1

    def read_float(self):
        if not self.buffer:
            raise ValueError('buffer is closed')

        cdef float x
        cdef char *buf
        cdef unsigned char le = 0

        if StringIO_cread(self.buffer, &buf, 4) != 4:
            raise EOFError

        if not is_big_endian(self._endian):
            le = 1

        x = _PyFloat_Unpack4(<unsigned char *>buf, le)

        return PyFloat_FromDouble(x)

    def write_float(self, double c):
        if not self.buffer:
            raise ValueError('buffer is closed')

        cdef char buf[8]
        cdef unsigned char le = 0

        if not is_big_endian(self._endian):
            le = 1

        _PyFloat_Pack4(c, <unsigned char *>buf, le)
        StringIO_cwrite(self.buffer, buf, 4)
        self.len_changed = 1

    def __len__(self):
        if not self.buffer:
            return 0

        return self.c_length()

    def peek(self, long size=1):
        if size == -1:
            return self.peek(<long>self.remaining())

        if size < -1:
            raise ValueError("Cannot peek backwards")

        cdef char *buffer = NULL
        cdef long pos = <long>self.tell()
        cdef long remaining = self.c_remaining()

        if remaining >= size:
            if StringIO_cread(self.buffer, &buffer, size) != size:
                raise RuntimeError
        else:
            if StringIO_cread(self.buffer, &buffer, remaining) != remaining:
                raise RuntimeError

            size = remaining

        self.seek(pos)

        return PyString_FromStringAndSize(buffer, size)

    def truncate(self, long size=0):
        if not self.buffer:
            raise ValueError('buffer is closed')

        if size == 0:
            self.buffer = None
            self.__init__(self)
            self.len_changed = 1

            return

        if size > self.c_length():
            return

        cdef char *buffer = NULL
        cdef unsigned long cur_pos = <unsigned long>self.tell()

        self.seek(0)

        if StringIO_cread(self.buffer, &buffer, size) != size:
            raise RuntimeError

        buf = StringIO_NewOutput(128)
        StringIO_cwrite(buf, buffer, size)

        buf.seek(cur_pos)

        self.buffer = buf
        self.len_changed = 1

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

    def close(self):
        if not self.buffer:
            raise ValueError('buffer is closed')

        self.buffer.close()
        self.buffer = None
        self.length = 0

    def flush(self):
        if not self.buffer:
            raise ValueError('buffer is closed')

        self.buffer.flush()
        self.len_changed = 1

    def readline(self):
        if not self.buffer:
            raise ValueError('buffer is closed')

        return self.buffer.readline()

    def readlines(self, sizehint=0):
        if not self.buffer:
            raise ValueError('buffer is closed')

        return self.buffer.readlines(sizehint)

    def writelines(self, iterable):
        if not self.buffer:
            raise ValueError('buffer is closed')

        self.buffer.writelines(iterable)
        self.len_changed = 1

    def consume(self):
        """
        Chops the tail off the stream starting at 0 and ending at C{tell()}.
        The stream pointer is set to 0 at the end of this function.

        @since: 0.4
        """
        if not self.buffer:
            raise ValueError('buffer is closed')

        # read the entire buffer
        cdef char *buf = NULL
        cdef unsigned int chars_read = StringIO_cread(self.buffer, &buf, -1)

        # quick truncate
        new_buffer = StringIO_NewOutput(128)

        StringIO_cwrite(new_buffer, buf, chars_read)
        self.buffer = new_buffer
        self.buffer.seek(0)

        self.len_changed = 1

# init module here:
PycString_IMPORT

SYSTEM_ENDIAN = _get_native_endian()
float_broken = is_broken_float()
