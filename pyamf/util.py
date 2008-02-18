# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
AMF Utilities.

@author: U{Arnar Birgisson<mailto:arnarbi@gmail.com>}
@author: U{Thijs Triemstra<mailto:info@collab.nl>}
@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import struct, calendar, datetime, types

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

        self._len = self._buffer.tell()
        self._buffer.seek(0, 0)

    def close(self):
        self._buffer.close()
        self._len = 0

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
        @param sizehint:
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

        self._get_len()

    def write(self, s):
        self._buffer.write(s)

        self._get_len()

    def writelines(self, iterable):
        self._buffer.writelines(iterable)
        self._get_len()

    def _get_len(self):
        if hasattr(self._buffer, 'len'):
            self._len = self._buffer.len

            return

        old_pos = self._buffer.tell()
        self._buffer.seek(0, 2)

        self._len = self._buffer.tell()
        self._buffer.seek(old_pos)

    def __len__(self):
        return self._len

class NetworkIOMixIn(object):
    """
    Provides mix-in methods for file-like objects to read and write basic
    datatypes in big-endian byte-order.
    """

    def _read(self, length):
        """
        @type length:
        @param length:
        @raise EOFError: Not in range.
        @rtype:
        @return: Bytes.
        """
        bytes = self.read(length)

        if len(bytes) != length:
            self.seek(0 - len(bytes), 1)

            raise EOFError("Tried to read %d byte(s) from the stream" % length)

        return bytes

    def read_uchar(self):
        return struct.unpack("!B", self._read(1))[0]

    def write_uchar(self, c):
        """
        @raise ValueError: Not in range.
        """
        if not 0 <= c <= 256:
            raise ValueError("c not in range (%d)" % c)

        self.write(struct.pack("!B", c))

    def read_char(self):
        return struct.unpack("!b", self._read(1))[0]

    def write_char(self, c):
        """
        @raise ValueError: Not in range.
        """
        if not -128 <= c <= 127:
            raise ValueError("c not in range (%d)" % c)

        self.write(struct.pack("!b", c))

    def read_ushort(self):
        return struct.unpack("!H", self._read(2))[0]

    def write_ushort(self, s):
        """
        @raise ValueError: Not in range.
        """
        if not 0 <= s <= 65536:
            raise ValueError("Not in range (%d)" % s)

        self.write(struct.pack("!H", s))

    def read_short(self):
        return struct.unpack("!h", self._read(2))[0]

    def write_short(self, s):
        """
        @raise ValueError: Not in range.
        """
        if not -32768 <= s <= 32767:
            raise ValueError("Not in range (%d)" % s)

        self.write(struct.pack("!h", s))

    def read_ulong(self):
        return struct.unpack("!L", self._read(4))[0]

    def write_ulong(self, l):
        """
        @raise ValueError: Not in range.
        """
        if not 0 <= l <= 4294967295:
            raise ValueError("Not in range (%d)" % l)

        self.write(struct.pack("!L", l))

    def read_long(self):
        return struct.unpack("!l", self._read(4))[0]

    def write_long(self, l):
        """
        @raise ValueError: Not in range.
        """
        if not -2147483648 <= l <= 2147483647:
            raise ValueError("Not in range (%d)" % l)

        self.write(struct.pack("!l", l))

    def read_double(self):
        return struct.unpack("!d", self._read(8))[0]

    def write_double(self, d):
        self.write(struct.pack("!d", d))

    def write_float(self, f):
        self.write(struct.pack("!f", f))

    def read_float(self):
        return struct.unpack("!f", self._read(4))[0]

    def read_utf8_string(self, length):
        str = struct.unpack("%ds" % length, self.read(length))[0]
        return unicode(str, "utf8")

    def write_utf8_string(self, u):
        self.write(u.encode("utf8"))

class BufferedByteStream(StringIOProxy, NetworkIOMixIn):
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

        @param size:
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
    @param d:
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

def get_attr(obj, attr):
    try:
        return getattr(obj, attr)
    except AttributeError:
        if obj.__class__ == dict:
            return obj[attr]

        raise

def get_mro(C):
    """
    Compute the class precedence list (mro)
    """
    def merge(seqs):
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

# workaround for python2.4's shortcomings with exceptional floats
# see: http://blog.pyamf.org/archives/when-is-nan-not-a-number-with-python-24
import fpconst

fp = struct.unpack("!d", '\xff\xf8\x00\x00\x00\x00\x00\x00')[0]

if not fpconst.isNaN(fp):
    def read_float_workaround(self):
        bytes = self._read(8)

        if bytes == '\xff\xf8\x00\x00\x00\x00\x00\x00':
            return fpconst.NaN

        if bytes == '\xff\xf0\x00\x00\x00\x00\x00\x00':
            return fpconst.NegInf

        if bytes == '\x7f\xf0\x00\x00\x00\x00\x00\x00':
            return fpconst.PosInf

        return struct.unpack("!d", bytes)[0]

    NetworkIOMixIn.read_double = read_float_workaround

    def write_float_workaround(self, d):
        if fpconst.isNaN(d):
            self.write('\xff\xf8\x00\x00\x00\x00\x00\x00')
        elif fpconst.isNegInf(d):
            self.write('\xff\xf0\x00\x00\x00\x00\x00\x00')
        elif fpconst.isPosInf(d):
            self.write('\x7f\xf0\x00\x00\x00\x00\x00\x00')
        else:
            write_float_workaround.old_func(self, d)

    x = NetworkIOMixIn.write_double
    NetworkIOMixIn.write_double = write_float_workaround
    write_float_workaround.old_func = x

del fp
