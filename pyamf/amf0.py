# -*- coding: utf-8 -*-
#
# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
AMF0 implementation.

C{AMF0} supports the basic data types used for the NetConnection, NetStream,
LocalConnection, SharedObjects and other classes in the Adobe Flash Player.

@since: 0.1
@see: U{Official AMF0 Specification in English (external)
    <http://opensource.adobe.com/wiki/download/attachments/1114283/amf0_spec_121207.pdf>}
@see: U{Official AMF0 Specification in Japanese (external)
    <http://opensource.adobe.com/wiki/download/attachments/1114283/JP_amf0_spec_121207.pdf>}
@see: U{AMF documentation on OSFlash (external)
    <http://osflash.org/documentation/amf>}
"""

import datetime

import pyamf
from pyamf import util, codec, python


#: Represented as 9 bytes: 1 byte for C{0×00} and 8 bytes a double
#: representing the value of the number.
TYPE_NUMBER      = '\x00'
#: Represented as 2 bytes: 1 byte for C{0×01} and a second, C{0×00}
#: for C{False}, C{0×01} for C{True}.
TYPE_BOOL        = '\x01'
#: Represented as 3 bytes + len(String): 1 byte C{0×02}, then a UTF8 string,
#: including the top two bytes representing string length as a C{int}.
TYPE_STRING      = '\x02'
#: Represented as 1 byte, C{0×03}, then pairs of UTF8 string, the key, and
#: an AMF element, ended by three bytes, C{0×00} C{0×00} C{0×09}.
TYPE_OBJECT      = '\x03'
#: MovieClip does not seem to be supported by Remoting.
#: It may be used by other AMF clients such as SharedObjects.
TYPE_MOVIECLIP   = '\x04'
#: 1 single byte, C{0×05} indicates null.
TYPE_NULL        = '\x05'
#: 1 single byte, C{0×06} indicates null.
TYPE_UNDEFINED   = '\x06'
#: When an ActionScript object refers to itself, such C{this.self = this},
#: or when objects are repeated within the same scope (for example, as the
#: two parameters of the same function called), a code of C{0×07} and an
#: C{int}, the reference number, are written.
TYPE_REFERENCE   = '\x07'
#: A MixedArray is indicated by code C{0×08}, then a Long representing the
#: highest numeric index in the array, or 0 if there are none or they are
#: all negative. After that follow the elements in key : value pairs.
TYPE_MIXEDARRAY  = '\x08'
#: @see: L{TYPE_OBJECT}
TYPE_OBJECTTERM  = '\x09'
#: An array is indicated by C{0x0A}, then a Long for array length, then the
#: array elements themselves. Arrays are always sparse; values for
#: inexistant keys are set to null (C{0×06}) to maintain sparsity.
TYPE_ARRAY       = '\x0A'
#: Date is represented as C{0x0B}, then a double, then an C{int}. The double
#: represents the number of milliseconds since 01/01/1970. The C{int} represents
#: the timezone offset in minutes between GMT. Note for the latter than values
#: greater than 720 (12 hours) are represented as M{2^16} - the value. Thus GMT+1
#: is 60 while GMT-5 is 65236.
TYPE_DATE        = '\x0B'
#: LongString is reserved for strings larger then M{2^16} characters long. It
#: is represented as C{0x0C} then a LongUTF.
TYPE_LONGSTRING  = '\x0C'
#: Trying to send values which don’t make sense, such as prototypes, functions,
#: built-in objects, etc. will be indicated by a single C{00x0D} byte.
TYPE_UNSUPPORTED = '\x0D'
#: Remoting Server -> Client only.
#: @see: L{RecordSet}
#: @see: U{RecordSet structure on OSFlash (external)
#: <http://osflash.org/documentation/amf/recordset>}
TYPE_RECORDSET   = '\x0E'
#: The XML element is indicated by C{0x0F} and followed by a LongUTF containing
#: the string representation of the XML object. The receiving gateway may which
#: to wrap this string inside a language-specific standard XML object, or simply
#: pass as a string.
TYPE_XML         = '\x0F'
#: A typed object is indicated by C{0×10}, then a UTF string indicating class
#: name, and then the same structure as a normal C{0×03} Object. The receiving
#: gateway may use a mapping scheme, or send back as a vanilla object or
#: associative array.
TYPE_TYPEDOBJECT = '\x10'
#: An AMF message sent from an AVM+ client such as the Flash Player 9 may break
#: out into L{AMF3<pyamf.amf3>} mode. In this case the next byte will be the
#: AMF3 type code and the data will be in AMF3 format until the decoded object
#: reaches it’s logical conclusion (for example, an object has no more keys).
TYPE_AMF3        = '\x11'


class Context(codec.Context):
    """
    I hold the AMF0 context for en/decoding streams.

    AMF0 object references start at index 1.
    """

    def clear(self):
        """
        Clears the context.
        """
        codec.Context.clear(self)

        self.amf3_objs = []

    def hasAMF3ObjectReference(self, obj):
        """
        Gets a reference for an object.
        """
        return obj in self.amf3_objs

    def addAMF3Object(self, obj):
        """
        Adds an AMF3 reference to C{obj}.

        @param obj: The object to add to the context.
        @rtype: C{int}
        @return: Reference to C{obj}.
        """
        return self.amf3_objs.append(obj)


class Decoder(codec.Decoder):
    """
    Decodes an AMF0 stream.
    """

    # XXX nick: Do we need to support TYPE_MOVIECLIP here?
    type_map = {
        TYPE_NUMBER:     'readNumber',
        TYPE_BOOL:       'readBoolean',
        TYPE_STRING:     'readUnicode',
        TYPE_OBJECT:     'readObject',
        TYPE_NULL:       'readNull',
        TYPE_UNDEFINED:  'readUndefined',
        TYPE_REFERENCE:  'readReference',
        TYPE_MIXEDARRAY: 'readMixedArray',
        TYPE_ARRAY:      'readList',
        TYPE_DATE:       'readDate',
        TYPE_LONGSTRING: 'readLongString',
        # TODO: do we need a special value here?
        TYPE_UNSUPPORTED:'readNull',
        TYPE_XML:        'readXML',
        TYPE_TYPEDOBJECT:'readTypedObject',
        TYPE_AMF3:       'readAMF3'
    }

    def buildContext(self):
        return Context()

    def readNumber(self):
        """
        Reads a ActionScript C{Number} value.

        In ActionScript 1 and 2 the C{NumberASTypes} type represents all numbers,
        both floats and integers.

        @rtype: C{int} or C{float}
        """
        return python.check_for_int(self.stream.read_double())

    def readBoolean(self):
        """
        Reads a ActionScript C{Boolean} value.

        @rtype: C{bool}
        @return: Boolean.
        """
        return bool(self.stream.read_uchar())

    def readNull(self):
        """
        Reads a ActionScript C{null} value.

        @return: C{None}
        @rtype: C{None}
        """
        return None

    def readUndefined(self):
        """
        Reads an ActionScript C{undefined} value.

        @return: L{Undefined<pyamf.Undefined>}
        """
        return pyamf.Undefined

    def readMixedArray(self):
        """
        Read mixed array.

        @rtype: C{dict}
        @return: C{dict} read from the stream
        """
        self.stream.read_ulong() # length
        obj = pyamf.MixedArray()
        self.context.addObject(obj)
        self._readObject(obj)
        ikeys = []

        for key in obj.keys():
            try:
                ikey = int(key)
                ikeys.append((key, ikey))
                obj[ikey] = obj[key]
                del obj[key]
            except ValueError:
                # XXX: do we want to ignore this?
                pass

        ikeys.sort()

        return obj

    def readList(self):
        """
        Read a C{list} from the data stream.

        @rtype: C{list}
        @return: C{list}
        """
        obj = []
        self.context.addObject(obj)
        len = self.stream.read_ulong()

        for i in xrange(len):
            obj.append(self.readElement())

        return obj

    def readTypedObject(self):
        """
        Reads an ActionScript object from the stream and attempts to
        'cast' it.

        @see: L{load_class<pyamf.load_class>}
        """
        classname = self.readString()
        alias = None

        try:
            alias = pyamf.get_class_alias(classname)

            ret = alias.createInstance(codec=self)
        except pyamf.UnknownClassAlias:
            if self.strict:
                raise

            ret = pyamf.TypedObject(classname)

        self.context.addObject(ret)
        self._readObject(ret, alias)

        return ret

    def _getAMF3Decoder(self):
        decoder = getattr(self, 'amf3_decoder', None)

        if not decoder:
            decoder = pyamf.get_decoder(pyamf.AMF3, stream=self.stream)

        return decoder

    def readAMF3(self):
        """
        Read AMF3 elements from the data stream.

        @rtype: C{mixed}
        @return: The AMF3 element read from the stream
        """
        decoder = self._getAMF3Decoder()

        element = decoder.readElement()
        self.context.addAMF3Object(element)

        return element

    def readString(self):
        """
        Reads a C{string} from the stream.
        """
        l = self.stream.read_ushort()

        return self.stream.read(l)

    def readUnicode(self):
        """
        Reads a C{unicode} from the data stream.
        """
        l = self.stream.read_ushort()

        bytes = self.stream.read(l)

        return self.context.getStringForBytes(bytes)

    def _readObject(self, obj, alias=None):
        obj_attrs = dict()

        key = self.readString()

        while self.stream.peek() != TYPE_OBJECTTERM:
            obj_attrs[key] = self.readElement()
            key = self.readString()

        # discard the end marker (TYPE_OBJECTTERM)
        self.stream.read(1)

        if alias:
            alias.applyAttributes(obj, obj_attrs, codec=self)
        else:
            util.set_attrs(obj, obj_attrs)

    def readObject(self):
        """
        Reads an object from the data stream.

        @rtype: L{ASObject<pyamf.ASObject>}
        """
        obj = pyamf.ASObject()
        self.context.addObject(obj)

        self._readObject(obj)

        return obj

    def readReference(self):
        """
        Reads a reference from the data stream.

        @raise pyamf.ReferenceError: Unknown reference.
        """
        idx = self.stream.read_ushort()

        o = self.context.getObject(idx)

        if o is None:
            raise pyamf.ReferenceError('Unknown reference %d' % (idx,))

        return o

    def readDate(self):
        """
        Reads a UTC date from the data stream. Client and servers are
        responsible for applying their own timezones.

        Date: C{0x0B T7 T6} .. C{T0 Z1 Z2 T7} to C{T0} form a 64 bit
        Big Endian number that specifies the number of nanoseconds
        that have passed since 1/1/1970 0:00 to the specified time.
        This format is UTC 1970. C{Z1} and C{Z0} for a 16 bit Big
        Endian number indicating the indicated time's timezone in
        minutes.
        """
        ms = self.stream.read_double() / 1000.0
        self.stream.read_short() # tz

        # Timezones are ignored
        d = util.get_datetime(ms)

        if self.timezone_offset:
            d = d + self.timezone_offset

        self.context.addObject(d)

        return d

    def readLongString(self):
        """
        Read UTF8 string.
        """
        l = self.stream.read_ulong()

        bytes = self.stream.read(l)

        return self.context.getStringForBytes(bytes)

    def readXML(self):
        """
        Read XML.
        """
        data = self.readLongString()
        xml = util.ET.fromstring(data)
        self.context.addObject(xml)

        return xml


class Encoder(codec.Encoder):
    """
    Encodes an AMF0 stream.

    @ivar use_amf3: A flag to determine whether this encoder knows about AMF3.
    @type use_amf3: C{bool}
    """

    context_class = Context

    def __init__(self, *args, **kwargs):
        self.use_amf3 = kwargs.pop('use_amf3', False)

        codec.Encoder.__init__(self, *args, **kwargs)

    def buildContext(self):
        return Context()

    def getCustomTypeFunc(self, data):
        t = type(data)

        if t is pyamf.MixedArray:
            return self.writeMixedArray

        # There is a very specific use case that we must check for.
        # In the context there is an array of amf3_objs that contain
        # references to objects that are to be encoded in amf3.

        if self.use_amf3 and self.context.hasAMF3ObjectReference(data):
            return self.writeAMF3

        return codec.Encoder.getCustomTypeFunc(self, data)

    def writeType(self, t):
        """
        Writes the type to the stream.

        @type   t: C{str}
        @param  t: ActionScript type.

        @raise pyamf.EncodeError: AMF0 type is not recognized.
        """
        self.stream.write(t)

    def writeUndefined(self, data):
        """
        Writes the L{undefined<TYPE_UNDEFINED>} data type to the stream.

        @param data: The C{undefined} data to be encoded to the AMF0 data
            stream.
        @type data: C{undefined} data
        """
        self.writeType(TYPE_UNDEFINED)

    def writeUnsupported(self, data):
        """
        Writes L{unsupported<TYPE_UNSUPPORTED>} data type to the
        stream.

        @param data: The C{unsupported} data to be encoded to the AMF0
            data stream.
        @type data: C{unsupported} data
        """
        self.writeType(TYPE_UNSUPPORTED)

    def writeNull(self, n):
        """
        Write null type to data stream.

        @type   n: C{None}
        @param  n: Is ignored.
        """
        self.writeType(TYPE_NULL)

    def writeList(self, a):
        """
        Write array to the stream.

        @type a: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
        @param a: The array data to be encoded to the AMF0 data stream.
        """
        alias = self.context.getClassAlias(a.__class__)

        if alias.external:
            # a is a subclassed list with a registered alias - push to the
            # correct method
            self.writeObject(a)

            return

        if self.writeReference(a) != -1:
            return

        self.context.addObject(a)

        self.writeType(TYPE_ARRAY)
        self.stream.write_ulong(len(a))

        for data in a:
            self.writeElement(data)

    def writeNumber(self, n):
        """
        Write number to the data stream.

        @type   n: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
        @param  n: The number data to be encoded to the AMF0 data stream.
        """
        self.writeType(TYPE_NUMBER)
        self.stream.write_double(float(n))

    def writeBoolean(self, b):
        """
        Write boolean to the data stream.

        @type b: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
        @param b: The boolean data to be encoded to the AMF0 data stream.
        """
        self.writeType(TYPE_BOOL)

        if b:
            self.stream.write_uchar(1)
        else:
            self.stream.write_uchar(0)

    def writeString(self, s, writeType=True):
        """
        Write string to the data stream.

        @type s: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
        @param s: The string data to be encoded to the AMF0 data stream.
        @type writeType: C{bool}
        @param writeType: Write data type.
        """
        l = len(s)

        if writeType:
            if l > 0xffff:
                self.writeType(TYPE_LONGSTRING)
            else:
                self.writeType(TYPE_STRING)

        if l > 0xffff:
            self.stream.write_ulong(l)
        else:
            self.stream.write_ushort(l)

        self.stream.write(s)

    def writeLabel(self, s):
        self.writeString(s, False)

    def writeUnicode(self, u, writeType=True):
        """
        Write a unicode to the data stream.
        """
        s = self.context.getBytesForString(u)

        self.writeString(s, writeType)

    def writeReference(self, o):
        """
        Write reference to the data stream.

        @type o: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
        @param o: The reference data to be encoded to the AMF0 data
            stream.
        """
        idx = self.context.getObjectReference(o)

        if idx == -1 or idx > 65535:
            return -1

        self.writeType(TYPE_REFERENCE)

        self.stream.write_ushort(idx)

        return idx

    def _writeDict(self, o):
        """
        Write C{dict} to the data stream.

        @type o: C{iterable}
        @param o: The C{dict} data to be encoded to the AMF0 data
            stream.
        """
        for key, val in o.iteritems():
            self.writeString(key, False)
            self.writeElement(val)

    def writeMixedArray(self, o):
        """
        Write mixed array to the data stream.

        @type o: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
        @param o: The mixed array data to be encoded to the AMF0
            data stream.
        """
        if self.writeReference(o) != -1:
            return

        self.context.addObject(o)
        self.writeType(TYPE_MIXEDARRAY)

        # TODO: optimise this
        # work out the highest integer index
        try:
            # list comprehensions to save the day
            max_index = max([y[0] for y in o.items()
                if isinstance(y[0], (int, long))])

            if max_index < 0:
                max_index = 0
        except ValueError:
            max_index = 0

        self.stream.write_ulong(max_index)

        self._writeDict(o)
        self._writeEndObject()

    def _writeEndObject(self):
        self.stream.write('\x00\x00')
        self.writeType(TYPE_OBJECTTERM)

    def writeObject(self, o):
        """
        Write object to the stream.

        @type o: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
        @param o: The object data to be encoded to the AMF0 data stream.
        """
        if self.use_amf3:
            self.writeAMF3(o)

            return

        if self.writeReference(o) != -1:
            return

        self.context.addObject(o)
        alias = self.context.getClassAlias(o.__class__)

        alias.compile()

        if alias.amf3:
            self.writeAMF3(o)

            return

        if alias.anonymous:
            self.writeType(TYPE_OBJECT)
        else:
            self.writeType(TYPE_TYPEDOBJECT)
            self.writeString(alias.alias, False)

        attrs = alias.getEncodableAttributes(o, codec=self)

        if alias.static_attrs and attrs:
            for key in alias.static_attrs:
                value = attrs.pop(key)

                self.writeString(key, False)
                self.writeElement(value)

        if attrs:
            for key, value in attrs.iteritems():
                self.writeString(key, False)
                self.writeElement(value)

        self._writeEndObject()

    def writeDate(self, d):
        """
        Writes a date to the data stream.

        @type d: Instance of C{datetime.datetime}
        @param d: The date to be encoded to the AMF0 data stream.
        """
        if isinstance(d, datetime.time):
            raise pyamf.EncodeError('A datetime.time instance was found but '
                'AMF0 has no way to encode time objects. Please use '
                'datetime.datetime instead (got:%r)' % (d,))

        # According to the Red5 implementation of AMF0, dates references are
        # created, but not used.
        if self.timezone_offset is not None:
            d -= self.timezone_offset

        secs = util.get_timestamp(d)
        tz = 0

        self.writeType(TYPE_DATE)
        self.stream.write_double(secs * 1000.0)
        self.stream.write_short(tz)

    def writeXML(self, e):
        """
        Write XML to the data stream.

        @type e: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
        @param e: The XML data to be encoded to the AMF0 data stream.
        """
        if self.use_amf3 is True:
            self.writeAMF3(e)

            return

        self.writeType(TYPE_XML)

        data = util.ET.tostring(e, 'utf-8')
        self.stream.write_ulong(len(data))
        self.stream.write(data)

    def _getAMF3Encoder(self):
        encoder = getattr(self, 'amf3_encoder', None)

        if not encoder:
            encoder = pyamf.get_encoder(pyamf.AMF3, stream=self.stream)

        return encoder

    def writeAMF3(self, data):
        """
        Writes an element to the datastream in L{AMF3<pyamf.amf3>} format.

        @type data: C{mixed}
        @param data: The data to be encoded to the AMF0 data stream.
        """
        encoder = self._getAMF3Encoder()

        self.context.addAMF3Object(data)

        self.writeType(TYPE_AMF3)
        encoder.writeElement(data)


class RecordSet(object):
    """
    I represent the C{RecordSet} class used in Adobe Flash Remoting to hold
    (amongst other things) SQL records.

    @ivar columns: The columns to send.
    @type columns: List of strings.
    @ivar items: The C{RecordSet} data.
    @type items: List of lists, the order of the data corresponds to the order
        of the columns.
    @ivar service: Service linked to the C{RecordSet}.
    @type service:
    @ivar id: The id of the C{RecordSet}.
    @type id: C{str}

    @see: U{RecordSet on OSFlash (external)
    <http://osflash.org/documentation/amf/recordset>}
    """

    class __amf__:
        alias = 'RecordSet'
        static = ('serverInfo',)
        dynamic = False

    def __init__(self, columns=[], items=[], service=None, id=None):
        self.columns = columns
        self.items = items
        self.service = service
        self.id = id

    def _get_server_info(self):
        ret = pyamf.ASObject(totalCount=len(self.items), cursor=1, version=1,
            initialData=self.items, columnNames=self.columns)

        if self.service is not None:
            ret.update({'serviceName': str(self.service['name'])})

        if self.id is not None:
            ret.update({'id':str(self.id)})

        return ret

    def _set_server_info(self, val):
        self.columns = val['columnNames']
        self.items = val['initialData']

        try:
            # TODO nick: find relevant service and link in here.
            self.service = dict(name=val['serviceName'])
        except KeyError:
            self.service = None

        try:
            self.id = val['id']
        except KeyError:
            self.id = None

    serverInfo = property(_get_server_info, _set_server_info)

    def __repr__(self):
        ret = '<%s.%s object' % (self.__module__, self.__class__.__name__)

        if self.id is not None:
            ret += ' id=%s' % self.id

        if self.service is not None:
            ret += ' service=%s' % self.service

        ret += ' at 0x%x>' % id(self)

        return ret

pyamf.register_class(RecordSet)

