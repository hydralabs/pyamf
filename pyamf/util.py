# -*- encoding: utf8 -*-
#
# Copyright (c) 2007 The PyAMF Project. All rights reserved.
# 
# Arnar Birgisson
# Thijs Triemstra
# Nick Joyce
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

"""
Utility for PyAMF
"""

import struct, calendar, datetime
from StringIO import StringIO

try:
    import xml.etree.ElementTree as ET
except ImportError:
    try:
        import cElementTree as ET
    except ImportError:
        import elementtree.ElementTree as ET

class NetworkIOMixIn(object):
    """
    Provides mix-in methods for file like objects to read and write basic
    datatypes in network (= big-endian) byte-order.
    """

    def read_uchar(self):
        return struct.unpack("!B", self.read(1))[0]

    def write_uchar(self, c):
        self.write(struct.pack("!B", c))

    def read_char(self):
        return struct.unpack("!b", self.read(1))[0]

    def write_char(self, c):
        self.write(struct.pack("!b", c))

    def read_ushort(self):
        return struct.unpack("!H", self.read(2))[0]

    def write_ushort(self, s):
        self.write(struct.pack("!H", s))

    def read_short(self):
        return struct.unpack("!h", self.read(2))[0]

    def write_short(self, s):
        self.write(struct.pack("!h", s))

    def read_ulong(self):
        return struct.unpack("!L", self.read(4))[0]

    def write_ulong(self, l):
        self.write(struct.pack("!L", l))

    def read_long(self):
        return struct.unpack("!l", self.read(4))[0]

    def write_long(self, l):
        self.write(struct.pack("!l", l))

    def read_double(self):
        return struct.unpack("!d", self.read(8))[0]

    def write_double(self, d):
        self.write(struct.pack("!d", d))

    def read_utf8_string(self, length):
        str = struct.unpack("%ds" % length, self.read(length))[0]
        return unicode(str, "utf8")

    def write_utf8_string(self, u):
        self.write(u.encode("utf8"))

class BufferedByteStream(StringIO, NetworkIOMixIn):
    """
    An extension of StringIO that:
     - Raises EOFError if reading past end
     - Allows you to peek() at the next byte
    """

    def __init__(self, *args, **kwargs):
        StringIO.__init__(self, *args, **kwargs)

    def read(self, length=-1):
        if length > 0 and self.at_eof():
            raise EOFError
        if length > 0 and self.tell() + length > self.len:
            length = self.len - self.tell()
        return StringIO.read(self, length)

    def peek(self, size=1):
        """
        Looks size bytes ahead in the stream, returning what it finds,
        returning the stream pointer to its initial position.
        """
        if size == -1:
            return self.peek(self.len - self.tell())

        bytes = ''
        pos = self.tell()

        while not self.at_eof() and len(bytes) != size:
            bytes += self.read(1)

        self.seek(pos)

        return bytes

    def at_eof(self):
        """
        Returns true if next .read(1) will trigger EOFError
        """
        return self.tell() >= self.len

    def remaining(self):
        """
        Returns number of remaining bytes
        """
        return self.len - self.tell()

def hexdump(data):
    import string

    hex = ascii = bug = ""
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
    Returns a UTC timestamp for a datetime.datetime object.

    Inspiration taken from:
    http://intertwingly.net/blog/2007/09/02/Dealing-With-Dates
    """
    return calendar.timegm(d.utctimetuple())

def get_datetime(ms):
    """
    Return a UTC date from a timestamp
    """
    return datetime.datetime.utcfromtimestamp(ms)
