# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
AMF Utilities.

@since: 0.1.0
"""

import struct, calendar, datetime, types, sys

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

try:
    import xml.etree.ElementTree as ET
except ImportError:
    try:
        import cElementTree as ET

        ET._ElementInterface = ET.ElementTree
    except ImportError:
        import elementtree.ElementTree as ET

class StringIOProxy(object):
    """
    I am a C{StringIO} type object containing byte data from the AMF stream.

    @see: U{ByteArray on OSFlash (external)
    <http://osflash.org/documentation/amf3#x0c_-_bytearray>}
    @see: U{Parsing ByteArrays on OSFlash (external)
    <http://osflash.org/documentation/amf3/parsing_byte_arrays>}
    """

    _wrapped_class = StringIO

    def __init__(self, buf=None):
        """
        @raise TypeError: Unable to coerce C{buf} to C{StringIO}.
        """
        self._buffer = StringIOProxy._wrapped_class()

        if isinstance(buf, (str, unicode)):
            self._buffer.write(buf)
        elif hasattr(buf, 'getvalue'):
            self._buffer.write(buf.getvalue())
        elif hasattr(buf, 'read') and hasattr(buf, 'seek') and hasattr(buf, 'tell'):
            old_pos = buf.tell()
            buf.seek(0)
            self._buffer.write(buf.read())
            buf.seek(old_pos)
        elif buf is None:
            pass
        else:
            raise TypeError, "Unable to coerce buf->StringIO"

        self._get_len()
        self._len_changed = False
        self._buffer.seek(0, 0)

    def close(self):
        self._buffer.close()
        self._len = 0
        self._len_changed = False

    def flush(self):
        self._buffer.flush()

    def getvalue(self):
        return self._buffer.getvalue()

    def next(self):
        return self._buffer.next()

    def read(self, n=-1):
        bytes = self._buffer.read(n)

        return bytes

    def readline(self):
        line = self._buffer.readline()

        return line

    def readlines(self, sizehint=0):
        """
        @type sizehint: C{int}
        @param sizehint: Default is 0.
        @note: This function does not consume the buffer.
        """
        lines = self._buffer.readlines(sizehint)

        return lines

    def seek(self, pos, mode=0):
        return self._buffer.seek(pos, mode)

    def tell(self):
        return self._buffer.tell()

    def truncate(self, size=0):
        self._buffer = StringIOProxy._wrapped_class()
        self._len_changed = True

    def write(self, s):
        self._buffer.write(s)
        self._len_changed = True

    def writelines(self, iterable):
        self._buffer.writelines(iterable)
        self._len_changed = True

    def _get_len(self):
        if hasattr(self._buffer, 'len'):
            self._len = self._buffer.len

            return

        old_pos = self._buffer.tell()
        self._buffer.seek(0, 2)

        self._len = self._buffer.tell()
        self._buffer.seek(old_pos)

    def __len__(self):
        if not self._len_changed:
            return self._len

        self._get_len()
        self._len_changed = False

        return self._len

class DataTypeMixIn(object):
    """
    Provides methods for reading and writing basic data types for file-like
    objects.
    """

    ENDIAN_NETWORK = "!"
    ENDIAN_NATIVE = "@"
    ENDIAN_LITTLE = "<"
    ENDIAN_BIG = ">"

    endian = ENDIAN_NETWORK

    def _read(self, length):
        """
        Reads C{length} bytes from the stream. If an attempt to read past the
        end of the buffer is made, L{EOFError} is raised.
        """
        bytes = self.read(length)

        if len(bytes) != length:
            self.seek(0 - len(bytes), 1)

            raise EOFError("Tried to read %d byte(s) from the stream" % length)

        return bytes

    def read_uchar(self):
        """
        Reads an C{unsigned char} from the stream.
        """
        return struct.unpack("B", self._read(1))[0]

    def write_uchar(self, c):
        """
        Writes an C{unsigned char} to the stream.
        """
        if not 0 <= c <= 255:
            raise ValueError("Not in range, %d" % c)

        self.write(struct.pack("B", c))

    def read_char(self):
        """
        Reads a C{char} from the stream.
        """
        return struct.unpack("b", self._read(1))[0]

    def write_char(self, c):
        """
        Write a C{char} to the stream.
        """
        if not -128 <= c <= 127:
            raise ValueError("Not in range, %d" % c)

        self.write(struct.pack("b", c))

    def read_ushort(self):
        """
        Reads a 2 byte unsigned integer from the stream.
        """
        return struct.unpack("%sH" % self.endian, self._read(2))[0]

    def write_ushort(self, s):
        """
        Writes a 2 byte unsigned integer to the stream.
        """
        if not 0 <= s <= 65535:
            raise ValueError("Not in range, %d" % s)

        self.write(struct.pack("%sH" % self.endian, s))

    def read_short(self):
        """
        Reads a 2 byte integer from the stream.
        """
        return struct.unpack("%sh" % self.endian, self._read(2))[0]

    def write_short(self, s):
        """
        Writes a 2 byte integer to the stream.
        """
        if not -32768 <= s <= 32767:
            raise ValueError("Not in range, %d" % s)

        self.write(struct.pack("%sh" % self.endian, s))

    def read_ulong(self):
        """
        Reads a 4 byte unsigned integer from the stream.
        """
        return struct.unpack("%sL" % self.endian, self._read(4))[0]

    def write_ulong(self, l):
        """
        Writes a 4 byte unsigned integer to the stream.
        """
        if not 0 <= l <= 4294967295:
            raise ValueError("Not in range, %d" % l)

        self.write(struct.pack("%sL" % self.endian, l))

    def read_long(self):
        """
        Reads a 4 byte integer from the stream.
        """
        return struct.unpack("%sl" % self.endian, self._read(4))[0]

    def write_long(self, l):
        """
        Writes a 4 byte integer to the stream.
        """
        if not -2147483648 <= l <= 2147483647:
            raise ValueError("Not in range, %d" % l)

        self.write(struct.pack("%sl" % self.endian, l))

    def read_double(self):
        """
        Reads an 8 byte float from the stream.
        """
        return struct.unpack("%sd" % self.endian, self._read(8))[0]

    def write_double(self, d):
        """
        Writes an 8 byte float to the stream.
        """
        self.write(struct.pack("%sd" % self.endian, d))

    def read_float(self):
        """
        Reads a 4 byte float from the stream.
        """
        return struct.unpack("%sf" % self.endian, self._read(4))[0]

    def write_float(self, f):
        """
        Writes a 4 byte float to the stream.
        """
        self.write(struct.pack("%sf" % self.endian, f))

    def read_utf8_string(self, length):
        """
        Reads a UTF-8 string from the stream.

        @rtype: C{unicode}
        """
        str = struct.unpack("%s%ds" % (self.endian, length), self.read(length))[0]

        return unicode(str, "utf8")

    def write_utf8_string(self, u):
        """
        Writes a unicode object to the stream in UTF-8
        """
        bytes = u.encode("utf8")

        self.write(struct.pack("%s%ds" % (self.endian, len(bytes)), bytes))

class BufferedByteStream(StringIOProxy, DataTypeMixIn):
    """
    An extension of C{StringIO}.

    Features:
     - Raises C{EOFError} if reading past end.
     - Allows you to C{peek()} at the next byte.
    """

    def __init__(self, buf=None):
        """
        @param buf: Initial byte stream.
        @type buf: C{str} or C{StringIO} instance
        """
        StringIOProxy.__init__(self, buf=buf)

        self.seek(0)

    def read(self, length=-1):
        """
        Read bytes from stream.

        If we are at the end of the buffer, a C{EOFError} is raised.
        If there is not enough buffer to be read and length is
        specified C{IOError} is raised.

        @param length: Number of bytes to read.
        @type length: C{int}
        @raise EOFError: Reading past end of stream.
        @raise IOError: Length specified but not enough buffer
        available.

        @rtype: array of C{char}
        @return: The bytes read from the stream.
        """
        if length > 0 and self.at_eof():
            raise EOFError
        if length > 0 and self.tell() + length > len(self):
            raise IOError

        return StringIOProxy.read(self, length)

    def peek(self, size=1):
        """
        Looks size bytes ahead in the stream, returning what it finds,
        returning the stream pointer to its initial position.

        @param size: Default is 1.
        @type size: C{int}
        @raise ValueError: Trying to peek backwards.

        @rtype:
        @return: Bytes.
        """
        if size == -1:
            return self.peek(len(self) - self.tell())

        if size < -1:
            raise ValueError("Cannot peek backwards")

        bytes = ''
        pos = self.tell()

        while not self.at_eof() and len(bytes) != size:
            bytes += self.read(1)

        self.seek(pos)

        return bytes

    def at_eof(self):
        """
        Returns true if C{next.read(1)} will trigger an C{EOFError}.

        @rtype: C{bool}
        @return:
        """
        return self.tell() >= len(self)

    def remaining(self):
        """
        Returns number of remaining bytes.

        @rtype: C{number}
        @return: Number of remaining bytes.
        """
        return len(self) - self.tell()

    def __add__(self, other):
        old_pos = self.tell()
        old_other_pos = other.tell()

        new = BufferedByteStream(self)

        other.seek(0)
        new.seek(0, 2)
        new.write(other.read())

        self.seek(old_pos)
        other.seek(old_other_pos)
        new.seek(0)

        return new

def hexdump(data):
    """
    Get hexadecimal representation of C{StringIO} data.

    @type data: 
    @param data:
    @rtype: C{str}
    @return: Hexadecimal string.
    """
    import string

    hex = ascii = buf = ""
    index = 0

    for c in data:
        hex += "%02x " % ord(c)
        if c in string.printable and c not in string.whitespace:
            ascii += c
        else:
            ascii += "."

        if len(ascii) == 16:
            buf += "%04x:  %s %s %s\n" % (index, hex[:24], hex[24:], ascii)
            hex = ascii = ""
            index += 16

    if len(ascii):
        buf += "%04x:  %-24s %-24s %s\n" % (index, hex[:24], hex[24:], ascii)

    return buf

def get_timestamp(d):
    """
    Returns a UTC timestamp for a C{datetime.datetime} object.

    @type d: C{datetime.datetime}
    @param d: The date object.
    @return: UTC timestamp.
    @rtype: C{str}

    @note: Inspiration taken from the U{Intertwingly blog
    <http://intertwingly.net/blog/2007/09/02/Dealing-With-Dates>}.
    """
    if isinstance(d, datetime.date) and not isinstance(d, datetime.datetime):
        d = datetime.datetime.combine(d, datetime.time(0, 0, 0, 0))

    return calendar.timegm(d.utctimetuple())

def get_datetime(secs):
    """
    Return a UTC date from a timestamp.

    @type secs: C{long}
    @param secs: Seconds since 1970.
    @return: UTC timestamp.
    @rtype: C{datetime.datetime}
    """
    return datetime.datetime.utcfromtimestamp(secs)

def make_classic_instance(klass):
    """
    Create an instance of a classic class (not inherited from ``object``)
    without calling __init__().

    @type klass: C{class}
    @param klass: The classic class to create an instance for.
    @rtype:
    @return: instance created
    """
    assert isinstance(klass, types.ClassType), "not an old style class"

    class _TemporaryClass:
        pass

    inst = _TemporaryClass()
    inst.__class__ = klass

    return inst

def get_mro(C):
    """
    Compute the class precedence list (mro).

    @raise TypeError: class type expected.
    """
    def merge(seqs):
        """
        @raise NameError: Inconsistent hierarchy.
        """
        res = []
        i = 0

        while 1:
            nonemptyseqs = [seq for seq in seqs if seq]
            if not nonemptyseqs:
                return res

            i += 1
            for seq in nonemptyseqs:
                cand = seq[0]
                nothead = [s for s in nonemptyseqs if cand in s[1:]]

                if nothead:
                    cand = None
                else:
                    break

            if not cand:
                raise NameError, "Inconsistent hierarchy"

            res.append(cand)

            for seq in nonemptyseqs:
                if seq[0] == cand:
                    del seq[0]

    if not isinstance(C, (types.ClassType, types.ObjectType)):
        raise TypeError, 'class type expected'

    if hasattr(C, '__mro__'):
        return C.__mro__

    return merge([[C]] + map(get_mro, C.__bases__) + [list(C.__bases__)])

def get_attrs(obj):
    """
    Gets a dict of the attrs of an object in a predefined resolution order
    """
    if hasattr(obj, '__getstate__'):
        return obj.__getstate__()
    elif hasattr(obj, 'iteritems'):
        attrs = {}

        for k, v in obj.iteritems():
            attrs[k] = v

        return attrs
    elif hasattr(obj, '__dict__'):
        return obj.__dict__

    return None

def get_instance_attrs(obj, alias):
    obj_attrs = None

    if alias is not None:
        attrs = alias.getAttrs(obj)

        if attrs is not None:
            obj_attrs = {}

            for at in attrs:
                obj_attrs[at] = getattr(obj, at)

    if obj_attrs is None:
        obj_attrs = get_attrs(obj)

    return obj_attrs

if sys.version_info < (2, 5) or sys.platform.startswith('win'):
    # workaround for python2.4's shortcomings with exceptional floats
    # see: http://blog.pyamf.org/archives/when-is-nan-not-a-number-with-python-24
    import fpconst

    if not fpconst.isNaN(struct.unpack("!d", '\xff\xf8\x00\x00\x00\x00\x00\x00')[0]):
        def read_double_workaround(self):
            bytes = self._read(8)

            if bytes == '\xff\xf8\x00\x00\x00\x00\x00\x00':
                return fpconst.NaN

            if bytes == '\xff\xf0\x00\x00\x00\x00\x00\x00':
                return fpconst.NegInf

            if bytes == '\x7f\xf0\x00\x00\x00\x00\x00\x00':
                return fpconst.PosInf

            return struct.unpack("%sd" % self.endian, bytes)[0]

        DataTypeMixIn.read_double = read_double_workaround

        def write_double_workaround(self, d):
            if fpconst.isNaN(d):
                self.write('\xff\xf8\x00\x00\x00\x00\x00\x00')
            elif fpconst.isNegInf(d):
                self.write('\xff\xf0\x00\x00\x00\x00\x00\x00')
            elif fpconst.isPosInf(d):
                self.write('\x7f\xf0\x00\x00\x00\x00\x00\x00')
            else:
                write_double_workaround.old_func(self, d)

        x = DataTypeMixIn.write_double
        DataTypeMixIn.write_double = write_double_workaround
        write_double_workaround.old_func = x
