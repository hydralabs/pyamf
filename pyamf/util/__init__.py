# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.

"""
AMF Utilities.

@since: 0.1.0
"""

import struct
import calendar
import datetime
import types
import inspect

import pyamf

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

try:
    set
except NameError:
    from sets import Set as set


#: XML types.
xml_types = None
ET = None
#: On some Python versions retrieving a negative timestamp, like
#: C{datetime.datetime.utcfromtimestamp(-31536000.0)} is broken.
negative_timestamp_broken = False

int_types = [int]
str_types = [str]

# py3k support
try:
    int_types.append(long)
except NameError:
    pass

try:
    str_types.append(unicode)
except NameError:
    pass

#: Numeric types.
int_types = tuple(int_types)
#: String types.
str_types = tuple(str_types)

PosInf = 1e300000
NegInf = -1e300000
# we do this instead of float('nan') because windows throws a wobbler.
NaN = PosInf / PosInf


def find_xml_lib():
    """
    Run through a predefined order looking through the various C{ElementTree}
    implementations so that any type can be encoded but PyAMF will return
    elements as the first implementation found.

    We work through the C implementations first - then the pure Python
    versions. The downside to this is that a possible of three libraries will
    be loaded into memory that are not used but the libs are small
    (relatively) and the flexibility that this gives seems to outweigh the
    cost. Time will tell.

    @since: 0.4
    """
    global xml_types, ET

    xml_types = []

    try:
        import xml.etree.cElementTree as cET

        ET = cET
        xml_types.append(type(cET.Element('foo')))
    except ImportError:
        pass

    try:
        import cElementTree as cET

        if ET is None:
            ET = cET

        xml_types.append(type(cET.Element('foo')))
    except ImportError:
        pass

    try:
        import xml.etree.ElementTree as pET

        if ET is None:
            ET = pET

        xml_types.append(pET._ElementInterface)
    except ImportError:
        pass

    try:
        import elementtree.ElementTree as pET

        if ET is None:
            ET = pET

        xml_types.append(pET._ElementInterface)
    except ImportError:
        pass

    for x in xml_types[:]:
        # hack for jython
        if x.__name__ == 'instance':
            xml_types.remove(x)

    xml_types = tuple(xml_types)

    return xml_types


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
            raise TypeError("Unable to coerce buf->StringIO")

        self._get_len()
        self._len_changed = False
        self._buffer.seek(0, 0)

    def getvalue(self):
        """
        Get raw data from buffer.
        """
        return self._buffer.getvalue()

    def read(self, n=-1):
        """
        Reads C{n} bytes from the stream.
        """
        bytes = self._buffer.read(n)

        return bytes

    def seek(self, pos, mode=0):
        """
        Sets the file-pointer offset, measured from the beginning of this stream,
        at which the next write operation will occur.

        @param pos:
        @type pos: C{int}
        @param mode:
        @type mode: C{int}
        """
        return self._buffer.seek(pos, mode)

    def tell(self):
        """
        Returns the position of the stream pointer.
        """
        return self._buffer.tell()

    def truncate(self, size=0):
        """
        Truncates the stream to the specified length.

        @param size: The length of the stream, in bytes.
        @type size: C{int}
        """
        if size == 0:
            self._buffer = StringIOProxy._wrapped_class()
            self._len_changed = True

            return

        cur_pos = self.tell()
        self.seek(0)
        buf = self.read(size)
        self._buffer = StringIOProxy._wrapped_class()

        self._buffer.write(buf)
        self.seek(cur_pos)
        self._len_changed = True

    def write(self, s):
        """
        Writes the content of the specified C{s} into this buffer.

        @param s:
        @type s:
        """
        self._buffer.write(s)
        self._len_changed = True

    def _get_len(self):
        """
        Return total number of bytes in buffer.
        """
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

    def consume(self):
        """
        Chops the tail off the stream starting at 0 and ending at C{tell()}.
        The stream pointer is set to 0 at the end of this function.

        @since: 0.4
        """
        try:
            bytes = self.read()
        except IOError:
            bytes = ''

        self.truncate()

        if len(bytes) > 0:
            self.write(bytes)
            self.seek(0)


class DataTypeMixIn(object):
    """
    Provides methods for reading and writing basic data types for file-like
    objects.

    @ivar endian: Byte ordering used to represent the data. Default byte order
        is L{ENDIAN_NETWORK}.
    @type endian: C{str}
    """

    #: Network byte order
    ENDIAN_NETWORK = "!"
    #: Native byte order
    ENDIAN_NATIVE = "@"
    #: Little endian
    ENDIAN_LITTLE = "<"
    #: Big endian
    ENDIAN_BIG = ">"

    endian = ENDIAN_NETWORK

    def _read(self, length):
        """
        Reads C{length} bytes from the stream. If an attempt to read past the
        end of the buffer is made, L{IOError} is raised.
        """
        bytes = self.read(length)

        if len(bytes) != length:
            self.seek(0 - len(bytes), 1)

            raise IOError("Tried to read %d byte(s) from the stream" % length)

        return bytes

    def _is_big_endian(self):
        """
        Whether this system is big endian or not.

        @rtype: C{bool}
        """
        if self.endian == DataTypeMixIn.ENDIAN_NATIVE:
            return DataTypeMixIn._system_endian == DataTypeMixIn.ENDIAN_BIG

        return self.endian in (DataTypeMixIn.ENDIAN_BIG, DataTypeMixIn.ENDIAN_NETWORK)

    def read_uchar(self):
        """
        Reads an C{unsigned char} from the stream.
        """
        return struct.unpack("B", self._read(1))[0]

    def write_uchar(self, c):
        """
        Writes an C{unsigned char} to the stream.

        @param c: Unsigned char
        @type c: C{int}
        @raise TypeError: Unexpected type for int C{c}.
        @raise OverflowError: Not in range.
        """
        if type(c) not in int_types:
            raise TypeError('expected an int (got:%r)' % (type(c),))

        if not 0 <= c <= 255:
            raise OverflowError("Not in range, %d" % c)

        self.write(struct.pack("B", c))

    def read_char(self):
        """
        Reads a C{char} from the stream.
        """
        return struct.unpack("b", self._read(1))[0]

    def write_char(self, c):
        """
        Write a C{char} to the stream.

        @param c: char
        @type c: C{int}
        @raise TypeError: Unexpected type for int C{c}.
        @raise OverflowError: Not in range.
        """
        if type(c) not in int_types:
            raise TypeError('expected an int (got:%r)' % (type(c),))

        if not -128 <= c <= 127:
            raise OverflowError("Not in range, %d" % c)

        self.write(struct.pack("b", c))

    def read_ushort(self):
        """
        Reads a 2 byte unsigned integer from the stream.
        """
        return struct.unpack("%sH" % self.endian, self._read(2))[0]

    def write_ushort(self, s):
        """
        Writes a 2 byte unsigned integer to the stream.

        @param s: 2 byte unsigned integer
        @type s: C{int}
        @raise TypeError: Unexpected type for int C{s}.
        @raise OverflowError: Not in range.
        """
        if type(s) not in int_types:
            raise TypeError('expected an int (got:%r)' % (type(s),))

        if not 0 <= s <= 65535:
            raise OverflowError("Not in range, %d" % s)

        self.write(struct.pack("%sH" % self.endian, s))

    def read_short(self):
        """
        Reads a 2 byte integer from the stream.
        """
        return struct.unpack("%sh" % self.endian, self._read(2))[0]

    def write_short(self, s):
        """
        Writes a 2 byte integer to the stream.

        @param s: 2 byte integer
        @type s: C{int}
        @raise TypeError: Unexpected type for int C{s}.
        @raise OverflowError: Not in range.
        """
        if type(s) not in int_types:
            raise TypeError('expected an int (got:%r)' % (type(s),))

        if not -32768 <= s <= 32767:
            raise OverflowError("Not in range, %d" % s)

        self.write(struct.pack("%sh" % self.endian, s))

    def read_ulong(self):
        """
        Reads a 4 byte unsigned integer from the stream.
        """
        return struct.unpack("%sL" % self.endian, self._read(4))[0]

    def write_ulong(self, l):
        """
        Writes a 4 byte unsigned integer to the stream.

        @param l: 4 byte unsigned integer
        @type l: C{int}
        @raise TypeError: Unexpected type for int C{l}.
        @raise OverflowError: Not in range.
        """
        if type(l) not in int_types:
            raise TypeError('expected an int (got:%r)' % (type(l),))

        if not 0 <= l <= 4294967295:
            raise OverflowError("Not in range, %d" % l)

        self.write(struct.pack("%sL" % self.endian, l))

    def read_long(self):
        """
        Reads a 4 byte integer from the stream.
        """
        return struct.unpack("%sl" % self.endian, self._read(4))[0]

    def write_long(self, l):
        """
        Writes a 4 byte integer to the stream.

        @param l: 4 byte integer
        @type l: C{int}
        @raise TypeError: Unexpected type for int C{l}.
        @raise OverflowError: Not in range.
        """
        if type(l) not in int_types:
            raise TypeError('expected an int (got:%r)' % (type(l),))

        if not -2147483648 <= l <= 2147483647:
            raise OverflowError("Not in range, %d" % l)

        self.write(struct.pack("%sl" % self.endian, l))

    def read_24bit_uint(self):
        """
        Reads a 24 bit unsigned integer from the stream.

        @since: 0.4
        """
        order = None

        if not self._is_big_endian():
            order = [0, 8, 16]
        else:
            order = [16, 8, 0]

        n = 0

        for x in order:
            n += (self.read_uchar() << x)

        return n

    def write_24bit_uint(self, n):
        """
        Writes a 24 bit unsigned integer to the stream.

        @since: 0.4
        @param n: 24 bit unsigned integer
        @type n: C{int}
        @raise TypeError: Unexpected type for int C{n}.
        @raise OverflowError: Not in range.
        """
        if type(n) not in int_types:
            raise TypeError('expected an int (got:%r)' % (type(n),))

        if not 0 <= n <= 0xffffff:
            raise OverflowError("n is out of range")

        order = None

        if not self._is_big_endian():
            order = [0, 8, 16]
        else:
            order = [16, 8, 0]

        for x in order:
            self.write_uchar((n >> x) & 0xff)

    def read_24bit_int(self):
        """
        Reads a 24 bit integer from the stream.

        @since: 0.4
        """
        n = self.read_24bit_uint()

        if n & 0x800000 != 0:
            # the int is signed
            n -= 0x1000000

        return n

    def write_24bit_int(self, n):
        """
        Writes a 24 bit integer to the stream.

        @since: 0.4
        @param n: 24 bit integer
        @type n: C{int}
        @raise TypeError: Unexpected type for int C{n}.
        @raise OverflowError: Not in range.
        """
        if type(n) not in int_types:
            raise TypeError('expected an int (got:%r)' % (type(n),))

        if not -8388608 <= n <= 8388607:
            raise OverflowError("n is out of range")

        order = None

        if not self._is_big_endian():
            order = [0, 8, 16]
        else:
            order = [16, 8, 0]

        if n < 0:
            n += 0x1000000

        for x in order:
            self.write_uchar((n >> x) & 0xff)

    def read_double(self):
        """
        Reads an 8 byte float from the stream.
        """
        return struct.unpack("%sd" % self.endian, self._read(8))[0]

    def write_double(self, d):
        """
        Writes an 8 byte float to the stream.

        @param d: 8 byte float
        @type d: C{float}
        @raise TypeError: Unexpected type for float C{d}.
        """
        if not type(d) is float:
            raise TypeError('expected a float (got:%r)' % (type(d),))

        self.write(struct.pack("%sd" % self.endian, d))

    def read_float(self):
        """
        Reads a 4 byte float from the stream.
        """
        return struct.unpack("%sf" % self.endian, self._read(4))[0]

    def write_float(self, f):
        """
        Writes a 4 byte float to the stream.

        @param f: 4 byte float
        @type f: C{float}
        @raise TypeError: Unexpected type for float C{f}.
        """
        if type(f) is not float:
            raise TypeError('expected a float (got:%r)' % (type(f),))

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
        Writes a unicode object to the stream in UTF-8.

        @param u: unicode object
        @raise TypeError: Unexpected type for str C{u}.
        """
        if type(u) not in str_types:
            raise TypeError('expected a str (got:%r)' % (type(u),))

        bytes = u.encode("utf8")

        self.write(struct.pack("%s%ds" % (self.endian, len(bytes)), bytes))


if struct.pack('@H', 1)[0] == '\x01':
    DataTypeMixIn._system_endian = DataTypeMixIn.ENDIAN_LITTLE
else:
    DataTypeMixIn._system_endian = DataTypeMixIn.ENDIAN_BIG


class BufferedByteStream(StringIOProxy, DataTypeMixIn):
    """
    An extension of C{StringIO}.

    Features:
     - Raises L{IOError} if reading past end.
     - Allows you to C{peek()} at the next byte.

    @see: L{cBufferedByteStream<cpyamf.util.cBufferedByteStream>}
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
        Reads up to the specified number of bytes from the stream into
        the specified byte array of specified length.

        @raise IOError: Attempted to read past the end of the buffer.
        """
        if length == -1 and self.at_eof():
            raise IOError('Attempted to read from the buffer but already at '
                'the end')
        elif length > 0 and self.tell() + length > len(self):
            raise IOError('Attempted to read %d bytes from the buffer but '
                'only %d remain' % (length, len(self) - self.tell()))

        return StringIOProxy.read(self, length)

    def peek(self, size=1):
        """
        Looks C{size} bytes ahead in the stream, returning what it finds,
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

    def remaining(self):
        """
        Returns number of remaining bytes.

        @rtype: C{number}
        @return: Number of remaining bytes.
        """
        return len(self) - self.tell()

    def at_eof(self):
        """
        Returns C{True} if the internal pointer is at the end of the stream.

        @rtype: C{bool}
        """
        return self.tell() == len(self)

    def append(self, data):
        """
        Append data to the end of the stream. The pointer will not move if
        this operation is successful.

        @param data: The data to append to the stream.
        @type data: C{str} or C{unicode}
        @raise TypeError: data is not C{str} or C{unicode}
        """
        t = self.tell()

        # seek to the end of the stream
        self.seek(0, 2)

        if hasattr(data, 'getvalue'):
            self.write_utf8_string(data.getvalue())
        else:
            self.write_utf8_string(data)

        self.seek(t)

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

    msec = str(d.microsecond).rjust(6).replace(' ', '0')

    return float('%s.%s' % (calendar.timegm(d.utctimetuple()), msec))


def get_datetime(secs):
    """
    Return a UTC date from a timestamp.

    @type secs: C{long}
    @param secs: Seconds since 1970.
    @return: UTC timestamp.
    @rtype: C{datetime.datetime}
    """
    if secs < 0 and negative_timestamp_broken:
        return datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds=secs)

    return datetime.datetime.utcfromtimestamp(secs)


def get_properties(obj):
    """
    @since: 0.5
    """
    if hasattr(obj, 'keys'):
        return set(obj.keys())
    elif hasattr(obj, '__dict__'):
        return obj.__dict__.keys()

    return []


def get_attrs(obj):
    """
    Gets a C{dict} of the attrs of an object in a predefined resolution order.

    @raise AttributeError: A duplicate attribute was already found in this
        collection, are you mixing different key types?
    """
    if hasattr(obj, 'iteritems'):
        attrs = {}

        for k, v in obj.iteritems():
            sk = str(k)

            if sk in attrs.keys():
                raise AttributeError('A duplicate attribute (%s) was '
                    'already found in this collection, are you mixing '
                    'different key types?' % (sk,))

            attrs[sk] = v

        return attrs
    elif hasattr(obj, '__dict__'):
        return obj.__dict__.copy()
    elif hasattr(obj, '__slots__'):
        attrs = {}

        for k in obj.__slots__:
            attrs[k] = getattr(obj, k)

        return attrs

    return None


def set_attrs(obj, attrs):
    """
    A generic function which applies a collection of attributes C{attrs} to
    object C{obj}.

    @param obj: An instance implementing the C{__setattr__} function
    @param attrs: A collection implementing the C{iteritems} function
    @type attrs: Usually a dict
    """
    if isinstance(obj, (list, dict)):
        for k, v in attrs.iteritems():
            obj[k] = v

        return

    for k, v in attrs.iteritems():
        setattr(obj, k, v)


def get_class_alias(klass):
    """
    Returns a alias class suitable for klass. Defaults to L{pyamf.ClassAlias}
    """
    for k, v in pyamf.ALIAS_TYPES.iteritems():
        for kl in v:
            if isinstance(kl, types.FunctionType):
                if kl(klass) is True:
                    return k
            elif isinstance(kl, (type, (types.ClassType, types.ObjectType))):
                if issubclass(klass, kl):
                    return k

    return pyamf.ClassAlias


def is_class_sealed(klass):
    """
    Returns a C{boolean} whether or not the supplied class can accept dynamic
    properties.

    @rtype: C{bool}
    @since: 0.5
    """
    mro = inspect.getmro(klass)
    new = False

    if mro[-1] is object:
        mro = mro[:-1]
        new = True

    for kls in mro:
        if new and '__dict__' in kls.__dict__:
            return False

        if not hasattr(kls, '__slots__'):
            return False

    return True


def get_class_meta(klass):
    """
    Returns a C{dict} containing meta data based on the supplied class, useful
    for class aliasing.

    @rtype: C{dict}
    @since: 0.5
    """
    if not isinstance(klass, (type, types.ClassType)) or klass is object:
        raise TypeError('klass must be a class object, got %r' % type(klass))

    meta = {
        'static_attrs': None,
        'exclude_attrs': None,
        'readonly_attrs': None,
        'amf3': None,
        'dynamic': None,
        'alias': None,
        'external': None
    }

    if not hasattr(klass, '__amf__'):
        return meta

    a = klass.__amf__

    if type(a) is dict:
        in_func = lambda x: x in a
        get_func = a.__getitem__
    else:
        in_func = lambda x: hasattr(a, x)
        get_func = lambda x: getattr(a, x)

    for prop in ['alias', 'amf3', 'dynamic', 'external']:
        if in_func(prop):
            meta[prop] = get_func(prop)

    for prop in ['static', 'exclude', 'readonly']:
        if in_func(prop):
            meta[prop + '_attrs'] = list(get_func(prop))

    return meta


class IndexedCollection(object):
    """
    A class that provides a quick and clean way to store references and
    referenced objects.

    @note: All attributes on the instance are private.
    @ivar exceptions: If C{True} then L{ReferenceError<pyamf.ReferenceError>}
        will be raised, otherwise C{None} will be returned.
    """

    def __init__(self, use_hash=False, exceptions=True):
        if use_hash is True:
            self.func = hash
        else:
            self.func = id

        self.exceptions = exceptions

        self.clear()

    def clear(self):
        """
        Clears the index.
        """
        self.list = []
        self.dict = {}

    def getByReference(self, ref):
        """
        Returns an object based on the reference.

        @raise TypeError: Bad reference type.
        @raise pyamf.ReferenceError: Reference not found.
        """
        if not isinstance(ref, (int, long)):
            raise TypeError("Bad reference type")

        try:
            return self.list[ref]
        except IndexError:
            if self.exceptions is False:
                return None

            raise pyamf.ReferenceError("Reference %r not found" % (ref,))

    def getReferenceTo(self, obj):
        """
        Returns a reference to C{obj} if it is contained within this index.

        @raise pyamf.ReferenceError: Value not found.
        """
        try:
            return self.dict[self.func(obj)]
        except KeyError:
            if self.exceptions is False:
                return None

            raise pyamf.ReferenceError("Value %r not found" % (obj,))

    def append(self, obj):
        """
        Appends C{obj} to this index.

        @note: Uniqueness is not checked
        @return: The reference to C{obj} in this index.
        """
        h = self.func(obj)

        self.list.append(obj)
        idx = len(self.list) - 1
        self.dict[h] = idx

        return idx

    def __eq__(self, other):
        if isinstance(other, list):
            return self.list == other
        elif isinstance(other, dict):
            return self.dict == other

        return False

    def __len__(self):
        return len(self.list)

    def __getitem__(self, idx):
        return self.getByReference(idx)

    def __contains__(self, obj):
        try:
            r = self.getReferenceTo(obj)
        except pyamf.ReferenceError:
            r = None

        return r is not None

    def __repr__(self):
        return '<%s list=%r dict=%r>' % (self.__class__.__name__, self.list, self.dict)

    def __iter__(self):
        return iter(self.list)


class IndexedMap(IndexedCollection):
    """
    Like L{IndexedCollection}, but also maps to another object.

    @since: 0.4
    """

    def __init__(self, use_hash=False, exceptions=True):
        IndexedCollection.__init__(self, use_hash, exceptions)

    def clear(self):
        """
        Clears the index and mapping.
        """
        IndexedCollection.clear(self)

        self.mapped = []

    def getMappedByReference(self, ref):
        """
        Returns the mapped object by reference.

        @raise TypeError: Bad reference type.
        @raise pyamf.ReferenceError: Reference not found.
        """
        if not isinstance(ref, (int, long)):
            raise TypeError("Bad reference type.")

        try:
            return self.mapped[ref]
        except IndexError:
            if self.exceptions is False:
                return None

            raise pyamf.ReferenceError("Reference %r not found" % ref)

    def append(self, obj):
        """
        Appends C{obj} to this index.

        @return: The reference to C{obj} in this index.
        """
        idx = IndexedCollection.append(self, obj)
        diff = (idx + 1) - len(self.mapped)

        for i in range(0, diff):
            self.mapped.append(None)

        return idx

    def map(self, obj, mapped_obj):
        """
        Maps an object.
        """
        idx = self.append(obj)
        self.mapped[idx] = mapped_obj

        return idx


def is_ET_element(obj):
    """
    Determines if the supplied C{obj} param is a valid ElementTree element.
    """
    return isinstance(obj, xml_types)


def is_float_broken():
    """
    Older versions of Python (<=2.5) and the Windows platform are renowned for
    mixing up 'special' floats. This function determines whether this is the
    case.

    @since: 0.4
    @rtype: C{bool}
    """
    global NaN

    return str(NaN) != str(struct.unpack("!d", '\xff\xf8\x00\x00\x00\x00\x00\x00')[0])


def isNaN(val):
    """
    @since: 0.5
    """
    return str(float(val)) == str(NaN)


def isPosInf(val):
    """
    @since: 0.5
    """
    return str(float(val)) == str(PosInf)


def isNegInf(val):
    """
    @since: 0.5
    """
    return str(float(val)) == str(NegInf)


# init the module from here ..

find_xml_lib()

try:
    datetime.datetime.utcfromtimestamp(-31536000.0)
except ValueError:
    negative_timestamp_broken = True

if is_float_broken():
    def read_double_workaround(self):
        global PosInf, NegInf, NaN

        """
        Override the L{DataTypeMixIn.read_double} method to fix problems
        with doubles by using the third-party C{fpconst} library.
        """
        bytes = self.read(8)

        if self._is_big_endian():
            if bytes == '\xff\xf8\x00\x00\x00\x00\x00\x00':
                return NaN

            if bytes == '\xff\xf0\x00\x00\x00\x00\x00\x00':
                return NegInf

            if bytes == '\x7f\xf0\x00\x00\x00\x00\x00\x00':
                return PosInf
        else:
            if bytes == '\x00\x00\x00\x00\x00\x00\xf8\xff':
                return NaN

            if bytes == '\x00\x00\x00\x00\x00\x00\xf0\xff':
                return NegInf

            if bytes == '\x00\x00\x00\x00\x00\x00\xf0\x7f':
                return PosInf

        return struct.unpack("%sd" % self.endian, bytes)[0]

    DataTypeMixIn.read_double = read_double_workaround

    def write_double_workaround(self, d):
        """
        Override the L{DataTypeMixIn.write_double} method to fix problems
        with doubles by using the third-party C{fpconst} library.
        """
        if type(d) is not float:
            raise TypeError('expected a float (got:%r)' % (type(d),))

        if isNaN(d):
            if self._is_big_endian():
                self.write('\xff\xf8\x00\x00\x00\x00\x00\x00')
            else:
                self.write('\x00\x00\x00\x00\x00\x00\xf8\xff')
        elif isNegInf(d):
            if self._is_big_endian():
                self.write('\xff\xf0\x00\x00\x00\x00\x00\x00')
            else:
                self.write('\x00\x00\x00\x00\x00\x00\xf0\xff')
        elif isPosInf(d):
            if self._is_big_endian():
                self.write('\x7f\xf0\x00\x00\x00\x00\x00\x00')
            else:
                self.write('\x00\x00\x00\x00\x00\x00\xf0\x7f')
        else:
            write_double_workaround.old_func(self, d)

    x = DataTypeMixIn.write_double
    DataTypeMixIn.write_double = write_double_workaround
    write_double_workaround.old_func = x


try:
    from cpyamf.util import BufferedByteStream, IndexedCollection, IndexedMap

    class StringIOProxy(BufferedByteStream):
        _wrapped_class = None

        def __init__(self, *args, **kwargs):
            BufferedByteStream.__init__(self, *args, **kwargs)
            self._buffer = self

    class DataTypeMixIn(BufferedByteStream):
        #: Network byte order
        ENDIAN_NETWORK = "!"
        #: Native byte order
        ENDIAN_NATIVE = "@"
        #: Little endian
        ENDIAN_LITTLE = "<"
        #: Big endian
        ENDIAN_BIG = ">"
except ImportError:
    pass
