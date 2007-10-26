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
# Resources:
#   http://www.vanrijkom.org/archives/2005/06/amf_format.html
#   http://osflash.org/documentation/amf3

"""AMF3 Implementation"""

import types, datetime, time, copy

import pyamf
from pyamf import util

class ASTypes:
    UNDEFINED  = 0x00
    NULL       = 0x01
    BOOL_FALSE = 0x02
    BOOL_TRUE  = 0x03
    INTEGER    = 0x04
    NUMBER     = 0x05
    STRING     = 0x06
    # TODO: not defined on site, says it's only XML type,
    # so we'll assume it is for the time being..
    # XXX nick: According to http://osflash.org/documentation/amf3 this
    # represents the legacy XMLDocument
    XML        = 0x07
    DATE       = 0x08
    ARRAY      = 0x09
    OBJECT     = 0x0a
    XMLSTRING  = 0x0b
    BYTEARRAY  = 0x0c

ACTIONSCRIPT_TYPES = set(
    ASTypes.__dict__[x] for x in ASTypes.__dict__ if not x.startswith('__'))

REFERENCE_BIT = 0x01

class ObjectEncoding:
    # Property list encoding.
    # The remaining integer-data represents the number of
    # class members that exist. The property names are read
    # as string-data. The values are then read as AMF3-data.
    STATIC = 0x00

    # Externalizable object.
    # What follows is the value of the "inner" object,
    # including type code. This value appears for objects
    # that implement IExternalizable, such as
    # ArrayCollection and ObjectProxy.
    EXTERNAL = 0x01
    
    # Name-value encoding.
    # The property names and values are encoded as string-data
    # followed by AMF3-data until there is an empty string
    # property name. If there is a class-def reference there
    # are no property names and the number of values is equal
    # to the number of properties in the class-def.
    DYNAMIC = 0x02
    
    # Proxy object
    PROXY = 0x03

class ByteArray(str):
    """
    I am a file type object containing byte data from the AMF stream
    """

class ClassDefinition(object):
    """
    I contain meta relating to the class definition
    """
    attrs = []

    def __init__(self, name, encoding):
        self.name = name
        self.encoding = encoding

    def is_external(self):
        return self.encoding == ObjectEncoding.EXTERNAL

    def is_static(self):
        return self.encoding == ObjectEncoding.STATIC

    def is_dynamic(self):
        return self.encoding == ObjectEncoding.DYNAMIC

    external = property(is_external)
    static = property(is_static)
    dynamic = property(is_dynamic)

class Parser(object):
    """
    Parses an AMF3 data stream
    """

    type_map = {
        ASTypes.UNDEFINED: 'readNull',
        ASTypes.NULL: 'readNull',
        ASTypes.BOOL_FALSE: 'readBoolFalse',
        ASTypes.BOOL_TRUE: 'readBoolTrue',
        ASTypes.INTEGER: 'readInteger',
        ASTypes.NUMBER: 'readNumber',
        ASTypes.STRING: 'readString',
        ASTypes.XML: 'readXML',
        ASTypes.DATE: 'readDate',
        ASTypes.ARRAY: 'readArray',
        ASTypes.OBJECT: 'readObject',
        ASTypes.XMLSTRING: 'readString',
        ASTypes.BYTEARRAY: 'readByteArray',
    }

    def __init__(self, data=None, context=None):
        if isinstance(data, util.BufferedByteStream):
            self.input = data
        else:
            self.input = util.BufferedByteStream(data)

        if context == None:
            context = pyamf.Context()

        self.context = context

    def readType(self):
        """
        Read and returns the next byte in the stream and determine its type.
        Raises ValueError if not recognized
        """
        type = self.input.read_uchar()

        if type not in ACTIONSCRIPT_TYPES:
            raise pyamf.ParseError("Unknown AMF3 type 0x%02x at %d" % (
                type, self.input.tell() - 1))

        return type

    def readNull(self):
        return None

    def readBoolFalse(self):
        return False

    def readBoolTrue(self):
        return True

    def readNumber(self):
        return self.input.read_double()

    def readElement(self):
        """Reads the data type."""
        type = self.readType()

        try:
            func = getattr(self, self.type_map[type])
        except KeyError, e:
            raise NotImplementedError(
                "Unsupported ActionScript type 0x%02x" % type)

        return func()

    def readInteger(self):
        """
        Reads and returns an integer from the stream
        See http://osflash.org/amf3/parsing_integers for AMF3 integer data
        format
        """
        n = 0
        b = self.input.read_uchar()
        result = 0

        while b & 0x80 and n < 3:
            result <<= 7
            result |= b & 0x7f
            b = self.input.read_uchar()
            n += 1

        if n < 3:
            result <<= 7
            result |= b
        else:
            result <<= 8
            result |= b

            if result & 0x10000000:
                result |= 0xe0000000

        return result

    def readString(self, use_references=True):
        """
        Reads and returns a string from the stream.
        """
        def readLength():
            x = self.readInteger()

            return (x >> 1, x & REFERENCE_BIT == 0)

        length, is_reference = readLength()

        if use_references and is_reference:
            return self.context.getString(length)

        buf = self.input.read(length)

        try:
            # Try decoding as regular utf8 first since that will
            # cover most cases and is more efficient.
            # XXX: I'm not sure if it's ok though..
            # will it always raise exception?
            result = unicode(buf, "utf8")
        except UnicodeDecodeError:
            result = decode_utf8_modified(buf)

        if len(result) != 0 and use_references:
            self.context.addString(result)

        return result

    def readXML(self):
        return util.ET.fromstring(self.readString(False))

    def readDate(self):
        ref = self.readInteger()
        
        if ref & REFERENCE_BIT == 0:
            return self.context.getObject(ref >> 1)

        ms = self.input.read_double()
        result = datetime.datetime.fromtimestamp(ms / 100)

        self.context.addObject(result)

        return result

    def readArray(self):
        """
        Reads an array from the stream.

        There is a very specific problem with AMF3 where the first three bytes
        of an encoded empty dict will mirror that of an encoded {'': 1, '2': 2}

        See http://www.docuverse.com/blog/donpark/2007/05/14/flash-9-amf3-bug
        for more information.
        """
        if self.input.peek(2) == '\x01\x01':
            raise pyamf.ParseError("empty dict bug encountered")

        size = self.readInteger()

        if size & REFERENCE_BIT == 0:
            return self.context.getObject(size >> 1)

        size >>= 1

        key = self.readString()

        if key == "":
            # integer indexes only -> python list
            result = [self.readElement() for i in xrange(size)]

        else:
            # key,value pairs -> python dict
            result = {}

            while key != "":
                el = self.readElement()

                try:
                    result[str(key)] = el
                except UnicodeError:
                    result[key] = el

                key = self.readString()

            for i in xrange(size):
                el = self.readElement()
                result[i] = el

        self.context.addObject(result)

        return result

    def _getClassDefinition(self, ref):
        class_ref = ref & REFERENCE_BIT == 0
        
        ref >>= 1

        if class_ref:
            class_def = self.context.getClassDefinition(ref)
        else:
            class_def = ClassDefinition(self.readString(), ref & 0x03)
            self.context.addClassDefinition(class_def)

        return class_ref, class_def

    def readObject(self):
        """
        Reads an object from the stream.
        """
        ref = self.readInteger()

        if ref & REFERENCE_BIT == 0:
            return self.context.getObject(ref >> 1)

        ref >>= 1
        (class_ref, class_def) = self._getClassDefinition(ref)
        ref >>= 3

        klass = self.context.getClass(class_def)
        obj = klass()

        if class_def.external:
            # TODO: implement externalizeable interface here
            obj.__amf_externalized_data = self.readElement()

        elif class_def.dynamic:
            attr = self.readString()

            while attr != "":
                if attr not in class_def.attrs:
                    class_def.attrs.append(attr)

                obj[attr] = self.readElement()
                attr = self.readString()

        elif class_def.static:
            if not class_ref:
                class_def.attrs = [self.readString() for i in range(ref)]

            for attr in class_def.attrs:
                setattr(obj, attr, self.readElement())
        else:
            raise pyamf.ParseError("Unknown object encoding")

        self.context.addObject(obj)

        return obj

    def readByteArray(self):
        """
        Reads a string of data from the stream.
        """
        length = self.readInteger()

        return ByteArray(self.input.read(length >> 1))

class Encoder(object):

    type_map = [
        # Unsupported types go first
        ((types.BuiltinFunctionType, types.BuiltinMethodType,), "writeUnsupported"),
        ((bool,), "writeBoolean"),
        ((int,long), "writeInteger"),
        ((float,), "writeNumber"),
        ((ByteArray,), "writeByteArray"),
        ((types.StringTypes,), "writeString"),
        ((util.ET._ElementInterface,), "writeXML"),
        ((types.DictType,), "writeDict"),
        ((types.ListType,types.TupleType,), "writeList"),
        ((datetime.date, datetime.datetime), "writeDate"),
        ((types.NoneType,), "writeNull"),
        ((types.InstanceType,types.ObjectType,), "writeObject"),
    ]

    def __init__(self, output, context=None):
        """Constructs a new Encoder. output should be a writable
        file-like object."""
        self.output = output

        if context == None:
            context = pyamf.Context()

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

    def writeElement(self, data):
        """
        Writes an encoded version of data to the output stream
        """
        for tlist, method in self.type_map:
            for t in tlist:
                if isinstance(data, t):
                    try:
                        return getattr(self, method)(data)
                    except AttributeError:
                        # Should NotImplementedError be raised here?
                        raise

    def writeNull(self, n):
        self.writeType(ASTypes.NULL)

    def writeBoolean(self, n):
        if n:
            self.writeType(ASTypes.BOOL_TRUE)
        else:
            self.writeType(ASTypes.BOOL_FALSE)

    def _writeInteger(self, n):
        """
        AMF Integers are encoded.
        
        See http://osflash.org/documentation/amf3/parsing_integers for more
        info.
        """
        bytes = []

        if n & 0xff000000 == 0:
            for i in xrange(3, -1, -1):
                bytes.append((n >> (7 * i)) & 0x7F)
        else:
            for i in xrange(2, -1, -1):
                bytes.append(n >> (8 + 7 * i) & 0x7F)

            bytes.append(n & 0xFF)

        for x in bytes[:-1]:
            if x > 0:
                self.output.write_uchar(x | 0x80)

        self.output.write_uchar(bytes[-1])

    def writeInteger(self, n):
        """
        Writes an integer to the data stream
        """
        self.writeType(ASTypes.INTEGER)
        self._writeInteger(n)

    def writeNumber(self, n):
        """
        Writes a non integer to the data stream
        """
        self.writeType(ASTypes.NUMBER)
        self.output.write_double(n)

    def _writeString(self, n):
        """
        Writes a raw string to the stream.
        """
        if len(n) == 0:
            self._writeInteger(REFERENCE_BIT)

            return

        try:
            ref = self.context.getStringReference(n)
            self._writeInteger(ref << 1)

            return
        except pyamf.ReferenceError:
            self.context.addString(n)

        s = encode_utf8_modified(n)[2:]
        self._writeInteger((len(s) << 1) | REFERENCE_BIT)

        for ch in s:
            self.output.write_uchar(ord(ch))

    def writeString(self, n):
        """
        Writes a unicode string to the stream.
        """
        self.writeType(ASTypes.STRING)
        self._writeString(n)

    def writeDate(self, n):
        """
        Writes a datetime instance to the stream.
        """
        if isinstance(n, datetime.date):
            n = datetime.datetime.combine(n, datetime.time(0))

        self.writeType(ASTypes.DATE)

        try:
            ref = self.context.getObjectReference(n)
            self._writeInteger(ref << 1)

            return
        except pyamf.ReferenceError:
            pass

        self.context.addObject(n)
        self._writeInteger(REFERENCE_BIT)

        ms = time.mktime(n.timetuple())
        self.output.write_double(ms * 100.0)

    def writeList(self, n):
        """
        Writes a list to the stream.
        """
        self.writeType(ASTypes.ARRAY)

        try:
            ref = self.context.getObjectReference(n)
            self._writeInteger(ref << 1)

            return
        except pyamf.ReferenceError:
            pass

        self.context.addObject(n)
        self._writeInteger(len(n) << 1 | REFERENCE_BIT)

        self.output.write_uchar(0x01)
        for x in n:
            self.writeElement(x)

    def writeDict(self, n):
        """
        Writes a dict to the stream.
        """
        self.writeType(ASTypes.ARRAY)

        try:
            ref = self.context.getObjectReference(n)
            self._writeInteger(ref << 1)

            return
        except pyamf.ReferenceError:
            pass

        self.context.addObject(n)

        # The AMF3 spec demands that all str based indicies be listed first
        keys = n.keys()
        int_keys = []
        str_keys = []

        for x in keys:
            if isinstance(x, (int, long)):
                int_keys.append(x)
            elif isinstance(x, (str, unicode)):
                str_keys.append(x)
            else:
                raise ValueError("Non int/str key value found in dict")

        # Make sure the integer keys are within range
        l = len(int_keys)

        for x in int_keys:
            if l < x <= 0:
                # treat as a string key
                str_keys.append(x)
                del int_keys[int_keys.index(x)]

        int_keys.sort()

        # If integer keys don't start at 0, they will be treated as strings
        if len(int_keys) > 0 and int_keys[0] != 0:
            for x in int_keys:
                str_keys.append(str(x))
                del int_keys[int_keys.index(x)]

        self._writeInteger(len(int_keys) << 1 | REFERENCE_BIT)

        for x in str_keys:
            # Design bug in AMF3 that cannot read/write empty key strings
            # http://www.docuverse.com/blog/donpark/2007/05/14/flash-9-amf3-bug
            # for more info
            if x == '':
                raise pyamf.EncodeError(
                    "dicts cannot contain empty string keys")

            self._writeString(x)
            self.writeElement(n[x])

        self.output.write_uchar(0x01)

        for k in int_keys:
            self.writeElement(n[k])

    def _getClassDefinition(self, obj):
        try:
            alias = pyamf.get_class_alias(obj)
        except LookupError:
            alias = '%s.%s' % (obj.__module__, obj.__class__.__name__)

        class_def = ClassDefinition(alias, ObjectEncoding.STATIC)

        for name in obj.__dict__.keys():
            class_def.attrs.append(name)

        return class_def

    def writeObject(self, obj):
        """
        Writes an object to the stream.
        """
        self.writeType(ASTypes.OBJECT)
        try:
            ref = self.context.getObjectReference(obj)
            self._writeInteger(ref << 1)

            return
        except pyamf.ReferenceError:
            pass

        self.context.addObject(obj)

        try:
            ref = self.context.getClassDefinitionReference(obj)
            class_ref = True

            self._writeInteger(ref << 2 | REFERENCE_BIT)
        except pyamf.ReferenceError:
            class_def = self._getClassDefinition(obj)
            class_ref = False

            ref = 0

            if class_def.encoding != ObjectEncoding.EXTERNAL:
                ref += len(class_def.attrs) << 4

            self._writeInteger(ref | class_def.encoding << 2 |
                REFERENCE_BIT << 1 | REFERENCE_BIT)
            self._writeString(class_def.name)

        if class_def.encoding == ObjectEncoding.EXTERNAL:
            # TODO
            pass
        elif class_def.encoding == ObjectEncoding.DYNAMIC:
            if not class_ref:
                for attr in class_def.attrs:
                    self._writeString(attr)
                    self.writeElement(getattr(obj, attr))

                self.writeString("")
            else:
                for attr in class_def.attrs:
                    self.writeElement(getattr(obj, attr))
        elif class_def.encoding == ObjectEncoding.STATIC:
            if not class_ref:
                for attr in class_def.attrs:
                    self._writeString(attr)

            for attr in class_def.attrs:
                self.writeElement(getattr(obj, attr))

    def writeByteArray(self, n):
        """
        Writes a L{ByteArray} to the data stream.
        """
        self.writeType(ASTypes.BYTEARRAY)
        
        try:
            ref = self.context.getObjectReference(n)
            self._writeInteger(ref << 1)

            return
        except pyamf.ReferenceError:
            pass

        self.context.addObject(n)
        self._writeInteger(len(n) << 1 | REFERENCE_BIT)

        for ch in n:
            self.output.write_uchar(ord(ch))

class AbstractMessage(object):

    def __init__(self):
        # The body of the message.
        self.data = None
        # Unique client ID.
        self.clientId = None
        # Destination.
        self.destination = None
        # Message headers.
        self.headers = []
        # Unique message ID 
        self.messageId = None
        # timeToLive
        self.timeToLive = None
        # timestamp
        self.timestamp = None

    def __repr__(self):
        return "<AbstractMessage clientId=%s data=%r>" % (self.clientId, self.data)

class AcknowledgeMessage(AbstractMessage):

    def __init__(self):
        """
        This is the receipt for any message thats being sent.
        """
        AbstractMessage.__init__(self)
        # The ID of the message where this is a receipt of.
        self.correlationId = None

    def __repr__(self):
        return "<AcknowledgeMessage correlationId=%s>" % (self.correlationId)

class CommandMessage(AbstractMessage):

    def __init__(self):
        """
        This class is used for service commands, like pinging the server.
        """
        AbstractMessage.__init__(self)
        self.operation = None
        # The ID of the message where this is a receipt of.
        self.correlationId = None
        self.messageRefType = None
    
    def __repr__(self):
        return "<CommandMessage correlationId=%s operation=%r messageRefType=%d>" % (
            self.correlationId, self.operation, self.messageRefType)

class ErrorMessage(AbstractMessage):

    def __init__(self):
        """
        This is the receipt for Error Messages.
        """
        AbstractMessage.__init__(self)
        # Extended data that the remote destination has chosen to associate with 
        # this error to facilitate custom error processing on the client.
        self.extendedData = {}
        # The fault code for the error. 
        self.faultCode = None
        # Detailed description of what caused the error. 
        self.faultDetail = None
        # A simple description of the error. 
        self.faultString = None
        # Should a root cause exist for the error, this property contains those details.
        self.rootCause = {}

    def __repr__(self):
        return "<ErrorMessage faultCode=%s faultString=%r>" % (
            self.faultCode, self.faultString)

class RemotingMessage(AbstractMessage):

    def __init__(self):
        AbstractMessage.__init__(self)
        self.operation = None
        self.source = None

    def __repr__(self):
        return "<RemotingMessage operation=%s source=%r>" % (self.operation, self.source)

def encode_utf8_modified(data):
    """
    Encodes a unicode string to Modified UTF-8 data.
    See http://en.wikipedia.org/wiki/UTF-8#Java for details.
    """
    if not isinstance(data, unicode):
        data = unicode(data, "utf8")

    bytes = ''
    charr = data.encode("utf_16_be")
    utflen = 0
    i = 0

    for i in xrange(0, len(charr), 2):
        ch = ord(charr[i]) << 8 | ord(charr[i+1])

        if 0x00 < ch < 0x80:
            utflen += 1
            bytes += chr(ch)
        elif ch < 0x800:
            utflen += 2
            bytes += chr(0xc0 | ((ch >>  6) & 0x1f))
            bytes += chr(0x80 | ((ch >>  0) & 0x3f))
        else:
            utflen += 3
            bytes += chr(0xe0 | ((ch >> 12) & 0x0f))
            bytes += chr(0x80 | ((ch >> 6) & 0x3f))
            bytes += chr(0x80 | ((ch >> 0) & 0x3f))

    return chr((utflen >> 8) & 0xff) + chr((utflen >> 0) & 0xff) + bytes

# Ported from http://viewvc.rubyforge.mmmultiworks.com/cgi/viewvc.cgi/trunk/lib/ruva/class.rb
# Ruby version is Copyright (c) 2006 Ross Bamford (rosco AT roscopeco DOT co DOT uk).
def decode_utf8_modified(data):
    """
    Decodes a unicode string from Modified UTF-8 data.
    See http://en.wikipedia.org/wiki/UTF-8#Java for details.
    """
    size = ((ord(data[0]) << 8) & 0xff) + ((ord(data[1]) << 0) & 0xff)
    data = data[2:]
    utf16 = []
    i = 0

    while i < len(data):
        ch = ord(data[i])
        c = ch >> 4

        if 0 <= c <= 7:
            utf16.append(ch)
            i += 1
        elif 12 <= c <= 13:
            utf16.append(((ch & 0x1f) << 6) | (ord(data[i+1]) & 0x3f))
            i += 2
        elif c == 14:
            utf16.append(
                ((ch & 0x0f) << 12) |
                ((ord(data[i+1]) & 0x3f) << 6) |
                (ord(data[i+2]) & 0x3f))
            i += 3
        else:
            raise ValueError("Data is not valid modified UTF-8")

    utf16 = "".join([chr((c >> 8) & 0xff) + chr(c & 0xff) for c in utf16])

    return unicode(utf16, "utf_16_be")
