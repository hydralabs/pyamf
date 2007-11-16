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
AMF3 implementation.

AMF3 is the default serialization for
U{ActionScript<http://en.wikipedia.org/wiki/ActionScript>} 3.0 and
provides various advantages over L{AMF0<pyamf.amf0>}, which is used
for ActionScript 1.0 and 2.0. It adds support for sending C{int}
and C{uint} objects as integers and supports data types that are
available only in ActionScript 3.0, such as L{ByteArray} and
L{ArrayCollection}.

@see: U{AMF3 documentation on OSFlash (external)
<http://osflash.org/documentation/amf3>}

@author: U{Arnar Birgisson<mailto:arnarbi@gmail.com>}
@author: U{Thijs Triemstra<mailto:info@collab.nl>}
@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import types, datetime, zlib

import pyamf
from pyamf import util, compat

class ASTypes:
    """
    All AMF3 data types used in ActionScript 3.0.
    
    AMF represents ActionScript objects by a single byte representing
    type, and then by a type-specific byte array that may be of fixed
    length, may contain length information, or may come with its own end
    code.

    @see: U{AMF3 data types on OSFlash (external)
    <http://osflash.org/documentation/amf3#data_types>}
    """
    #: Simple type that doesn't have any inner data.
    UNDEFINED  = 0x00
    #: Simple type that doesn't have any inner data.
    NULL       = 0x01
    #: Simple type that doesn't have any inner data.
    BOOL_FALSE = 0x02
    #: Simple type that doesn't have any inner data.
    BOOL_TRUE  = 0x03
    #: 0×04 integer type code, followed by up to 4 bytes of data.
    #: @see: U{Parsing Integers on OSFlash (external)
    #: <http://osflash.org/documentation/amf3/parsing_integers>}
    INTEGER    = 0x04
    #: 0x05 Number type-code followed by 8 bytes of data.
    #:
    #: Format is the same as an AMF0
    #: L{Number<pyamf.amf0.ASTypes.NUMBER>}.
    NUMBER     = 0x05
    #: 
    STRING     = 0x06
    # TODO: not defined on site, says it's only XML type,
    # so we'll assume it is for the time being..
    #: @see: According to U{the OSFlash documentation
    #:<http://osflash.org/documentation/amf3>} this
    #: represents the legacy C{flash.xml.XMLDocument}.
    XML        = 0x07
    #: 0×08 integer-data.
    DATE       = 0x08
    #: 0×09 integer-data ( [ 1OCTET *amf3-data ] | [OCTET *amf3-data 1]
    #: | [ OCTET *amf-data ] )
    ARRAY      = 0x09
    #: 0x0A integer-data [ class-def ] [ *amf3-data ]
    OBJECT     = 0x0a
    #: This type is used for the E4X XML class.
    XMLSTRING  = 0x0b
    #: 0x0c L{ByteArray} flag, followed by string data.
    #: @see: U{Parsing ByteArrays on OSFlash (external)
    #: <http://osflash.org/documentation/amf3/parsing_byte_arrays>}
    BYTEARRAY  = 0x0c

#: List of available ActionScript types in AMF3.
ACTIONSCRIPT_TYPES = []

for x in ASTypes.__dict__:
    if not x.startswith('_'):
        ACTIONSCRIPT_TYPES.append(ASTypes.__dict__[x])

#: Reference bit.
REFERENCE_BIT = 0x01

class ObjectEncoding:
    """
    AMF object encodings.
    """
    #: Property list encoding.
    #: The remaining integer-data represents the number of
    #: class members that exist. The property names are read
    #: as string-data. The values are then read as AMF3-data.
    STATIC = 0x00

    #: Externalizable object.
    #: What follows is the value of the "inner" object,
    #: including type code. This value appears for objects
    #: that implement IExternalizable, such as
    #: ArrayCollection and ObjectProxy.
    EXTERNAL = 0x01
    
    #: Name-value encoding.
    #: The property names and values are encoded as string-data
    #: followed by AMF3-data until there is an empty string
    #: property name. If there is a class-def reference there
    #: are no property names and the number of values is equal
    #: to the number of properties in the class-def.
    DYNAMIC = 0x02
    
    #: Proxy object.
    PROXY = 0x03

class ByteArray(util.StringIOProxy):
    """
    I am a C{StringIO} type object containing byte data from
    the AMF stream.

    Possible uses of the C{ByteArray} class:

     - Creating a custom protocol to connect to a client.
     - Writing your own AMF/Remoting packet.
     - Optimizing the size of your data by using custom
     data types.

    Supports C{zlib} compression.
     
    @see: U{ByteArray on Livedocs (external)
    <http://livedocs.adobe.com/flex/2/langref/flash/utils/ByteArray.html>}
    """

    def __init__(self, *args, **kwargs):
        util.StringIOProxy.__init__(self, *args, **kwargs)
        self._was_compressed = False

    def __cmp__(self, other):
        if isinstance(other, ByteArray):
            return cmp(self._buffer.getvalue(), other._buffer.getvalue())

        return cmp(self._buffer, other)

class ClassDefinition(object):
    """
    I contain meta relating to the class definition.

    @ivar alias: The alias to this class definition. If this value is None, or
                 an empty string, the class is considered to be anonymous.
    @type alias: L{pyamf.ClassAlias}
    @ivar encoding: The type of encoding to use when serializing the object.
    @type encoding: int
    @ivar attrs: List of attributes to encode.
    @type attrs: list 
    """

    def __init__(self, alias, encoding=ObjectEncoding.STATIC):
        if alias in (None, ''):
            self.alias = None
        elif isinstance(alias, pyamf.ClassAlias):
            self.alias = alias
        else:
            self.alias = pyamf.get_class_alias(alias)

        self.encoding = encoding
        self.attrs = []

    def _get_name(self):
        if self.alias is None:
            # anonymous class
            return ''

        return str(self.alias)

    name = property(_get_name)

    def _getClass(self):
        """
        If C{alias} is None, an anonymous class is returned (L{pyamf.Bag}),
        otherwise the class is loaded externally.

        """
        if self.alias in (None, ''):
            # anonymous class
            return pyamf.Bag

        return self.getClassAlias().klass

    def getClassAlias(self):
        """
        Gets the class alias that is held by this definition.

        @see L{pyamf.load_class}
        @rtype: L{pyamf.ClassAlias}
        """
        if not hasattr(self, '_alias'):
            if self.name == '':
                raise pyamf.UnknownClassAlias, '%s' % (
                    'Anonymous class definitions do not have class aliases')

            self._alias = pyamf.load_class(self.alias) 

        return self._alias

    def getClass(self):
        """
        Gets the referenced class that is held by this definition.
        """
        if hasattr(self, '_alias'):
            return self._alias

        self._klass = self._getClass()

        return self._klass

    klass = property(getClass)

class Context(pyamf.BaseContext):
    """
    I hold the AMF3 context for en/decoding streams.

    @ivar strings: A list of string references.
    @type strings: list
    @ivar classes: A list of L{ClassDefinition}.
    @type classes: list
    """

    def clear(self):
        """
        Resets the context.
        """
        pyamf.BaseContext.clear(self)

        self.strings = []
        self.classes = []

    def _getObject(self, ref):
        return self.objects[ref]

    def _getObjectReference(self, obj):
        return self.objects.index(obj)

    def _addObject(self, obj):
        try:
            return self.objects.index(obj) - 1
        except ValueError:
            self.objects.append(obj)

            return len(self.objects) - 1

    def getString(self, ref):
        """
        Gets a string based on a reference C{ref}.

        @param ref: The reference index.
        @type ref: str
        @return: The referenced string.
        @rtype: str 
        @raise ReferenceError: The referenced string could not be found.
        """
        try:
            return self.strings[ref]
        except IndexError:
            raise pyamf.ReferenceError("String reference %d not found" % ref)

    def getStringReference(self, s):
        """
        Return string reference.

        @type s: str
        @param s: The referenced string.
        @raise ReferenceError: the string reference could not be found.
        @return: The reference index to the string.
        @rtype: int
        """
        try:
            return self.strings.index(s)
        except ValueError:
            raise pyamf.ReferenceError("Reference for string %r not found" % s)

    def addString(self, s):
        """
        Creates a reference to s. If the reference already exists, that
        reference is returned.

        @type s: string
        @param s: The string to be referenced.
        @return: The reference index.
        @rtype: int
        """
        if len(s) == 0:
            # do not store empty string references
            raise ValueError, "Cannot store a reference to an empty string"

        try:
            return self.strings.index(s)
        except ValueError:
            self.strings.append(s)

            return len(self.strings) - 1

    def getClassDefinition(self, ref):
        """
        Return class reference.
               
        @type ref:
        @param ref:
        @raise ReferenceError: the class reference could not be found.
        @return: 
        """
        try:
            return self.classes[ref]
        except IndexError:
            raise pyamf.ReferenceError("Class reference %d not found" % ref)

    def getClassDefinitionReference(self, class_def):
        """
        Return class definition reference. 

        @type class_def:
        @param class_def:
        @raise ReferenceError: the definition could not be found.
        @return: 
        """
        try:
            return self.classes.index(class_def)
        except ValueError:
            raise pyamf.ReferenceError("Reference for class %r not found" % 
                class_def)

    def addClassDefinition(self, class_def):
        """
        Creates a reference to class_def.

        @type class_def:
        @param class_def:
        @return:
        """
        try:
            return self.classes.index(class_def)
        except ValueError:
            self.classes.append(class_def)

            return len(self.classes)

    def getClass(self, class_def):
        """
        @type class_def:
        @param class_def:
        @return:
        """

    def __copy__(self):
        return self.__class__()

class Decoder(object):
    """
    Decodes an AMF3 data stream.
    """
    #: Decoder type mappings.
    type_map = {
        ASTypes.UNDEFINED:  'readNull',
        ASTypes.NULL:       'readNull',
        ASTypes.BOOL_FALSE: 'readBoolFalse',
        ASTypes.BOOL_TRUE:  'readBoolTrue',
        ASTypes.INTEGER:    'readInteger',
        ASTypes.NUMBER:     'readNumber',
        ASTypes.STRING:     'readString',
        ASTypes.XML:        'readXML',
        ASTypes.DATE:       'readDate',
        ASTypes.ARRAY:      'readArray',
        ASTypes.OBJECT:     'readObject',
        ASTypes.XMLSTRING:  'readXMLString',
        ASTypes.BYTEARRAY:  'readByteArray',
    }

    def __init__(self, data=None, context=None):
        """
        @type   data: L{BufferedByteStream}
        @param  data: AMF3 data
        @type   context: L{Context}
        @param  context: Context
        """
        if isinstance(data, util.BufferedByteStream):
            self.stream = data
        else:
            self.stream = util.BufferedByteStream(data)

        if context == None:
            self.context = Context()
        elif isinstance(context, Context):
            self.context = context
        else:
            raise TypeError, "context must be of type amf3.Context"

    def readType(self):
        """
        Read and returns the next byte in the stream and determine its type.
        
        @raise DecodeError: AMF3 type not recognized
        @return: AMF3 type
        @rtype: int
        """
        type = self.stream.read_uchar()

        if type not in ACTIONSCRIPT_TYPES:
            raise pyamf.DecodeError("Unknown AMF3 type 0x%02x at %d" % (
                type, self.stream.tell() - 1))

        return type

    def readNull(self):
        """
        Read null and return None.

        @return: None
        @rtype: None
        """
        return None

    def readBoolFalse(self):
        """
        Returns False.

        @return: False
        @rtype: bool
        """
        return False

    def readBoolTrue(self):
        """
        Returns True.

        @return: True
        @rtype: bool
        """
        return True

    def readNumber(self):
        """
        Read number.
        """
        return self.stream.read_double()

    def readElement(self):
        """
        Reads an AMF3 element from the data stream.

        @raise DecodeError: the ActionScript type is unknown or
        there is insufficient data left in the stream.
        @return:
        @rtype:
        """
        type = self.readType()

        try:
            func = getattr(self, self.type_map[type])
        except KeyError, e:
            raise pyamf.DecodeError(
                "Unsupported ActionScript type 0x%02x" % type)
        
        try:
            return func()
        except EOFError:
            raise pyamf.DecodeError("Insufficient data")

    def readInteger(self):
        """
        Reads and returns an integer from the stream.

        @see: U{Parsing integers on OSFlash
        <http://osflash.org/amf3/parsing_integers>} for the AMF3
        integer data format.
        @return:
        @rtype:
        """
        n = 0
        b = self.stream.read_uchar()
        result = 0

        while b & 0x80 and n < 3:
            result <<= 7
            result |= b & 0x7f
            b = self.stream.read_uchar()
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

        @type use_references:
        @param use_references:
        @return:
        @rtype:
        """
        def readLength():
            x = self.readInteger()

            return (x >> 1, x & REFERENCE_BIT == 0)

        length, is_reference = readLength()

        if use_references and is_reference:
            return self.context.getString(length)

        buf = self.stream.read(length)

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
        """
        Read XML from the stream.

        @return:
        @rtype:
        """
        return util.ET.fromstring(self.readString(False))

    def readDate(self):
        """
        Read date from the stream.

        The timezone is ignored as the date is always in UTC.

        @return:
        @rtype:
        """
        ref = self.readInteger()

        if ref & REFERENCE_BIT == 0:
            return self.context.getObject(ref >> 1)

        ms = self.stream.read_double()
        result = util.get_datetime(ms / 1000.0)

        self.context.addObject(result)

        return result

    def readArray(self):
        """
        Reads an array from the stream.

        @warning: There is a very specific problem with AMF3 where the
        first three bytes of an encoded empty C{dict} will mirror that
        of an encoded C{{'': 1, '2': 2}}

        @bug: See the U{Docuverse blog
        <http://www.docuverse.com/blog/donpark/2007/05/14/flash-9-amf3-bug>}
        for more information.

        @return:
        @rtype:
        """
        size = self.readInteger()

        if size & REFERENCE_BIT == 0:
            return self.context.getObject(size >> 1)

        size >>= 1

        key = self.readString()

        if key == "":
            # integer indexes only -> python list
            result = []
            self.context.addObject(result)

            for i in xrange(size):
                result.append(self.readElement())

        else:
            # key,value pairs -> python dict
            result = {}
            self.context.addObject(result)

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

        return result

    def _getClassDefinition(self, ref):
        """
        Reads class definition from the stream.
        
        @type ref: 
        @param ref:
        @return:
        @rtype:
        """
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

        @raise DecodeError: The object encoding is unknown.
        @return:
        @rtype:
        """
        ref = self.readInteger()

        if ref & REFERENCE_BIT == 0:
            return self.context.getObject(ref >> 1)

        ref >>= 1

        (class_ref, class_def) = self._getClassDefinition(ref)
        ref >>= 3

        klass = class_def.getClass()

        obj = klass()
        self.context.addObject(obj)

        if class_def.encoding in (ObjectEncoding.EXTERNAL, ObjectEncoding.PROXY):
            class_def.alias.read_func(obj, compat.DataInput(self))
        elif class_def.encoding == ObjectEncoding.DYNAMIC:
            attr = self.readString()

            while attr != "":
                if attr not in class_def.attrs:
                    class_def.attrs.append(attr)

                obj[attr] = self.readElement()
                attr = self.readString()

        elif class_def.encoding == ObjectEncoding.STATIC:
            if not class_ref:
                for i in range(ref):
                    class_def.attrs.append(self.readString())

            for attr in class_def.attrs:
                setattr(obj, attr, self.readElement())
        else:
            raise pyamf.DecodeError("Unknown object encoding")

        return obj

    def readXMLString(self):
        """
        Reads a string from the data stream and converts it into an XML Tree.

        @return:
        @rtype:
        """
        ref = self.readInteger()
        
        if ref & REFERENCE_BIT == 0:
            return self.context.getObject(ref >> 1)

        xmlstring = self.stream.read(ref >> 1)
        
        x = util.ET.XML(xmlstring)
        self.context.addObject(x)

        return x

    def readByteArray(self):
        """
        Reads a string of data from the stream.

        @see: L{ByteArray}
        @note: This is not supported in Actionscript 1.0 and 2.0.
        @return:
        @rtype:
        """
        ref = self.readInteger()

        if ref & REFERENCE_BIT == 0:
            return self.context.getObject(ref >> 1)

        buffer = self.stream.read(ref >> 1)

        try:
            buffer = zlib.decompress(buffer)
            compressed = True
        except zlib.error:
            compressed = False

        obj = ByteArray(buffer)
        obj._was_compressed = compressed

        self.context.addObject(obj)

        return obj

class Encoder(object):
    """
    Encodes an AMF3 data stream.
    """
    #: Python to AMF type mapping.
    type_map = [
        # Unsupported types go first
        ((types.BuiltinFunctionType, types.BuiltinMethodType,), "writeUnsupported"),
        ((bool,), "writeBoolean"),
        ((int,long), "writeInteger"),
        ((float,), "writeNumber"),
        ((ByteArray,), "writeByteArray"),
        ((util.ET.iselement,), "writeXML"),
        ((types.StringTypes,), "writeString"),
        ((datetime.date, datetime.datetime), "writeDate"),
        ((types.NoneType,), "writeNull"),
        ((types.InstanceType,types.ObjectType,), "writeInstance"),
    ]

    def __init__(self, output, context=None):
        """
        Constructs a new AMF3 Encoder.

        Output should be a writable file-like object.

        @type   output: StringIO
        @param  output: file-like object
        @type   context: L{Context}
        @param  context: Context
        """
        self.stream = output

        if context == None:
            self.context = Context()
        elif isinstance(context, Context):
            self.context = context
        else:
            raise TypeError, "context must be of type amf0.Context"

    def writeType(self, type):
        """
        Writes the data type to the stream.

        @type   type: 
        @param  type: ActionScript type
        @raise EncodeError: AMF3 type is not recognized
        """
        if type not in ACTIONSCRIPT_TYPES:
            raise pyamf.EncodeError("Unknown AMF3 type 0x%02x at %d" % (
                type, self.stream.tell() - 1))

        self.stream.write_uchar(type)

    def _writeElementFunc(self, data):
        """
        Gets a function based on the type of data.
        
        @type   data: 
        @param  data: Python data
        @rtype: callable or None
        @return: The function used to encode data to the stream
        """
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

    def writeElement(self, data, use_references=True):
        """
        Writes the data.

        @type   data: mixed
        @param  data: The data to be encoded to the AMF3 data stream 
        """
        func = self._writeElementFunc(data)

        if func is not None:
            func(data, use_references)
        else:
            # XXX nick: Should we be generating a warning here?
            self.writeUnsupported(data)

    def writeNull(self, n, use_references=True):
        """
        Writes a null value to the stream.

        @type   n:
        @param  n: null data
        """
        self.writeType(ASTypes.NULL)

    def writeBoolean(self, n, use_references=True):
        """
        Writes a boolean to the stream.

        @param n:
        @type n: bool
        """
        if n:
            self.writeType(ASTypes.BOOL_TRUE)
        else:
            self.writeType(ASTypes.BOOL_FALSE)

    def _writeInteger(self, n):
        """
        AMF3 integers are encoded.
        
        See U{Parsing Integers on OSFlash
        <http://osflash.org/documentation/amf3/parsing_integers>}
        for more info.

        @type   n:
        @param  n: integer data
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
                self.stream.write_uchar(x | 0x80)

        self.stream.write_uchar(bytes[-1])

    def writeInteger(self, n, use_references=True):
        """
        Writes an integer to the stream.

        @type   n:
        @param  n: integer data
        """
        self.writeType(ASTypes.INTEGER)
        self._writeInteger(n)

    def writeNumber(self, n, use_references=True):
        """
        Writes a non integer to the stream.

        @type   n:
        @param  n: number data
        """
        self.writeType(ASTypes.NUMBER)
        self.stream.write_double(n)

    def _writeString(self, n, use_references=True):
        """
        Writes a raw string to the stream.

        @type   n:
        @param  n: string data
        """
        if len(n) == 0:
            self._writeInteger(REFERENCE_BIT)

            return

        if use_references:
            try:
                ref = self.context.getStringReference(n)
                self._writeInteger(ref << 1)

                return
            except pyamf.ReferenceError:
                self.context.addString(n)

        s = encode_utf8_modified(n)[2:]
        self._writeInteger((len(s) << 1) | REFERENCE_BIT)

        for ch in s:
            self.stream.write_uchar(ord(ch))

    def writeString(self, n, use_references=True):
        """
        Writes a unicode string to the stream.

        @type   n:
        @param  n: string data
        """
        self.writeType(ASTypes.STRING)
        self._writeString(n, use_references)

    def writeDate(self, n, use_references=True):
        """
        Writes a datetime instance to the stream.

        @type n: Instance of L{datetime}
        @param n: Date data
        """
        self.writeType(ASTypes.DATE)

        if use_references is True:
            try:
                ref = self.context.getObjectReference(n)
                self._writeInteger(ref << 1)

                return
            except pyamf.ReferenceError:
                self.context.addObject(n)

        self._writeInteger(REFERENCE_BIT)

        ms = util.get_timestamp(n)
        self.stream.write_double(ms * 1000.0)

    def writeList(self, n, use_references=True):
        """
        Writes a tuple, set or list to the stream.

        @type n: One of __builtin__.tuple, __builtin__.set or __builtin__.list
        @param n: list data
        """
        self.writeType(ASTypes.ARRAY)

        if use_references is True:
            try:
                ref = self.context.getObjectReference(n)
                self._writeInteger(ref << 1)

                return
            except pyamf.ReferenceError:
                self.context.addObject(n)

        self._writeInteger(len(n) << 1 | REFERENCE_BIT)

        self.stream.write_uchar(0x01)

        for x in n:
            self.writeElement(x)

    def writeDict(self, n, use_references=True):
        """
        Writes a dict to the stream.

        @type   n:__builtin__.dict
        @param  n: dict data
        @raise ValueError: non int/str key value found in the C{dict}
        @raise EncodeError: C{dict} contains empty string keys.
        """
        self.writeType(ASTypes.ARRAY)

        if use_references:
            try:
                ref = self.context.getObjectReference(n)
                self._writeInteger(ref << 1)

                return
            except pyamf.ReferenceError:
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

        self.stream.write_uchar(0x01)

        for k in int_keys:
            self.writeElement(n[k])

    def _getClassDefinition(self, obj):
        """
        Read class definition.

        @type   obj:
        @param  obj:
        """
        try:
            alias = pyamf.get_class_alias(obj)
        except pyamf.UnknownClassAlias:
            alias = None

        encoding = ObjectEncoding.STATIC

        if alias:
            if 'dynamic' in alias.metadata:
                encoding = ObjectEncoding.DYNAMIC
            elif 'static' in alias.metadata:
                encoding = ObjectEncoding.STATIC
            elif 'external' in alias.metadata:
                encoding = ObjectEncoding.EXTERNAL
            elif alias.write_func and alias.read_func:
                encoding = ObjectEncoding.EXTERNAL

        class_def = ClassDefinition(alias, encoding)

        if encoding in (ObjectEncoding.STATIC, ObjectEncoding.DYNAMIC):
            if alias is None:
                for k in obj.__dict__.keys():
                    class_def.attrs.append(k)
            else:
                if alias.attrs is None:
                    for k in obj.__dict__.keys():
                        class_def.attrs.append(k)
                else:
                    import copy

                    class_def.attrs = copy.copy(alias.attrs)

        return class_def

    def writeInstance(self, obj, use_references=True):
        if obj.__class__ == dict:
            self.writeDict(obj, use_references)
        elif obj.__class__ in (list, set):
            self.writeList(obj, use_references)
        else:
            self.writeObject(obj, use_references)

    def writeObject(self, obj, use_references=True):
        """
        Writes an object to the stream.

        @type   obj:
        @param  obj:
        @type   use_references:
        @param  use_references:
        @raise EncodeError: Unknown object encoding
        """
        self.writeType(ASTypes.OBJECT)

        if use_references is True:
            try:
                ref = self.context.getObjectReference(obj)
                self._writeInteger(ref << 1)

                return
            except pyamf.ReferenceError:
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

        if class_def.encoding in (ObjectEncoding.EXTERNAL, ObjectEncoding.PROXY):
            class_def.alias.write_func(obj, compat.DataOutput(self))
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
        else:
            raise pyamf.EncodeError("Unknown object encoding")

    def writeByteArray(self, n, use_references=True):
        """
        Writes a L{ByteArray} to the data stream.

        @type   n: L{ByteArray}
        @param  n: data
        """
        self.writeType(ASTypes.BYTEARRAY)

        if use_references:
            try:
                ref = self.context.getObjectReference(n)
                self._writeInteger(ref << 1)

                return
            except pyamf.ReferenceError:
                self.context.addObject(n)

        buf = n.getvalue()

        if n._was_compressed:
            buf = zlib.compress(buf)
            #FIXME nick: hacked
            buf = buf[0] + '\xda' + buf[2:] 

        l = len(buf)
        self._writeInteger(l << 1 | REFERENCE_BIT)
        self.stream.write(buf)

    def writeXML(self, n, use_references=True):
        """
        Writes a XML string to the data stream.

        @type   n: 
        @param  n: XML string
        """
        self.writeType(ASTypes.XMLSTRING)

        if use_references:
            try:
                ref = self.context.getObjectReference(n)
                self._writeInteger(ref << 1)

                return
            except pyamf.ReferenceError:
                self.context.addObject(n)

        self._writeString(util.ET.tostring(n), False)

def encode_utf8_modified(data):
    """
    Encodes a unicode string to Modified UTF-8 data.
    
    @see: U{UTF-8 Java on Wikipedia<http://en.wikipedia.org/wiki/UTF-8#Java>}
    for details.

    @type   data:
    @param  data:
    @return:
    @rtype:
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

def decode_utf8_modified(data):
    """
    Decodes a unicode string from Modified UTF-8 data.

    @type   data:
    @param  data:
    @return: Unicode string
    @rtype: str
    @raise ValueError: Data is not valid modified UTF-8.
    
    @see: U{UTF-8 Java on Wikipedia<http://en.wikipedia.org/wiki/UTF-8#Java>}
    for more details.
    @copyright: Ruby version is Copyright (c) 2006 Ross Bamford (rosco AT roscopeco DOT co DOT uk)
    @note: Ported from U{Ruva
    <http://viewvc.rubyforge.mmmultiworks.com/cgi/viewvc.cgi/trunk/lib/ruva/class.rb>}
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

def decode(stream, context=None):
    """
    A helper function to decode an AMF3 datastream.

    @type   stream: L{BufferedByteStream}
    @param  stream: AMF3 data
    @type   context: L{Context}
    @param  context: Context

    @todo: Add Python 2.3 support.
    """
    decoder = Decoder(stream, context)
    
    for el in decoder.readElement():
        yield el

def encode(element, context=None):
    """
    A helper function to encode an element into AMF3 format.

    @type   element: 
    @param  element:
    @type   context: L{Context}
    @param  context: Context
    @return: Object containing the encoded AMF3 data
    @rtype: StringIO
    """
    buf = util.BufferedByteStream()
    encoder = Encoder(buf, context)

    encoder.writeElement(element)

    return buf
