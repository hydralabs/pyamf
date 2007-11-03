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
#
# AMF decoder
# sources:
#   http://www.vanrijkom.org/archives/2005/06/amf_format.html
#   http://osflash.org/documentation/amf/astypes

"""AMF0 Implementation"""

import datetime, calendar, types

import pyamf
from pyamf import util

class ASTypes:
    """
    A placeholder for all AMF0 ActionScript types.

    Reference: U{http://osflash.org/documentation/amf/astypes}
    """

    NUMBER      = 0x00
    BOOL        = 0x01
    STRING      = 0x02
    OBJECT      = 0x03
    # Not available in remoting
    MOVIECLIP   = 0x04
    NULL        = 0x05
    UNDEFINED   = 0x06
    REFERENCE   = 0x07
    MIXEDARRAY  = 0x08
    OBJECTTERM  = 0x09
    ARRAY       = 0x0a
    DATE        = 0x0b
    LONGSTRING  = 0x0c
    UNSUPPORTED = 0x0d
    # Remoting Server -> Client only
    RECORDSET   = 0x0e
    XML         = 0x0f
    TYPEDOBJECT = 0x10
    AMF3        = 0x11

ACTIONSCRIPT_TYPES = set(
    ASTypes.__dict__[x] for x in ASTypes.__dict__ if not x.startswith('__'))

class Decoder(object):
    """
    Parses an AMF0 stream
    """
    # XXX nick: Do we need to support ASTypes.MOVIECLIP here?
    type_map = {
        ASTypes.NUMBER: 'readNumber',
        ASTypes.BOOL: 'readBoolean',
        ASTypes.STRING: 'readString',
        ASTypes.OBJECT: 'readObject',
        ASTypes.NULL: 'readNull',
        # TODO: do we need a special value here?
        ASTypes.UNDEFINED: 'readNull',
        ASTypes.REFERENCE: 'readReference',
        ASTypes.MIXEDARRAY: 'readMixedArray',
        ASTypes.ARRAY: 'readList',
        ASTypes.DATE: 'readDate',
        ASTypes.LONGSTRING: 'readLongString',
        # TODO: do we need a special value here?
        ASTypes.UNSUPPORTED: 'readNull',
        ASTypes.XML: 'readXML',
        ASTypes.TYPEDOBJECT: 'readTypedObject',
        ASTypes.AMF3: 'readAMF3'
    }

    def __init__(self, data=None, context=None):
        # coersce data to BufferedByteStream
        if isinstance(data, util.BufferedByteStream):
            self.input = data
        else:
            self.input = util.BufferedByteStream(data)

        if context == None:
            self.context = pyamf.Context()
        else:
            self.context = context

    def readType(self):
        """
        Read and returns the next byte in the stream and determine its type.
        Raises ValueError if not recognized
        """
        type = self.input.read_uchar()

        if type not in ACTIONSCRIPT_TYPES:
            raise pyamf.ParseError("Unknown AMF0 type 0x%02x at %d" % (
                type, self.input.tell() - 1))

        return type

    def readNumber(self):
        """
        Reads a Number. In ActionScript 1 and 2 NumberASTypes type
        represents all numbers, both floats and integers.
        """
        return self.input.read_double()

    def readBoolean(self):
        return bool(self.input.read_uchar())

    def readNull(self):
        return None

    def readMixedArray(self):
        """
        Returns an array
        """
        len = self.input.read_ulong()
        obj = {}
        self._readObject(obj)

        for key in obj.keys():
            try:
                ikey = int(key)
                obj[ikey] = obj[key]
                del obj[key]
            except ValueError:
                # XXX: do we want to ignore this?
                pass

        self.context.addObject(obj)

        return obj

    def readList(self):
        obj = []
        len = self.input.read_ulong()

        for i in xrange(len):
            obj.append(self.readElement())

        self.context.addObject(obj)

        return obj

    def readTypedObject(self):
        """
        Reads an object from the stream and attempts to 'cast' it. See
        L{pyamf.load_class} for more info.
        """
        classname = self.readString()
        klass = pyamf.load_class(classname)

        ret = klass()
        obj = {}
        self._readObject(obj)

        for k, v in obj.iteritems():
            setattr(ret, k, v)

        self.context.addObject(obj)

        return ret

    def readAMF3(self):
        from pyamf import amf3

        # XXX: Does the amf3 decoder have access to the same references as amf0?
        p = amf3.Decoder(self.input, self.context)

        return p.readElement()

    def readElement(self):
        """
        Reads an element from the data stream.
        """
        type = self.readType()

        try:
            func = getattr(self, self.type_map[type])
        except KeyError, e:
            raise pyamf.ParseError(
                "Unknown ActionScript type 0x%02x" % type)

        return func()

    def readString(self):
        """
        Reads a string from the data stream.
        """
        len = self.input.read_ushort()
        return self.input.read_utf8_string(len)

    def _readObject(self, obj):
        key = self.readString()

        while self.input.peek() != chr(ASTypes.OBJECTTERM):
            obj[key] = self.readElement()
            key = self.readString()

        # discard the end marker (ASTypes.OBJECTTERM)
        self.input.read(len(chr(ASTypes.OBJECTTERM)))

    def readObject(self):
        """
        Reads an object from the AMF stream.

        @return The object
        @rettype __builtin__.object
        """
        obj = pyamf.Bag()

        self._readObject(obj)
        self.context.addObject(obj)

        return obj

    def readReference(self):
        idx = self.input.read_ushort()
        return self.context.getObject(idx)

    def readDate(self):
        """
        Reads a UTC date from the data stream

        Date: 0x0B T7 T6 .. T0 Z1 Z2 T7 to T0 form a 64 bit Big Endian number
        that specifies the number of nanoseconds that have passed since
        1/1/1970 0:00 to the specified time. This format is UTC 1970. Z1 an
        Z0 for a 16 bit Big Endian number indicating the indicated time's
        timezone in minutes.
        """
        ms = self.input.read_double() / 1000.0
        tz = self.input.read_short()

        # Timezones are ignored
        d = datetime.datetime.utcfromtimestamp(ms)
        self.context.addObject(d)

        return d

    def readLongString(self):
        len = self.input.read_ulong()
        return self.input.read_utf8_string(len)

    def readXML(self):
        data = self.readLongString()
        return util.ET.fromstring(data)

class Encoder(object):

    type_map = [
        # Unsupported types go first
        ((types.BuiltinFunctionType, types.BuiltinMethodType,), "writeUnsupported"),
        ((bool,), "writeBoolean"),
        ((int,long,float), "writeNumber"),
        ((types.StringTypes,), "writeString"),
        ((util.ET._ElementInterface,), "writeXML"),
        ((pyamf.Bag,), "writeObject"),
        ((types.DictType,), "writeMixedArray"),
        ((types.ListType,types.TupleType,), "writeArray"),
        ((datetime.date, datetime.datetime), "writeDate"),
        ((types.NoneType,), "writeNull"),
        ((types.InstanceType,types.ObjectType,), "writeObject"),
    ]

    def __init__(self, output, context=None):
        """Constructs a new Encoder. output should be a writable
        file-like object."""
        self.output = output

        if context == None:
            self.context = pyamf.Context()
        else:
            self.context = context

    def writeType(self, type):
        """
        Writes the type to the stream. Raises ValueError if type is not
        recognized
        """
        if type not in ACTIONSCRIPT_TYPES:
            raise ValueError("Unknown AMF0 type 0x%02x at %d" % (
                type, self.output.tell() - 1))

        self.output.write_uchar(type)

    def writeUnsupported(self, data):
        self.writeType(ASTypes.UNSUPPORTED)

    def writeElement(self, data):
        """Writes the data."""
        for tlist, method in self.type_map:
            for t in tlist:
                if isinstance(data, t):
                    return getattr(self, method)(data)

        self.writeUnsupported(data)

    def writeNull(self, n):
        self.writeType(ASTypes.NULL)

    def writeArray(self, a):
        try:
            self.writeReference(a)
            return
        except pyamf.ReferenceError:
            pass

        self.writeType(ASTypes.ARRAY)
        self.output.write_ulong(len(a))

        for data in a:
            self.writeElement(data)

        self.context.addObject(a)

    def writeNumber(self, n):
        self.writeType(ASTypes.NUMBER)
        self.output.write_double(float(n))

    def writeBoolean(self, b):
        self.writeType(ASTypes.BOOL)

        if b:
            self.output.write_uchar(1)
        else:
            self.output.write_uchar(0)

    def writeString(self, s, writeType=True):
        s = unicode(s).encode('utf8')
        if len(s) > 0xffff:
            if writeType:
                self.writeType(ASTypes.LONGSTRING)
            self.output.write_ulong(len(s))
        else:
            if writeType:
                self.output.write_uchar(ASTypes.STRING)
            self.output.write_ushort(len(s))
        self.output.write(s)

    def writeReference(self, o):
        idx = self.context.getObjectReference(o)

        self.writeType(ASTypes.REFERENCE)
        self.output.write_ushort(idx)

    def _writeDict(self, o):
        for key, val in o.items():
            self.writeString(key, False)
            self.writeElement(val)

    def writeMixedArray(self, o):
        try:
            self.writeReference(o)
            return
        except pyamf.ReferenceError:
            pass

        self.writeType(ASTypes.MIXEDARRAY)

        # TODO optimise this
        # work out the highest integer index
        try:
            # list comprehensions to save the day
            max_index = max([y[0] for y in o.items()
                if isinstance(y[0], (int, long))])

            if max_index < 0:
                max_index = 0
        except ValueError, e:
            max_index = 0

        self.output.write_ulong(max_index)

        self._writeDict(o)
        self._writeEndObject()
        self.context.addObject(o)

    def _writeEndObject(self):
        self.writeString("", False)
        self.writeType(ASTypes.OBJECTTERM)

    def writeObject(self, o):
        try:
            self.writeReference(o)
            return
        except pyamf.ReferenceError:
            pass

        # Need to check here if this object has a registered alias
        try:
            alias = pyamf.get_class_alias(o)
            self.writeType(ASTypes.TYPEDOBJECT)
            self.writeString(alias, False)
        except LookupError:
            self.writeType(ASTypes.OBJECT)

        # TODO: give objects a chance of controlling what we send
        if 'iteritems' in dir(o):
            it = o.iteritems()
        else:
            it = o.__dict__.iteritems()

        for key, val in it:
            self.writeString(key, False)
            self.writeElement(val)

        self._writeEndObject()
        self.context.addObject(o)

    def writeDate(self, d):
        """
        Writes a date to the data stream.

        If d.tzinfo is None, d will be assumed to be in UTC
        """
        try:
            self.writeReference(d)
            return
        except pyamf.ReferenceError:
            self.context.addObject(d)

        secs = util.get_timestamp(d)
        tz = 0

        self.writeType(ASTypes.DATE)
        self.output.write_double(secs * 1000.0)
        self.output.write_short(tz)

    def writeXML(self, e):
        data = util.ET.tostring(e, 'utf8')

        self.writeType(ASTypes.XML)
        self.output.write_ulong(len(data))
        self.output.write(data)

def decode(stream, context=None):
    """
    A helper function to decode an AMF0 datastream. 
    """
    decoder = Decoder(stream, context)

    for el in decoder.readElement():
        yield el

def encode(element, context=None):
    """
    A helper function to encode an element into AMF0 format.

    Returns a StringIO object
    """
    buf = util.BufferedByteStream()
    encoder = Encoder(buf, context)

    encoder.writeElement(element)

    return buf
