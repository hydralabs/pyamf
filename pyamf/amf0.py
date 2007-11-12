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

"""
AMF0 implementation.

AMF0 supports the basic data types used for the NetConnection, NetStream,
LocalConnection, SharedObjects and other classes in the Flash Player.

@see: U{AMF documentation on OSFlash (external)
<http://osflash.org/documentation/amf>}

@author: U{Arnar Birgisson<mailto:arnarbi@gmail.com>}
@author: U{Thijs Triemstra<mailto:info@collab.nl>}
@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import datetime, types

import pyamf
from pyamf import util

class ASTypes:
    """
    All AMF0 data types used in ActionScript 1.0 and 2.0.

    @see: U{Documentation on OSFlash (external)
    <http://osflash.org/documentation/amf/astypes>}
    """
    #: Represented as 9 bytes: 1 byte for 0×00 and 8 bytes a double
    #: representing the value of the number.
    NUMBER      = 0x00
    #: Represented as 2 bytes: 1 byte for 0×01 and a second, 0×00
    #: for false, 0×01 for true.
    BOOL        = 0x01
    #: Represented as 3 bytes + len(String): 1 byte 0×02, then a UTF8 string,
    #: including the top two bytes representing string length as a int.
    STRING      = 0x02
    #: Represented as 1 byte, 0×03, then pairs of UTF8 string, the key, and
    #: an AMF element, ended by three bytes, 0×00 0×00 0×09.
    OBJECT      = 0x03
    #: MovieClip does not seem to be supported by Remoting.
    #: It may be used by other AMF clients such as SharedObjects.
    MOVIECLIP   = 0x04
    #: 1 single byte, 0×05 indicates null.
    NULL        = 0x05
    #: 1 single byte, 0×06 indicates null.
    UNDEFINED   = 0x06
    #: When an ActionScript object refers to itself, such this.self = this, or
    #: when objects are repeated within the same scope (for example, as the two
    #: parameters of the same function called), a code of 0×07 and an int, the
    #: reference number, are written.
    REFERENCE   = 0x07
    #: A MixedArray is indicated by code 0×08, then a Long representing the highest
    #: numeric index in the array, or 0 if there are none or they are all negative.
    #: After that follow the elements in key : value pairs. 
    MIXEDARRAY  = 0x08
    #: @see: L{OBJECT}
    OBJECTTERM  = 0x09
    #: An array is indicated by 0x0A, then a Long for array length, then the array
    #: elements themselves. Arrays are always sparse; values for inexistant keys are
    #: set to null (0×06) to maintain sparsity.
    ARRAY       = 0x0a
    #: Date is represented as 0x0B, then a double, then an int. The double represents
    #: the number of milliseconds since 01/01/1970. The int represents the timezone
    #: offset in minutes between GMT. Note for the latter than values greater than 720
    #: (12 hours) are represented as 2^16 - the value. Thus GMT+1 is 60 while GMT-5 is 65236.
    DATE        = 0x0b
    #: LongString is reserved for strings larger then 2^16 characters long. It is represented
    #: as 0x0C then a LongUTF.
    LONGSTRING  = 0x0c
    #: Trying to send values which don’t make sense, such as prototypes, functions,
    #: built-in objects, etc. will be indicated by a single 0x0D byte.
    UNSUPPORTED = 0x0d
    #: Remoting Server -> Client only
    #: @see: U{Remoting record structure on OSFlash (external)
    #: <http://osflash.org/documentation/amf/recordset>}
    RECORDSET   = 0x0e
    #: The XML element is indicated by 0x0F and followed by a LongUTF containing the string
    #: representation of the XML object. The receiving gateway may which to wrap this string
    #: inside a language-specific standard XML object, or simply pass as a string.
    XML         = 0x0f
    #: A typed object is indicated by 0×10, then a UTF string indicating class name, and then
    #: the same structure as a normal 0×03 Object. The receiving gateway may use a mapping
    #: scheme, or send back as a vanilla object or associative array.
    TYPEDOBJECT = 0x10
    #: An AMF message sent from an AS3 client such as the Flash Player 9 may break out
    #: into L{AMF3<pyamf.amf3>} mode. In this case the next byte will be the AMF3 type code
    #: and the data will be in AMF3 format until the decoded object reaches it’s logical
    #: conclusion (for example, an object has no more keys).
    AMF3        = 0x11

#: List of available ActionScript types in AMF0.
ACTIONSCRIPT_TYPES = set(
    ASTypes.__dict__[x] for x in ASTypes.__dict__ if not x.startswith('__'))

class Decoder(object):
    """
    Decodes an AMF0 stream.
    """
    #: Decoder type mappings.
    # XXX nick: Do we need to support ASTypes.MOVIECLIP here?
    type_map = {
        ASTypes.NUMBER:     'readNumber',
        ASTypes.BOOL:       'readBoolean',
        ASTypes.STRING:     'readString',
        ASTypes.OBJECT:     'readObject',
        ASTypes.NULL:       'readNull',
        # TODO: do we need a special value here?
        ASTypes.UNDEFINED:  'readNull',
        ASTypes.REFERENCE:  'readReference',
        ASTypes.MIXEDARRAY: 'readMixedArray',
        ASTypes.ARRAY:      'readList',
        ASTypes.DATE:       'readDate',
        ASTypes.LONGSTRING: 'readLongString',
        # TODO: do we need a special value here?
        ASTypes.UNSUPPORTED:'readNull',
        ASTypes.XML:        'readXML',
        ASTypes.TYPEDOBJECT:'readTypedObject',
        ASTypes.AMF3:       'readAMF3'
    }

    def __init__(self, data=None, context=None):
        """
        @type   data: L{BufferedByteStream}
        @param  data: AMF0 data
        @type   context: L{Context}
        @param  context: Context
        """
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

        @return: AMF0 type
        @raise DecodeError: AMF0 type not recognized
        """
        type = self.input.read_uchar()

        if type not in ACTIONSCRIPT_TYPES:
            raise pyamf.DecodeError("Unknown AMF0 type 0x%02x at %d" % (
                type, self.input.tell() - 1))

        return type

    def readNumber(self):
        """
        Reads a Number.

        In ActionScript 1 and 2 the NumberASTypes type represents all numbers,
        both floats and integers.

        @return: number
        """
        return self.input.read_double()

    def readBoolean(self):
        """
        Reads a bool.

        @return: boolean
        @rtype: bool
        """
        return bool(self.input.read_uchar())

    def readNull(self):
        """
        Reads null.

        @return: None
        @rtype: None
        """
        return None

    def readMixedArray(self):
        """
        Read mixed array.
        
        @return: array
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
        """
        Read a list from the data stream.
        """
        obj = []
        len = self.input.read_ulong()

        for i in xrange(len):
            obj.append(self.readElement())

        self.context.addObject(obj)

        return obj

    def readTypedObject(self):
        """
        Reads an object from the stream and attempts to 'cast' it.

        @see: L{load_class<pyamf.load_class>} for more info.
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
        """
        Read AMF3 elements from the data stream.
        """
        # XXX: Does the amf3 decoder have access to the same references as amf0?
        context = pyamf.Context()
        decoder = pyamf._get_decoder(pyamf.AMF3)(self.input, context)

        element = decoder.readElement()
        self.context.amf3_objs.append(element)

        return element

    def readElement(self):
        """
        Reads an AMF0 element from the data stream.
        
        @raise DecodeError: the ActionScript type is unknown.
        """
        type = self.readType()

        try:
            func = getattr(self, self.type_map[type])
        except KeyError, e:
            raise pyamf.DecodeError(
                "Unknown ActionScript type 0x%02x" % type)

        return func()

    def readString(self):
        """
        Reads a string from the data stream.
        """
        len = self.input.read_ushort()
        return self.input.read_utf8_string(len)

    def _readObject(self, obj):
        """
        @type   obj:
        @param  obj:
        """
        key = self.readString()

        while self.input.peek() != chr(ASTypes.OBJECTTERM):
            obj[key] = self.readElement()
            key = self.readString()

        # discard the end marker (ASTypes.OBJECTTERM)
        self.input.read(len(chr(ASTypes.OBJECTTERM)))

    def readObject(self):
        """
        Reads an object from the data stream.

        @return: The object
        @rtype: __builtin__.object
        """
        obj = pyamf.Bag()

        self._readObject(obj)
        self.context.addObject(obj)

        return obj

    def readReference(self):
        """
        Reads a reference from the data stream.
        """
        idx = self.input.read_ushort()
        return self.context.getObject(idx)

    def readDate(self):
        """
        Reads a UTC date from the data stream.

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
        """
        Read utf8 string.
        """
        len = self.input.read_ulong()
        
        return self.input.read_utf8_string(len)

    def readXML(self):
        """
        Read XML.
        """
        data = self.readLongString()
        
        return util.ET.fromstring(data)

class Encoder(object):
    """
    Encodes an AMF0 stream.
    
    The type map is a list of types -> functions. The types is a list of
    possible instances or functions to call (that return a bool) to determine
    the correct function to call to encode the data.
    """
    #: Python to AMF type mappings.
    type_map = [
        # Unsupported types go first
        ((types.BuiltinFunctionType, types.BuiltinMethodType,), "writeUnsupported"),
        ((bool,), "writeBoolean"),
        ((int,long,float), "writeNumber"),
        ((types.StringTypes,), "writeString"),
        ((util.ET.iselement,), "writeXML"),
        ((pyamf.Bag,), "writeObject"),
        ((types.DictType,), "writeMixedArray"),
        ((types.ListType,types.TupleType,), "writeArray"),
        ((datetime.date, datetime.datetime), "writeDate"),
        ((types.NoneType,), "writeNull"),
        ((types.InstanceType,types.ObjectType,), "writeObject"),
    ]

    def __init__(self, output, context=None):
        """
        Constructs a new Encoder.

        Output should be a writable file-like object.

        @type   output: StringIO
        @param  output: File-like object.
        @type   context: L{Context}
        @param  context: Context
        """
        self.output = output

        if context == None:
            self.context = pyamf.Context()
        else:
            self.context = context

    def writeType(self, type):
        """
        Writes the type to the stream.

        @type   type: Integer
        @param  type: ActionScript type.
        @raise EncodeError: AMF0 type is not recognized.
        """
        if type not in ACTIONSCRIPT_TYPES:
            raise pyamf.EncodeError("Unknown AMF0 type 0x%02x at %d" % (
                type, self.output.tell() - 1))

        self.output.write_uchar(type)

    def writeUnsupported(self, data):
        """
        Writes unsupported data type to the stream.

        @type   data: 
        @param  data:
        """
        self.writeType(ASTypes.UNSUPPORTED)

    def _writeElementFunc(self, data):
        """
        Gets a function based on the type of data.
        
        @rtype: callable or None
        @return: The function used to encode data to the stream.
        """
        # There is a very specific use case that we must check for.
        # In the context there is an array of amf3_objs that contain references
        # to objects that are to be encoded in amf3
        if data in self.context.amf3_objs:
            return self.writeAMF3

        func = None
        td = type(data)

        for tlist, method in self.type_map:
            for t in tlist:
                try:
                    if isinstance(data, t):
                        return getattr(self, method)
                except TypeError:
                    if callable(t) and t(data):
                        return getattr(self, method)

        return None

    def writeElement(self, data):
        """
        Writes an encoded version of data to the output stream.

        @type   data: mixed
        @param  data: 
        """
        func = self._writeElementFunc(data)

        if func is not None:
            func(data)
        else:
            # XXX nick: Should we be generating a warning here?
            self.writeUnsupported(data)

    def writeNull(self, n):
        """
        Write null type to data stream.

        @type   n: None
        @param  n: Is ignored
        """
        self.writeType(ASTypes.NULL)

    def writeArray(self, a):
        """
        Write array to the stream.

        @type   a: L{BufferedByteStream}
        @param  a: AMF data.
        """
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
        """
        Write number to data stream.

        @type   n: L{BufferedByteStream}
        @param  n: AMF data.
        """
        self.writeType(ASTypes.NUMBER)
        self.output.write_double(float(n))

    def writeBoolean(self, b):
        """
        Write boolean to data stream.

        @type   b: L{BufferedByteStream}
        @param  b: AMF data.
        """
        self.writeType(ASTypes.BOOL)

        if b:
            self.output.write_uchar(1)
        else:
            self.output.write_uchar(0)

    def writeString(self, s, writeType=True):
        """
        Write string to data stream.

        @type   s: L{BufferedByteStream}
        @param  s: AMF data.
        @type   writeType: bool
        @param  writeType: Write data type.
        """
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
        """
        Write reference to data stream.

        @type   o: L{BufferedByteStream}
        @param  o: AMF data.
        """
        idx = self.context.getObjectReference(o)

        self.writeType(ASTypes.REFERENCE)
        self.output.write_ushort(idx)

    def _writeDict(self, o):
        """
        Write dict to data stream.

        @type   o: iterable
        @param  o: AMF data.
        """
        for key, val in o.iteritems():
            self.writeString(key, False)
            self.writeElement(val)

    def writeMixedArray(self, o):
        """
        Write mixed array to data stream.

        @type   o: L{BufferedByteStream}
        @param  o: AMF data.
        """
        try:
            self.writeReference(o)
            return
        except pyamf.ReferenceError:
            pass

        self.writeType(ASTypes.MIXEDARRAY)

        # TODO: optimise this
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
        """
        Write end of object in the data stream.
        """
        # Write a null string, this is an optimisation so that we don't have to
        # wasting precious cycles by encoding the string etc. 
        self.output.write('\x00\x00')
        self.writeType(ASTypes.OBJECTTERM)

    def writeObject(self, o):
        """
        Write object to the stream.

        @type   o: L{BufferedByteStream}
        @param  o: AMF data.
        """
        try:
            self.writeReference(o)
            return
        except pyamf.ReferenceError:
            pass

        # Need to check here if this object has a registered alias
        try:
            alias = pyamf.get_class_alias(o)
            self.writeType(ASTypes.TYPEDOBJECT)
            self.writeString(alias.alias, False)
        except pyamf.UnknownClassAlias:
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

        @type   d: Instance of datetime.datetime
        @param  d: The date to be written.
        """
        # According to the Red 5 implementation of AMF0, dates references are
        # created, but not used
        secs = util.get_timestamp(d)
        tz = 0

        self.writeType(ASTypes.DATE)
        self.output.write_double(secs * 1000.0)
        self.output.write_short(tz)

    def writeXML(self, e):
        """
        Write XML to data stream.

        @type   e: L{BufferedByteStream}
        @param  e: AMF data.
        """
        data = util.ET.tostring(e, 'utf8')

        self.writeType(ASTypes.XML)
        self.output.write_ulong(len(data))
        self.output.write(data)

    def writeAMF3(self, data):
        """
        Writes an element to the datastream in AMF3 format.
        
        @type data: mixed
        @param data: The data to be encoded.
        """
        context = pyamf.Context()
        encoder = pyamf._get_encoder(pyamf.AMF3)(self.output, context)

        self.writeType(ASTypes.AMF3)
        encoder.writeElement(data)

def decode(stream, context=None):
    """
    A helper function to decode an AMF0 datastream.

    @type   stream: L{BufferedByteStream}
    @param  stream: AMF0 datastream.
    @type   context: L{Context}
    @param  context: Context.
    """
    decoder = Decoder(stream, context)

    for el in decoder.readElement():
        yield el

def encode(element, context=None):
    """
    A helper function to encode an element into the AMF0 format.

    @type   element: 
    @param  element:
    @type   context: L{Context}
    @param  context: Context.
    @return: File object.
    @returntype: StringIO
    """
    buf = util.BufferedByteStream()
    encoder = Encoder(buf, context)

    encoder.writeElement(element)

    return buf
