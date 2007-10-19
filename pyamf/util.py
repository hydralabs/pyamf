# -*- encoding: utf8 -*-
#
# Copyright (c) 2007 The PyAMF Project. All rights reserved.
# 
# Arnar Birgisson
# Thijs Triemstra
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

import struct
import time
from StringIO import StringIO

class NetworkIOMixIn:
    """Provides mix-in methods for file like objects to read and write basic
    datatypes in network (= big-endian) byte-order."""
    
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
    """An extension of StringIO that:
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

    def peek(self):
        if self.at_eof():
            return None
        else:
            c = self.read(1)
            self.seek(self.tell()-1)
            return c

    def at_eof(self):
        "Returns true if next .read(1) will trigger EOFError"
        return self.tell() >= self.len
    
    def remaining(self):
        "Returns number of remaining bytes"
        return self.len - self.tell()


# Enum from python cookbook
def Enum(*names):
   ##assert names, "Empty enums are not supported" # <- Don't like empty enums? Uncomment!

   class EnumClass(object):
      __slots__ = names
      def __iter__(self):        return iter(constants)
      def __len__(self):         return len(constants)
      def __getitem__(self, i):  return constants[i]
      def __repr__(self):        return 'Enum' + str(names)
      def __str__(self):         return 'enum ' + str(constants)

   class EnumValue(object):
      __slots__ = ('__value')
      def __init__(self, value): self.__value = value
      Value = property(lambda self: self.__value)
      EnumType = property(lambda self: EnumType)
      def __hash__(self):        return hash(self.__value)
      def __cmp__(self, other):
         # C fans might want to remove the following assertion
         # to make all enums comparable by ordinal value {;))
         # assert self.EnumType is other.EnumType, "Only values from the same enum are comparable"
         return cmp(self.__value, other.__value)
      def __invert__(self):      return constants[maximum - self.__value]
      def __nonzero__(self):     return bool(self.__value)
      def __repr__(self):        return str(names[self.__value])

   maximum = len(names) - 1
   constants = [None] * len(names)
   for i, each in enumerate(names):
      val = EnumValue(i)
      setattr(EnumClass, each, val)
      constants[i] = val
   constants = tuple(constants)
   EnumType = EnumClass()
   return EnumType

def hexdump(data):
    import string
    hex = ascii = ""
    buf = ""
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

def uptime():
    """Returns uptime in milliseconds, starting at first call"""
    if not hasattr(uptime, "t0") is None:
        uptime.t0 = time.time()
    return int((time.time() - uptime.t0)*1000)

def decode_utf8_modified(data):
    """Decodes a unicode string from Modified UTF-8 data.
    See http://en.wikipedia.org/wiki/UTF-8#Java for details."""
    # Ported from http://viewvc.rubyforge.mmmultiworks.com/cgi/viewvc.cgi/trunk/lib/ruva/class.rb
    # Ruby version is Copyright (c) 2006 Ross Bamford (rosco AT roscopeco DOT co DOT uk).
    # The string is first converted to UTF16 BE
    utf16 = []
    i = 0
    while i < len(data):
        c = ord(data[i])
        if 0x00 < c < 0x80:
            utf16.append(c)
            i += 1
        elif c & 0xc0 == 0xc0:
            utf16.append(((c & 0x1f) << 6) | (ord(data[i+1]) & 0x3f))
            i += 2
        elif c & 0xe0 == 0xe0:
            utf16.append(((c & 0x0f) << 12) | ((ord(data[i+1]) & 0x3f) << 6) | (ord(data[i+2]) & 0x3f))
            i += 3
        else:
            raise ValueError("Data is not valid modified UTF-8")
    
    utf16 = "".join([chr((c >> 8) & 0xff) + chr(c & 0xff) for c in utf16])
    return unicode(utf16, "utf_16_be")
