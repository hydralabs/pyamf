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
#
# AMF parser
# sources:
#   http://www.vanrijkom.org/archives/2005/06/amf_format.html
#   http://osflash.org/documentation/amf/astypes

"""AMF0 Implementation"""

import datetime
from types import *

from pyamf import util

class ASTypes:
    """
    A placeholder for all AMF0 ActionScript types.
    Ref: http://osflash.org/documentation/amf/astypes
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

class Parser(object):
    """
    Parses an AMF0 stream
    """
    obj_refs = []
    # XXX nick: Do we need to support ASTypes.MOVIECLIP here?
    type_map = {
        ASTypes.NUMBER: 'readNumber',
        ASTypes.BOOL: 'readBool',
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

    def __init__(self, data):
        # coersce data to BufferedByteStream
        if isinstance(data, util.BufferedByteStream):
            self.input = data
        else:
            self.input = util.BufferedByteStream(data)

    def readType(self):
        """
        Read and returns the next byte in the stream and determine its type.
        Raises ValueError if not recognized
        """
        type = self.input.read_uchar()

        if type not in ACTIONSCRIPT_TYPES:
            raise ValueError("Unknown AMF0 type 0x%02x at %d" % (
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
        obj = self.readObject()

        for key in obj.keys():
            try:
                ikey = int(key)
                obj[ikey] = obj[key]
                del obj[key]
            except ValueError:
                # XXX: do we want to ignore this?
                pass

        return obj

    def readList(self):
        len = self.input.read_ulong()
        obj = []
        self.obj_refs.append(obj)

        obj.extend(self.readElement() for i in xrange(len))

        return obj

    def readTypedObject(self):
        classname = self.readString()
        obj = self.readObject()

        # TODO do some class mapping?
        return obj

    def readAMF3(self):
        from pyamf import amf3

        # XXX: Does the amf3 parser have access to the same references as amf0?
        p = amf3.Parser(self.input)

        return p.readElement()

    def readElement(self):
        """Reads the data type."""
        type = self.readType()

        try:
            func = getattr(self, self.type_map[type])
        except KeyError, e:
            raise NotImplementedError(
                "Unknown ActionScript type 0x%02x" % type)

        return func()

    def readString(self):
        len = self.input.read_ushort()
        return self.input.read_utf8_string(len)

    def readObject(self):
        obj = dict()
        self.obj_refs.append(obj)
        key = self.readString()
        while self.input.peek() != chr(ASTypes.OBJECTTERM):
            obj[key] = self.readElement()
            key = self.readString()
        self.input.read(1) # discard the end marker (ASTypes.OBJECTTERM = 0x09)
        return obj

    def readReference(self):
        idx = self.input.read_ushort()
        return self.obj_refs[idx]

    def readDate(self):
        """Reads a date.
        Date: 0x0B T7 T6 .. T0 Z1 Z2 T7 to T0 form a 64 bit Big Endian number
        that specifies the number of nanoseconds that have passed since
        1/1/1970 0:00 to the specified time. This format is UTC 1970. Z1 an
        Z0 for a 16 bit Big Endian number indicating the indicated time's
        timezone in minutes."""
        ms = self.input.read_double()
        tz = self.input.read_short()
        class TZ(datetime.tzinfo):
            def utcoffset(self, dt):
                return datetime.timedelta(minutes=tz)
            def dst(self,dt):
                return None
            def tzname(self,dt):
                return None
        return datetime.datetime.fromtimestamp(ms/1000.0, TZ())

    def readLongString(self):
        len = self.input.read_ulong()
        return self.input.read_utf8_string(len)

    def readXML(self):
        data = readLongString()
        return ET.fromstring(data)

class Encoder(object):

    type_map = [
        ((bool,), "writeBoolean"),
        ((int,long,float), "writeNumber"), # Maybe add decimal ?
        ((StringTypes,), "writeString"),
        ((InstanceType,DictType,), "writeObject"),
        ((ListType,TupleType,), "writeArray"),
        ((datetime.date, datetime.datetime), "writeDate"),
        ((util.ET._ElementInterface,), "writeXML"),
        ((NoneType,), "writeNull"),
    ]

    def __init__(self, output):
        """Constructs a new Encoder. output should be a writable
        file-like object."""
        self.output = output
        self.obj_refs = []

    def writeType(self, type):
        """
        Writes the type to the stream. Raises ValueError if type is not
        recognized
        """
        if type not in ACTIONSCRIPT_TYPES:
            raise ValueError("Unknown AMF0 type 0x%02x at %d" % (
                type, self.input.tell() - 1))

        self.output.write_uchar(type)

    def writeElement(self, data):
        """Writes the data."""
        for tlist, method in self.type_map:
            for t in tlist:
                if isinstance(data, t):
                    return getattr(self, method)(data)

    def writeNull(self, n):
        self.writeType(ASTypes.NULL)

    def writeArray(self, a):
        self.writeType(ASTypes.ARRAY)
        self.output.write_ushort(len(a))
        for data in a:
            self.writeElement(data)

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

    def writeObject(self, o):
        if o in self.obj_refs:
            self.writeType(ASTypes.REFERENCE)
            self.output.write_ushort(self.obj_refs.index(o))
        else:
            self.obj_refs.append(o)
            self.writeType(ASTypes.OBJECT)
            # TODO: give objects a chance of controlling what we send
            o = o.__dict_
            for key, val in o.items():
                self.writeString(key, False)
                self.writeElement(o)
            self.writeString("", False)
            self.writeType(ASTypes.OBJECTTERM)

    def writeDate(self, d):
        if isinstance(d, datetime.date):
            d = datetime.datetime.combine(d, datetime.time(0))
        self.writeType(ASTypes.DATE)
        ms = time.mktime(d.timetuple)
        if d.tzinfo:
            tz = d.tzinfo.utcoffset.days*1440 + d.tzinfo.utcoffset.seconds/60
        else:
            tz = 0
        self.output.write_double(ms)
        self.output.write_short(tz)

    def writeXML(self, e):
        self.writeType(ASTypes.XML)
        data = ET.tostring(e, 'utf8')
        self.output.write_ulong(len(data))
        self.output.write(data)
