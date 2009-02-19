# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE for details.

"""
AMF0 implementation.

C{AMF0} supports the basic data types used for the NetConnection, NetStream,
LocalConnection, SharedObjects and other classes in the Flash Player.

@see: U{Official AMF0 Specification in English (external)
<http://opensource.adobe.com/wiki/download/attachments/1114283/amf0_spec_121207.pdf>}
@see: U{Official AMF0 Specification in Japanese (external)
<http://opensource.adobe.com/wiki/download/attachments/1114283/JP_amf0_spec_121207.pdf>}
@see: U{AMF documentation on OSFlash (external)
<http://osflash.org/documentation/amf>}

@since: 0.1.0
"""

import datetime, types
import copy

import pyamf
from pyamf import util

class ASTypes:
    """
    The AMF/RTMP data encoding format constants.

    @see: U{Data types on OSFlash (external)
    <http://osflash.org/documentation/amf/astypes>}
    """
    #: Represented as 9 bytes: 1 byte for C{0×00} and 8 bytes a double
    #: representing the value of the number.
    NUMBER      = 0x00
    #: Represented as 2 bytes: 1 byte for C{0×01} and a second, C{0×00}
    #: for C{False}, C{0×01} for C{True}.
    BOOL        = 0x01
    #: Represented as 3 bytes + len(String): 1 byte C{0×02}, then a UTF8 string,
    #: including the top two bytes representing string length as a C{int}.
    STRING      = 0x02
    #: Represented as 1 byte, C{0×03}, then pairs of UTF8 string, the key, and
    #: an AMF element, ended by three bytes, C{0×00} C{0×00} C{0×09}.
    OBJECT      = 0x03
    #: MovieClip does not seem to be supported by Remoting.
    #: It may be used by other AMF clients such as SharedObjects.
    MOVIECLIP   = 0x04
    #: 1 single byte, C{0×05} indicates null.
    NULL        = 0x05
    #: 1 single byte, C{0×06} indicates null.
    UNDEFINED   = 0x06
    #: When an ActionScript object refers to itself, such C{this.self = this},
    #: or when objects are repeated within the same scope (for example, as the
    #: two parameters of the same function called), a code of C{0×07} and an
    #: C{int}, the reference number, are written.
    REFERENCE   = 0x07
    #: A MixedArray is indicated by code C{0×08}, then a Long representing the
    #: highest numeric index in the array, or 0 if there are none or they are
    #: all negative. After that follow the elements in key : value pairs.
    MIXEDARRAY  = 0x08
    #: @see: L{OBJECT}
    OBJECTTERM  = 0x09
    #: An array is indicated by C{0x0A}, then a Long for array length, then the
    #: array elements themselves. Arrays are always sparse; values for
    #: inexistant keys are set to null (C{0×06}) to maintain sparsity.
    ARRAY       = 0x0a
    #: Date is represented as C{00x0B}, then a double, then an C{int}. The double
    #: represents the number of milliseconds since 01/01/1970. The C{int} represents
    #: the timezone offset in minutes between GMT. Note for the latter than values
    #: greater than 720 (12 hours) are represented as M{2^16} - the value. Thus GMT+1
    #: is 60 while GMT-5 is 65236.
    DATE        = 0x0b
    #: LongString is reserved for strings larger then M{2^16} characters long. It
    #: is represented as C{00x0C} then a LongUTF.
    LONGSTRING  = 0x0c
    #: Trying to send values which don’t make sense, such as prototypes, functions,
    #: built-in objects, etc. will be indicated by a single C{00x0D} byte.
    UNSUPPORTED = 0x0d
    #: Remoting Server -> Client only.
    #: @see: L{RecordSet}
    #: @see: U{RecordSet structure on OSFlash (external)
    #: <http://osflash.org/documentation/amf/recordset>}
    RECORDSET   = 0x0e
    #: The XML element is indicated by C{00x0F} and followed by a LongUTF containing
    #: the string representation of the XML object. The receiving gateway may which
    #: to wrap this string inside a language-specific standard XML object, or simply
    #: pass as a string.
    XML         = 0x0f
    #: A typed object is indicated by C{0×10}, then a UTF string indicating class
    #: name, and then the same structure as a normal C{0×03} Object. The receiving
    #: gateway may use a mapping scheme, or send back as a vanilla object or
    #: associative array.
    TYPEDOBJECT = 0x10
    #: An AMF message sent from an AVM+ client such as the Flash Player 9 may break
    #: out into L{AMF3<pyamf.amf3>} mode. In this case the next byte will be the
    #: AMF3 type code and the data will be in AMF3 format until the decoded object
    #: reaches it’s logical conclusion (for example, an object has no more keys).
    AMF3        = 0x11

#: List of available ActionScript types in AMF0.
ACTIONSCRIPT_TYPES = []

for x in ASTypes.__dict__:
    if not x.startswith('_'):
        ACTIONSCRIPT_TYPES.append(ASTypes.__dict__[x])
del x

class Context(pyamf.BaseContext):
    """
    I hold the AMF0 context for en/decoding streams.

    AMF0 object references start at index 1.

    @ivar amf3_objs: A list of objects that have been decoded in
        L{AMF3<pyamf.amf3>}.
    @type amf3_objs: L{util.IndexedCollection}
    """
    def __init__(self):
        self.amf3_objs = util.IndexedCollection()

        pyamf.BaseContext.__init__(self)

    def clear(self):
        """
        Clears the context.
        """
        pyamf.BaseContext.clear(self)

        self.amf3_objs.clear()

        if hasattr(self, 'amf3_context'):
            self.amf3_context.clear()

    def reset(self):
        """
        Resets the context.

        @see: L{pyamf.BaseContext.reset}
        """
        pyamf.BaseContext.reset(self)

        if hasattr(self, 'amf3_context'):
            self.amf3_context.reset()

    def getAMF3ObjectReference(self, obj):
        """
        Gets a reference for an object.

        @raise ReferenceError: Object reference could not be found.
        """
        try:
            return self.amf3_objs.getReferenceTo(obj)
        except KeyError:
            raise ReferenceError

    def addAMF3Object(self, obj):
        """
        Adds an AMF3 reference to C{obj}.

        @type obj: C{mixed}
        @param obj: The object to add to the context.
        @rtype: C{int}
        @return: Reference to C{obj}.
        """
        return self.amf3_objs.append(obj)

    def __copy__(self):
        cpy = self.__class__()
        cpy.amf3_objs = copy.copy(self.amf3_objs)

        return cpy

class Decoder(pyamf.BaseDecoder):
    """
    Decodes an AMF0 stream.
    """

    context_class = Context

    # XXX nick: Do we need to support ASTypes.MOVIECLIP here?
    type_map = {
        ASTypes.NUMBER:     'readNumber',
        ASTypes.BOOL:       'readBoolean',
        ASTypes.STRING:     'readString',
        ASTypes.OBJECT:     'readObject',
        ASTypes.NULL:       'readNull',
        ASTypes.UNDEFINED:  'readUndefined',
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

    def readType(self):
        """
        Read and returns the next byte in the stream and determine its type.

        @raise DecodeError: AMF0 type not recognized.
        @return: AMF0 type.
        """
        type = self.stream.read_uchar()

        if type not in ACTIONSCRIPT_TYPES:
            raise pyamf.DecodeError("Unknown AMF0 type 0x%02x at %d" % (
                type, self.stream.tell() - 1))

        return type

    def readNumber(self):
        """
        Reads a ActionScript C{Number} value.

        In ActionScript 1 and 2 the C{NumberASTypes} type represents all numbers,
        both floats and integers.

        @rtype: C{int} or C{float}
        """
        return _check_for_int(self.stream.read_double())

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
        len = self.stream.read_ulong()
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
            alias = pyamf.load_class(classname)

            ret = alias.createInstance(codec=self)
        except pyamf.UnknownClassAlias:
            if self.strict:
                raise

            ret = pyamf.TypedObject(classname)

        self.context.addObject(ret)
        self._readObject(ret, alias)

        return ret

    def readAMF3(self):
        """
        Read AMF3 elements from the data stream.

        @rtype: C{mixed}
        @return: The AMF3 element read from the stream
        """
        if not hasattr(self.context, 'amf3_context'):
            from pyamf import amf3

            self.context.amf3_context = amf3.Context()

        decoder = pyamf._get_decoder_class(pyamf.AMF3)(self.stream, self.context.amf3_context, strict=self.strict)

        element = decoder.readElement()
        self.context.addAMF3Object(element)

        return element

    def readString(self):
        """
        Reads a string from the data stream.

        @rtype: C{str}
        @return: string
        """
        len = self.stream.read_ushort()
        return self.stream.read_utf8_string(len)

    def _readObject(self, obj, alias=None):
        ot = chr(ASTypes.OBJECTTERM)
        obj_attrs = dict()

        key = self.readString().encode('utf8')

        while self.stream.peek() != ot:
            obj_attrs[key] = self.readElement()
            key = self.readString().encode('utf8')

        # discard the end marker (ASTypes.OBJECTTERM)
        self.stream.read(len(ot))

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
        """
        idx = self.stream.read_ushort()

        return self.context.getObject(idx)

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
        tz = self.stream.read_short()

        # Timezones are ignored
        d = util.get_datetime(ms)
        self.context.addObject(d)

        return d

    def readLongString(self):
        """
        Read UTF8 string.
        """
        len = self.stream.read_ulong()

        return self.stream.read_utf8_string(len)

    def readXML(self):
        """
        Read XML.
        """
        data = self.readLongString()
        xml = util.ET.fromstring(data)
        self.context.addObject(xml)

        return xml

class Encoder(pyamf.BaseEncoder):
    """
    Encodes an AMF0 stream.

    @ivar use_amf3: A flag to determine whether this encoder knows about AMF3.
    @type use_amf3: C{bool}
    """

    context_class = Context

    type_map = [
        ((types.BuiltinFunctionType, types.BuiltinMethodType,
            types.FunctionType, types.GeneratorType, types.ModuleType,
            types.LambdaType, types.MethodType), "writeFunc"),
        ((types.NoneType,), "writeNull"),
        ((bool,), "writeBoolean"),
        ((int,long,float), "writeNumber"),
        ((types.StringTypes,), "writeString"),
        ((pyamf.ASObject,), "writeObject"),
        ((pyamf.MixedArray,), "writeMixedArray"),
        ((types.ListType, types.TupleType,), "writeArray"),
        ((datetime.date, datetime.datetime), "writeDate"),
        ((util.is_ET_element,), "writeXML"),
        ((lambda x: x is pyamf.Undefined,), "writeUndefined"),
        ((types.InstanceType,types.ObjectType,), "writeObject"),
    ]

    def __init__(self, *args, **kwargs):
        self.use_amf3 = kwargs.pop('use_amf3', False)

        pyamf.BaseEncoder.__init__(self, *args, **kwargs)

    def writeType(self, type):
        """
        Writes the type to the stream.

        @type   type: C{int}
        @param  type: ActionScript type.

        @raise pyamf.EncodeError: AMF0 type is not recognized.
        """
        if type not in ACTIONSCRIPT_TYPES:
            raise pyamf.EncodeError("Unknown AMF0 type 0x%02x at %d" % (
                type, self.stream.tell() - 1))

        self.stream.write_uchar(type)

    def writeUndefined(self, data):
        """
        Writes the L{undefined<ASTypes.UNDEFINED>} data type to the stream.

        @param data: The C{undefined} data to be encoded to the AMF0 data
            stream.
        @type data: C{undefined} data
        """
        self.writeType(ASTypes.UNDEFINED)

    def writeFunc(self, *args, **kwargs):
        """
        Functions cannot be serialised.
        """
        raise pyamf.EncodeError("Callables cannot be serialised")

    def writeUnsupported(self, data):
        """
        Writes L{unsupported<ASTypes.UNSUPPORTED>} data type to the
        stream.

        @param data: The C{unsupported} data to be encoded to the AMF0
            data stream.
        @type data: C{unsupported} data
        """
        self.writeType(ASTypes.UNSUPPORTED)

    def _writeElementFunc(self, data):
        """
        Gets a function based on the type of data.

        @see: L{pyamf.BaseEncoder._writeElementFunc}
        """
        # There is a very specific use case that we must check for.
        # In the context there is an array of amf3_objs that contain
        # references to objects that are to be encoded in amf3.
        try:
            self.context.getAMF3ObjectReference(data)
            return self.writeAMF3
        except pyamf.ReferenceError:
            pass

        return pyamf.BaseEncoder._writeElementFunc(self, data)

    def writeElement(self, data):
        """
        Writes the data.

        @type data: C{mixed}
        @param data: The data to be encoded to the AMF0 data stream.
        @raise EncodeError: Cannot find encoder func.
        """
        func = self._writeElementFunc(data)

        if func is None:
            raise pyamf.EncodeError("Cannot find encoder func for %r" % (data,))
        else:
            try:
                func(data)
            except (KeyboardInterrupt, SystemExit):
                raise
            except pyamf.EncodeError:
                raise
            except:
                #raise pyamf.EncodeError("Unable to encode '%r'" % (data,))
                raise

    def writeNull(self, n):
        """
        Write null type to data stream.

        @type   n: C{None}
        @param  n: Is ignored.
        """
        self.writeType(ASTypes.NULL)

    def writeArray(self, a):
        """
        Write array to the stream.

        @type a: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
        @param a: The array data to be encoded to the AMF0 data stream.
        """
        alias = self.context.getClassAlias(a.__class__)

        if alias is not None and 'external' in alias.metadata:
            # a is a subclassed list with a registered alias - push to the
            # correct method
            self.writeObject(a)

            return

        try:
            self.writeReference(a)
            return
        except pyamf.ReferenceError:
            self.context.addObject(a)

        self.writeType(ASTypes.ARRAY)
        self.stream.write_ulong(len(a))

        for data in a:
            self.writeElement(data)

    def writeNumber(self, n):
        """
        Write number to the data stream.

        @type   n: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
        @param  n: The number data to be encoded to the AMF0 data stream.
        """
        self.writeType(ASTypes.NUMBER)
        self.stream.write_double(float(n))

    def writeBoolean(self, b):
        """
        Write boolean to the data stream.

        @type b: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
        @param b: The boolean data to be encoded to the AMF0 data stream.
        """
        self.writeType(ASTypes.BOOL)

        if b:
            self.stream.write_uchar(1)
        else:
            self.stream.write_uchar(0)

    def _writeString(self, s):
        if not isinstance(s, basestring):
            s = unicode(s).encode('utf8')

        if len(s) > 0xffff:
            self.stream.write_ulong(len(s))
        else:
            self.stream.write_ushort(len(s))

        self.stream.write(s)

    def writeString(self, s, writeType=True):
        """
        Write string to the data stream.

        @type s: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
        @param s: The string data to be encoded to the AMF0 data stream.
        @type writeType: C{bool}
        @param writeType: Write data type.
        """
        if isinstance(s, unicode):
            s = s.encode('utf8')
        elif not isinstance(s, basestring):
            s = unicode(s).encode('utf8')

        if len(s) > 0xffff:
            if writeType:
                self.writeType(ASTypes.LONGSTRING)
        else:
            if writeType:
                self.stream.write_uchar(ASTypes.STRING)

        self._writeString(s)

    def writeReference(self, o):
        """
        Write reference to the data stream.

        @type o: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
        @param o: The reference data to be encoded to the AMF0 data
            stream.
        """
        idx = self.context.getObjectReference(o)

        self.writeType(ASTypes.REFERENCE)
        self.stream.write_ushort(idx)

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
        try:
            self.writeReference(o)
            return
        except pyamf.ReferenceError:
            self.context.addObject(o)

        self.writeType(ASTypes.MIXEDARRAY)

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
        # Write a null string, this is an optimisation so that we don't
        # have to waste precious cycles by encoding the string etc.
        self.stream.write('\x00\x00')
        self.writeType(ASTypes.OBJECTTERM)

    def _getObjectAttrs(self, o, alias):
        """
        @raise pyamf.EncodeError: Unable to determine object attributes.
        """
        obj_attrs = None

        if alias is not None:
            obj_attrs = {}

            for attrs in alias.getAttributes(o, codec=self):
                obj_attrs.update(attrs)

        if obj_attrs is None:
            obj_attrs = util.get_attrs(o)

        if obj_attrs is None:
            raise pyamf.EncodeError('Unable to determine object attributes')

        return obj_attrs

    def writeObject(self, o):
        """
        Write object to the stream.

        @type o: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
        @param o: The object data to be encoded to the AMF0 data stream.
        """
        if self.use_amf3 is True:
            self.writeAMF3(o)

            return

        try:
            self.writeReference(o)
            return
        except pyamf.ReferenceError:
            self.context.addObject(o)

        alias = self.context.getClassAlias(o.__class__)

        if alias is None:
            self.writeType(ASTypes.OBJECT)
        else:
            if 'amf3' in alias.metadata:
                self.writeAMF3(o)

                return

            if 'anonymous' in alias.metadata:
                self.writeType(ASTypes.OBJECT)
            else:
                self.writeType(ASTypes.TYPEDOBJECT)
                self.writeString(alias.alias, False)

        obj_attrs = self._getObjectAttrs(o, alias)

        for key, value in obj_attrs.iteritems():
            self.writeString(key, False)
            self.writeElement(value)

        self._writeEndObject()

    def writeDate(self, d):
        """
        Writes a date to the data stream.

        @type d: Instance of C{datetime.datetime}
        @param d: The date to be encoded to the AMF0 data stream.
        """
        # According to the Red5 implementation of AMF0, dates references are
        # created, but not used.
        secs = util.get_timestamp(d)
        tz = 0

        self.writeType(ASTypes.DATE)
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

        self.writeType(ASTypes.XML)

        data = util.ET.tostring(e, 'utf-8')
        self.stream.write_ulong(len(data))
        self.stream.write(data)

    def writeAMF3(self, data):
        """
        Writes an element to the datastream in L{AMF3<pyamf.amf3>} format.

        @type data: C{mixed}
        @param data: The data to be encoded to the AMF0 data stream.
        """
        if not hasattr(self.context, 'amf3_context'):
            from pyamf import amf3

            self.context.amf3_context = amf3.Context()

        self.context.addAMF3Object(data)
        encoder = pyamf._get_encoder_class(pyamf.AMF3)(self.stream, self.context.amf3_context)

        self.writeType(ASTypes.AMF3)
        encoder.writeElement(data)

def decode(stream, context=None, strict=False):
    """
    A helper function to decode an AMF0 datastream.

    @type   stream: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
    @param  stream: AMF0 datastream.
    @type   context: L{Context<pyamf.amf0.Context>}
    @param  context: AMF0 Context.
    """
    decoder = Decoder(stream, context, strict=strict)

    while 1:
        try:
            yield decoder.readElement()
        except pyamf.EOStream:
            break

def encode(*args, **kwargs):
    """
    A helper function to encode an element into the AMF0 format.

    @type element: C{mixed}
    @keyword element: The element to encode
    @type context: L{Context<pyamf.amf0.Context>}
    @keyword context: AMF0 C{Context} to use for the encoding. This holds
        previously referenced objects etc.
    @rtype: C{StringIO}
    @return: The encoded stream.
    """
    context = kwargs.get('context', None)
    buf = util.BufferedByteStream()
    encoder = Encoder(buf, context)

    for element in args:
        encoder.writeElement(element)

    return buf

class RecordSet(object):
    """
    I represent the C{RecordSet} class used in Flash Remoting to hold
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

pyamf.register_class(RecordSet, 'RecordSet', attrs=['serverInfo'], metadata=['amf0'])

def _check_for_int(x):
    """
    This is a compatibility function that takes a C{float} and converts it to an
    C{int} if the values are equal.
    """
    try:
        y = int(x)
    except (OverflowError, ValueError):
        pass
    else:
        # There is no way in AMF0 to distinguish between integers and floats
        if x == x and y == x:
            return y

    return x

# check for some Python 2.3 problems with floats
try:
    float('nan')
except ValueError:
    pass
else:
    if float('nan') == 0:
        def check_nan(func):
            def f2(x):
                if str(x).lower().find('nan') >= 0:
                    return x

                return f2.func(x)
            f2.func = func

            return f2

        _check_for_int = check_nan(_check_for_int)
