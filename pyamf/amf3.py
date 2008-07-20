# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
AMF3 implementation.

C{AMF3} is the default serialization for
U{ActionScript<http://en.wikipedia.org/wiki/ActionScript>} 3.0 and provides
various advantages over L{AMF0<pyamf.amf0>}, which is used for ActionScript 1.0
and 2.0. It adds support for sending C{int} and C{uint} objects as integers and
supports data types that are available only in ActionScript 3.0, such as
L{ByteArray} and L{ArrayCollection}.

@see: U{Official AMF3 Specification in English (external)
<http://opensource.adobe.com/wiki/download/attachments/1114283/amf3_spec_121207.pdf>}
@see: U{Official AMF3 Specification in Japanese (external)
<http://opensource.adobe.com/wiki/download/attachments/1114283/JP_amf3_spec_121207.pdf>}
@see: U{AMF3 documentation on OSFlash (external)
<http://osflash.org/documentation/amf3>}

@since: 0.1.0
"""

import types, datetime, zlib

import pyamf
from pyamf import util

try:
    set()
except NameError:
    from sets import Set as set

class ASTypes:
    """
    All AMF3 data types used in ActionScript 3.0.

    AMF represents ActionScript objects by a single byte representing type, and
    then by a type-specific byte array that may be of fixed length, may contain
    length information, or may come with its own end code.

    @see: U{AMF3 data types on OSFlash (external)
    <http://osflash.org/documentation/amf3#data_types>}
    """
    #: The undefined type is represented by the undefined type marker.
    #: No further information is encoded for this value.
    UNDEFINED  = 0x00
    #: The undefined type is represented by the undefined type marker.
    #: No further information is encoded for this value.
    NULL       = 0x01
    #: The false type is represented by the false type marker and is
    #: used to encode a Boolean value of C{false}. No further information
    #: is encoded for this value.
    #: @note: In ActionScript 3.0 the concept of a primitive and Object
    #: form of Boolean does not exist.
    BOOL_FALSE = 0x02
    #: The true type is represented by the true type marker and is
    #: used to encode a Boolean value of C{true}. No further information
    #: is encoded for this value.
    #: @note: In ActionScript 3.0 the concept of a primitive and Object
    #: form of Boolean does not exist.
    BOOL_TRUE  = 0x03
    #: In AMF 3 integers are serialized using a variable length unsigned
    #: 29-bit integer.
    #: @see: U{Parsing Integers on OSFlash (external)
    #: <http://osflash.org/documentation/amf3/parsing_integers>}
    INTEGER    = 0x04
    #: This type is used to encode an ActionScript Number
    #: or an ActionScript C{int} of value greater than or equal to 2^28
    #: or an ActionScript uint of value greater than or equal to 2^29.
    #: The encoded value is is always an 8 byte IEEE-754 double precision
    #: floating point value in network byte order (sign bit in low memory).
    #: The AMF 3 number type is encoded in the same manner as the
    #: AMF 0 L{Number<pyamf.amf0.ASTypes.NUMBER>} type.
    NUMBER     = 0x05
    #: ActionScript String values are represented using a single string
    #: type in AMF 3 - the concept of string and long string types from
    #: AMF 0 is not used. Strings can be sent as a reference to a previously
    #: occurring String by using an index to the implicit string reference
    #: table.
    #: Strings are encoding using UTF-8 - however the header may either
    #: describe a string literal or a string reference.
    STRING     = 0x06
    #: ActionScript 3.0 introduced a new XML type however the legacy
    #: C{XMLDocument} type from ActionScript 1.0 and 2.0.is retained
    #: in the language as C{flash.xml.XMLDocument}. Similar to AMF 0, the
    #: structure of an C{XMLDocument} needs to be flattened into a string
    #: representation for serialization. As with other strings in AMF,
    #: the content is encoded in UTF-8. XMLDocuments can be sent as a reference
    #: to a previously occurring C{XMLDocument} instance by using an index to
    #: the implicit object reference table.
    #: @see: U{OSFlash documentation (external)
    #: <http://osflash.org/documentation/amf3#x07_-_xml_legacy_flash.xml.xmldocument_class>}
    XML        = 0x07
    #: In AMF 3 an ActionScript Date is serialized simply as the number of
    #: milliseconds elapsed since the epoch of midnight, 1st Jan 1970 in the
    #: UTC time zone. Local time zone information is not sent.
    DATE       = 0x08
    #: ActionScript Arrays are described based on the nature of their indices,
    #: i.e. their type and how they are positioned in the Array.
    ARRAY      = 0x09
    #: A single AMF 3 type handles ActionScript Objects and custom user classes.
    OBJECT     = 0x0a
    #: ActionScript 3.0 introduces a new top-level XML class that supports
    #: U{E4X<http://en.wikipedia.org/wiki/E4X>} syntax.
    #: For serialization purposes the XML type needs to be flattened into a
    #: string representation. As with other strings in AMF, the content is
    #: encoded using UTF-8.
    XMLSTRING  = 0x0b
    #: ActionScript 3.0 introduces the L{ByteArray} type to hold an Array
    #: of bytes. AMF 3 serializes this type using a variable length encoding
    #: 29-bit integer for the byte-length prefix followed by the raw bytes
    #: of the L{ByteArray}.
    #: @see: U{Parsing ByteArrays on OSFlash (external)
    #: <http://osflash.org/documentation/amf3/parsing_byte_arrays>}
    BYTEARRAY  = 0x0c

#: List of available ActionScript types in AMF3.
ACTIONSCRIPT_TYPES = []

for x in ASTypes.__dict__:
    if not x.startswith('_'):
        ACTIONSCRIPT_TYPES.append(ASTypes.__dict__[x])
del x

#: Reference bit.
REFERENCE_BIT = 0x01

class ObjectEncoding:
    """
    AMF object encodings.
    """
    #: Property list encoding.
    #: The remaining integer-data represents the number of class members that
    #: exist. The property names are read as string-data. The values are then
    #: read as AMF3-data.
    STATIC = 0x00

    #: Externalizable object.
    #: What follows is the value of the "inner" object, including type code.
    #: This value appears for objects that implement IExternalizable, such as
    #: L{ArrayCollection} and L{ObjectProxy}.
    EXTERNAL = 0x01

    #: Name-value encoding.
    #: The property names and values are encoded as string-data followed by
    #: AMF3-data until there is an empty string property name. If there is a
    #: class-def reference there are no property names and the number of values
    #: is equal to the number of properties in the class-def.
    DYNAMIC = 0x02

    #: Proxy object.
    PROXY = 0x03

class DataOutput(object):
    """
    I am a C{StringIO} type object containing byte data from the AMF stream.
    ActionScript 3.0 introduced the C{flash.utils.ByteArray} class to support
    the manipulation of raw data in the form of an Array of bytes.
    I provide a set of methods for writing binary data with ActionScript 3.0.

    This class is the I/O counterpart to the L{DataInput} class, which reads
    binary data.

    @see: U{IDataOutput on Livedocs (external)
    <http://livedocs.adobe.com/flex/201/langref/flash/utils/IDataOutput.html>}
    """
    def __init__(self, encoder):
        """
        @param encoder: Encoder containing the stream.
        @type encoder: L{amf3.Encoder<pyamf.amf3.Encoder>}
        """
        assert isinstance(encoder, Encoder)

        self.encoder = encoder
        self.stream = encoder.stream

    def writeBoolean(self, value):
        """
        Writes a Boolean value.

        @type value: C{bool}
        @param value: A C{Boolean} value determining which byte is written.
        If the parameter is C{True}, C{1} is written; if C{False}, C{0} is
        written.

        @raise ValueError: Non-boolean value found.
        """
        if isinstance(value, bool):
            if value is True:
                self.stream.write_uchar(1)
            else:
                self.stream.write_uchar(0)
        else:
            raise ValueError("Non-boolean value found")

    def writeByte(self, value):
        """
        Writes a byte.

        @type value: C{int}
        """
        self.stream.write_char(value)

    def writeDouble(self, value):
        """
        Writes an IEEE 754 double-precision (64-bit) floating
        point number.

        @type value: C{number}
        """
        self.stream.write_double(value)

    def writeFloat(self, value):
        """
        Writes an IEEE 754 single-precision (32-bit) floating
        point number.

        @type value: C{float}
        """
        self.stream.write_float(value)

    def writeInt(self, value):
        """
        Writes a 32-bit signed integer.

        @type value: C{int}
        """
        self.stream.write_long(value)

    def writeMultiByte(self, value, charset):
        """
        Writes a multibyte string to the datastream using the
        specified character set.

        @type value: C{str}
        @param value: The string value to be written.
        @type charset: C{str}
        @param charset: The string denoting the character
        set to use. Possible character set strings include
        C{shift-jis}, C{cn-gb}, C{iso-8859-1} and others.
        @see: U{Supported character sets on Livedocs (external)
        <http://livedocs.adobe.com/flex/201/langref/charset-codes.html>}
        """
        self.stream.write(unicode(value).encode(charset))

    def writeObject(self, value, use_references=True):
        """
        Writes an object to data stream in AMF serialized format.

        @param value: The object to be serialized.
        @type use_references: C{bool}
        @param use_references:
        """
        self.encoder.writeElement(value, use_references)

    def writeShort(self, value):
        """
        Writes a 16-bit integer.

        @type value: C{int}
        @param value: A byte value as an integer.
        """
        self.stream.write_short(value)

    def writeUnsignedInt(self, value):
        """
        Writes a 32-bit unsigned integer.

        @type value: C{int}
        @param value: A byte value as an unsigned integer.
        """
        self.stream.write_ulong(value)

    def writeUTF(self, value):
        """
        Writes a UTF-8 string to the data stream.

        The length of the UTF-8 string in bytes is written first,
        as a 16-bit integer, followed by the bytes representing the
        characters of the string.

        @type value: C{str}
        @param value: The string value to be written.
        """
        if not isinstance(value, unicode):
            value = unicode(value, 'utf8')

        buf = util.BufferedByteStream()
        buf.write_utf8_string(value)
        bytes = buf.getvalue()

        self.stream.write_ushort(len(bytes))
        self.stream.write(bytes)

    def writeUTFBytes(self, value):
        """
        Writes a UTF-8 string. Similar to L{writeUTF}, but does
        not prefix the string with a 16-bit length word.

        @type value: C{str}
        @param value: The string value to be written.
        """
        val = None

        if isinstance(value, unicode):
            val = value
        else:
            val = unicode(value, 'utf8')

        self.stream.write_utf8_string(val)

class DataInput(object):
    """
    I provide a set of methods for reading binary data with ActionScript 3.0.

    This class is the I/O counterpart to the L{DataOutput} class,
    which writes binary data.

    @see: U{IDataInput on Livedocs (external)
    <http://livedocs.adobe.com/flex/201/langref/flash/utils/IDataInput.html>}
    """
    def __init__(self, decoder):
        """
        @param decoder: AMF3 decoder containing the stream.
        @type decoder: L{amf3.Decoder<pyamf.amf3.Decoder>}
        """
        assert isinstance(decoder, Decoder)

        self.decoder = decoder
        self.stream = decoder.stream

    def readBoolean(self):
        """
        Read C{Boolean}.

        @raise ValueError: Error reading Boolean.
        @rtype: C{bool}
        @return: A Boolean value, C{True} if the byte
        is nonzero, C{False} otherwise.
        """
        byte = self.stream.read(1)

        if byte == '\x00':
            return False
        elif byte == '\x01':
            return True
        else:
            raise ValueError("Error reading boolean")

    def readByte(self):
        """
        Reads a signed byte.

        @rtype: C{int}
        @return: The returned value is in the range -128 to 127.
        """
        return self.stream.read_char()

    def readDouble(self):
        """
        Reads an IEEE 754 double-precision floating point number from the
        data stream.

        @rtype: C{number}
        @return: An IEEE 754 double-precision floating point number.
        """
        return self.stream.read_double()

    def readFloat(self):
        """
        Reads an IEEE 754 single-precision floating point number from the
        data stream.

        @rtype: C{number}
        @return: An IEEE 754 single-precision floating point number.
        """
        return self.stream.read_float()

    def readInt(self):
        """
        Reads a signed 32-bit integer from the data stream.

        @rtype: C{int}
        @return: The returned value is in the range -2147483648 to 2147483647.
        """
        return self.stream.read_long()

    def readMultiByte(self, length, charset):
        """
        Reads a multibyte string of specified length from the data stream
        using the specified character set.

        @type length: C{int}
        @param length: The number of bytes from the data stream to read.
        @type charset: C{str}
        @param charset: The string denoting the character set to use.

        @rtype: C{str}
        @return: UTF-8 encoded string.
        """
        #FIXME nick: how to work out the code point byte size (on the fly)?
        bytes = self.stream.read(length)

        return unicode(bytes, charset)

    def readObject(self):
        """
        Reads an object from the data stream.

        @return: The deserialized object.
        """
        return self.decoder.readElement()

    def readShort(self):
        """
        Reads a signed 16-bit integer from the data stream.

        @rtype: C{uint}
        @return: The returned value is in the range -32768 to 32767.
        """
        return self.stream.read_short()

    def readUnsignedByte(self):
        """
        Reads an unsigned byte from the data stream.

        @rtype: C{uint}
        @return: The returned value is in the range 0 to 255.
        """
        return self.stream.read_uchar()

    def readUnsignedInt(self):
        """
        Reads an unsigned 32-bit integer from the data stream.

        @rtype: C{uint}
        @return: The returned value is in the range 0 to 4294967295.
        """
        return self.stream.read_ulong()

    def readUnsignedShort(self):
        """
        Reads an unsigned 16-bit integer from the data stream.

        @rtype: C{uint}
        @return: The returned value is in the range 0 to 65535.
        """
        return self.stream.read_ushort()

    def readUTF(self):
        """
        Reads a UTF-8 string from the data stream.

        The string is assumed to be prefixed with an unsigned
        short indicating the length in bytes.

        @rtype: C{str}
        @return: A UTF-8 string produced by the byte
        representation of characters.
        """
        length = self.stream.read_ushort()
        return self.stream.read_utf8_string(length)

    def readUTFBytes(self, length):
        """
        Reads a sequence of C{length} UTF-8 bytes from the data
        stream and returns a string.

        @type length: C{int}
        @param length: The number of bytes from the data stream to read.
        @rtype: C{str}
        @return: A UTF-8 string produced by the byte representation of
        characters of specified C{length}.
        """
        return self.readMultiByte(length, 'utf-8')

class ByteArray(util.BufferedByteStream, DataInput, DataOutput):
    """
    I am a C{StringIO} type object containing byte data from the AMF stream.
    ActionScript 3.0 introduced the C{flash.utils.ByteArray} class to support
    the manipulation of raw data in the form of an Array of bytes.

    Supports C{zlib} compression.

    Possible uses of the C{ByteArray} class:
     - Creating a custom protocol to connect to a client.
     - Writing your own AMF/Remoting packet.
     - Optimizing the size of your data by using custom data types.

    @see: U{ByteArray on Livedocs (external)
    <http://livedocs.adobe.com/flex/201/langref/flash/utils/ByteArray.html>}
    """
    def __init__(self, *args, **kwargs):
        self.context = kwargs.pop('context', Context())

        util.BufferedByteStream.__init__(self, *args, **kwargs)
        DataInput.__init__(self, Decoder(self, self.context))
        DataOutput.__init__(self, Encoder(self, self.context))

        self.compressed = False

    def __cmp__(self, other):
        if isinstance(other, ByteArray):
            return cmp(self.getvalue(), other.getvalue())

        return cmp(self._buffer, other)

    def __str__(self):
        buf = self.getvalue()

        if self.compressed:
            buf = zlib.compress(buf)
            #FIXME nick: hacked
            buf = buf[0] + '\xda' + buf[2:]

        return buf

    def compress(self):
        """
        Forces compression of the underlying stream.
        """
        self.compressed = True

class ClassDefinition(object):
    """
    I contain meta relating to the class definition.

    @ivar alias: The alias to this class definition. If this value is C{None},
        or an empty string, the class is considered to be anonymous.
    @type alias: L{ClassAlias<pyamf.ClassAlias>}
    @ivar encoding: The type of encoding to use when serializing the object.
    @type encoding: C{int}
    """
    def __init__(self, alias, encoding=ObjectEncoding.DYNAMIC):
        if alias in (None, ''):
            self.alias = None
        elif isinstance(alias, pyamf.ClassAlias):
            self.alias = alias
        else:
            self.alias = pyamf.get_class_alias(alias)

        self.encoding = encoding

        if self.alias and self.alias.attrs is not None:
            self.static_attrs = self.alias.attrs
        else:
            self.static_attrs = []

    def _get_name(self):
        if self.alias is None:
            # anonymous class
            return ''

        if 'anonymous' in self.alias.metadata:
            return ''

        return str(self.alias)

    name = property(_get_name)

    def _getClass(self):
        """
        If C{alias} is C{None}, an L{anonymous class<pyamf.ASObject>} is
        returned, otherwise the class is loaded externally.
        """
        if self.alias in (None, ''):
            # anonymous class
            return pyamf.ASObject

        return self.getClassAlias().klass

    def getClassAlias(self):
        """
        Gets the class alias that is held by this definition.

        @see: L{load_class<pyamf.load_class>}.
        @raise UnknownClassAlias: Anonymous class definitions do not have
        class aliases.

        @rtype: L{ClassAlias<pyamf.ClassAlias>}
        @return: Class definition.
        """
        if not hasattr(self, '_alias'):
            if self.name == '':
                raise pyamf.UnknownClassAlias, 'Anonymous class definitions do not have class aliases'

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

    def getAttrs(self, obj):
        """
        Returns a C{tuple} containing a dict of static and dynamic attributes
        for C{obj}.
        """
        attrs = util.get_instance_attrs(obj, self.alias)
        static_attrs = dynamic_attrs = None

        if self.alias:
            if self.alias.attrs:
                static_attrs = {}

                for attr in self.alias.attrs:
                    static_attrs[attr] = getattr(obj, attr)

            if self.alias.attr_func:
                dynamic_attrs = {}

                for attr in self.alias.attr_func(obj):
                    dynamic_attrs[attr] = getattr(obj, attr)
            else:
                dynamic_attrs = attrs
        else:
            dynamic_attrs = attrs

        return (static_attrs, dynamic_attrs)

class Context(pyamf.BaseContext):
    """
    I hold the AMF3 context for en/decoding streams.

    @ivar strings: A list of string references.
    @type strings: C{list}
    @ivar classes: A list of L{ClassDefinition}.
    @type classes: C{list}
    @ivar legacy_xml: A list of legacy encoded XML documents.
    @type legacy_xml: C{list}
    """
    def clear(self):
        """
        Resets the context.
        """
        pyamf.BaseContext.clear(self)

        self.strings = []

        self.classes = []
        self.rev_classes = {}
        self.class_defs = {}
        self.rev_class_defs = {}

        self.legacy_xml = []
        self.rev_legacy_xml = {}

    def getString(self, ref):
        """
        Gets a string based on a reference C{ref}.

        @param ref: The reference index.
        @type ref: C{str}
        @raise ReferenceError: The referenced string could not be found.

        @rtype: C{str}
        @return: The referenced string.
        """
        try:
            return self.strings[ref]
        except IndexError:
            raise pyamf.ReferenceError, "String reference %d not found" % ref

    def getStringReference(self, s):
        """
        Return string reference.

        @type s: C{str}
        @param s: The referenced string.
        @raise ReferenceError: The string reference could not be found.
        @return: The reference index to the string.
        @rtype: C{int}
        """
        try:
            return self.strings.index(s)
        except ValueError:
            raise pyamf.ReferenceError, "Reference for string %r not found" % s

    def addString(self, s):
        """
        Creates a reference to C{s}. If the reference already exists, that
        reference is returned.

        @type s: C{str}
        @param s: The string to be referenced.
        @rtype: C{int}
        @return: The reference index.

        @raise TypeError: The parameter C{s} is not of C{basestring} type.
        @raise ValueError: Trying to store a reference to an empty string.
        """
        if not isinstance(s, basestring):
            raise TypeError

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

        @raise ReferenceError: The class reference could not be found.
        @return: Class reference.
        """
        try:
            return self.classes[ref]
        except IndexError:
            raise pyamf.ReferenceError, "Class reference %d not found" % ref

    def getClassDefinitionReference(self, class_def):
        """
        Return class definition reference.

        @type class_def: L{ClassDefinition} or C{instance} or C{class}
        @param class_def: The class definition reference to be found.
        @raise ReferenceError: The reference could not be found.
        @raise TypeError: Unable to determine class.
        @return: The reference to C{class_def}.
        @rtype: C{int}
        """
        if not isinstance(class_def, ClassDefinition):
            if isinstance(class_def, (type, types.ClassType)):
                try:
                    return self.rev_class_defs[class_def]
                except KeyError:
                    raise pyamf.ReferenceError("Reference for class definition for %s not found" %
                        class_def)
            elif isinstance(class_def, (types.InstanceType, types.ObjectType)):
                try:
                    return self.class_defs[class_def.__class__]
                except KeyError:
                    raise pyamf.ReferenceError("Reference for class definition for %s not found" %
                        class_def.__class__)

            raise TypeError, 'unable to determine class for %r' % class_def
        else:
            try:
                return self.rev_class_defs[id(class_def)]
            except ValueError:
                raise pyamf.ReferenceError, "Reference for class %s not found" % class_def.klass

    def addClassDefinition(self, class_def):
        """
        Creates a reference to C{class_def}.
        """
        try:
            return self.rev_class_defs[id(class_def)]
        except KeyError:
            self.classes.append(class_def)
            idx = len(self.classes) - 1

            self.rev_classes[id(class_def)] = idx
            self.class_defs[class_def.__class__] = class_def
            self.rev_class_defs[id(class_def.__class__)] = idx

            return idx

    def removeClassDefinition(self, class_def):
        del self.rev_classes[id(class_def)]
        del self.rev_class_defs[id(class_def.__class__)]
        del self.class_defs[class_def.__class__]

    def getLegacyXML(self, ref):
        """
        Return the legacy XML reference. This is the C{flash.xml.XMLDocument}
        class in ActionScript 3.0 and the top-level C{XML} class in
        ActionScript 1.0 and 2.0.

        @type ref: C{int}
        @param ref: The reference index.
        @raise ReferenceError: The reference could not be found.
        @return: Instance of L{ET<util.ET>}
        """
        try:
            return self.legacy_xml[ref]
        except IndexError:
            raise pyamf.ReferenceError(
                "Legacy XML reference %d not found" % ref)

    def getLegacyXMLReference(self, doc):
        """
        Return legacy XML reference.

        @type doc: L{ET<util.ET>}
        @param doc: The XML document to reference.
        @raise ReferenceError: The reference could not be found.
        @return: The reference to C{doc}.
        @rtype: C{int}
        """
        try:
            return self.rev_legacy_xml[id(doc)]
        except KeyError:
            raise pyamf.ReferenceError, "Reference for document %r not found" % doc

    def addLegacyXML(self, doc):
        """
        Creates a reference to C{doc}.

        If C{doc} is already referenced that index will be returned. Otherwise
        a new index will be created.

        @type doc: L{ET<util.ET>}
        @param doc: The XML document to reference.
        @rtype: C{int}
        @return: The reference to C{doc}.
        """
        try:
            return self.rev_legacy_xml[id(doc)]
        except KeyError:
            self.legacy_xml.append(doc)

            idx = len(self.legacy_xml) - 1
            self.rev_legacy_xml[id(doc)] = idx

            return idx

    def __copy__(self):
        return self.__class__()

class Decoder(pyamf.BaseDecoder):
    """
    Decodes an AMF3 data stream.
    """
    context_class = Context

    type_map = {
        ASTypes.UNDEFINED:  'readUndefined',
        ASTypes.NULL:       'readNull',
        ASTypes.BOOL_FALSE: 'readBoolFalse',
        ASTypes.BOOL_TRUE:  'readBoolTrue',
        ASTypes.INTEGER:    'readSignedInteger',
        ASTypes.NUMBER:     'readNumber',
        ASTypes.STRING:     'readString',
        ASTypes.XML:        'readXML',
        ASTypes.DATE:       'readDate',
        ASTypes.ARRAY:      'readArray',
        ASTypes.OBJECT:     'readObject',
        ASTypes.XMLSTRING:  'readXMLString',
        ASTypes.BYTEARRAY:  'readByteArray',
    }

    def readType(self):
        """
        Read and returns the next byte in the stream and determine its type.

        @raise DecodeError: AMF3 type not recognized.
        @return: AMF3 type.
        @rtype: C{int}
        """
        type = self.stream.read_uchar()

        if type not in ACTIONSCRIPT_TYPES:
            raise pyamf.DecodeError, "Unknown AMF3 type 0x%02x at %d" % (type, self.stream.tell() - 1)

        return type

    def readUndefined(self):
        """
        Read undefined.
        """
        return pyamf.Undefined

    def readNull(self):
        """
        Read null.

        @return: C{None}
        @rtype: C{None}
        """
        return None

    def readBoolFalse(self):
        """
        Returns C{False}.

        @return: C{False}
        @rtype: C{bool}
        """
        return False

    def readBoolTrue(self):
        """
        Returns C{True}.

        @return: C{True}
        @rtype: C{bool}
        """
        return True

    def readNumber(self):
        """
        Read number.
        """
        return self.stream.read_double()

    def readUnsignedInteger(self):
        """
        Reads and returns an unsigned integer from the stream.
        """
        return self.readInteger(False)

    def readSignedInteger(self):
        """
        Reads and returns a signed integer from the stream.
        """
        return self.readInteger(True)

    def readInteger(self, signed=False):
        """
        Reads and returns an integer from the stream.

	@type signed: C{bool}
        @see: U{Parsing integers on OSFlash
        <http://osflash.org/amf3/parsing_integers>} for the AMF3 integer data
        format.
        """
        n = result = 0
        b = self.stream.read_uchar()

        while b & 0x80 != 0 and n < 3:
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

            if result & 0x10000000 != 0:
                if signed:
                    result -= 0x20000000
                else:
                    result <<= 1
                    result += 1

        return result

    def readString(self, use_references=True):
        """
        Reads and returns a string from the stream.

        @type use_references: C{bool}
        """
        def readLength():
            x = self.readUnsignedInteger()

            return (x >> 1, x & REFERENCE_BIT == 0)

        length, is_reference = readLength()

        if use_references and is_reference:
            return self.context.getString(length)

        buf = self.stream.read(length)
        result = unicode(buf, "utf8")

        if len(result) != 0 and use_references:
            self.context.addString(result)

        return result

    def readDate(self):
        """
        Read date from the stream.

        The timezone is ignored as the date is always in UTC.
        """
        ref = self.readUnsignedInteger()

        if ref & REFERENCE_BIT == 0:
            return self.context.getObject(ref >> 1)

        ms = self.stream.read_double()
        result = util.get_datetime(ms / 1000.0)

        self.context.addObject(result)

        return result

    def readArray(self):
        """
        Reads an array from the stream.

        @warning: There is a very specific problem with AMF3 where the first
        three bytes of an encoded empty C{dict} will mirror that of an encoded
        C{{'': 1, '2': 2}}

        @see: U{Docuverse blog (external)
        <http://www.docuverse.com/blog/donpark/2007/05/14/flash-9-amf3-bug>}
        """
        size = self.readUnsignedInteger()

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
            result = pyamf.MixedArray()
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
        """
        class_ref = ref & REFERENCE_BIT == 0

        ref >>= 1

        if class_ref:
            class_def = self.context.getClassDefinition(ref)
        else:
            class_def = ClassDefinition(self.readString(), encoding=ref & 0x03)
            self.context.addClassDefinition(class_def)

        return class_ref, class_def, ref >> 2

    def readObject(self):
        """
        Reads an object from the stream.

        @raise pyamf.EncodeError: Decoding an object in amf3 tagged as amf0
            only is not allowed.
        @raise pyamf.DecodeError: Unknown object encoding.
        """
        def readStatic(is_ref, class_def, obj, num_attrs):
            if not is_ref:
                for i in range(num_attrs):
                    key = self.readString()

                    class_def.static_attrs.append(key)

            for attr in class_def.static_attrs:
                setattr(obj, attr, self.readElement())

        def readDynamic(is_ref, class_def, obj):
            attr = self.readString()

            while attr != "":
                setattr(obj, attr, self.readElement())
                attr = self.readString()

        ref = self.readUnsignedInteger()

        if ref & REFERENCE_BIT == 0:
            return self.context.getObject(ref >> 1)

        ref >>= 1

        class_ref, class_def, num_attrs = self._getClassDefinition(ref)

        if class_def.alias and 'amf0' in class_def.alias.metadata:
            raise pyamf.EncodeError, "Decoding an object in amf3 tagged as amf0 only is not allowed"

        if class_def.alias:
            obj = class_def.alias()
        else:
            klass = class_def.getClass()
            obj = klass()

        obj_attrs = pyamf.ASObject()
        self.context.addObject(obj)

        if class_def.encoding in (ObjectEncoding.EXTERNAL, ObjectEncoding.PROXY):
            obj.__readamf__(DataInput(self))
        elif class_def.encoding == ObjectEncoding.DYNAMIC:
            readStatic(class_ref, class_def, obj_attrs, num_attrs)
            readDynamic(class_ref, class_def, obj_attrs)
        elif class_def.encoding == ObjectEncoding.STATIC:
            readStatic(class_ref, class_def, obj_attrs, num_attrs)
        else:
            raise pyamf.DecodeError, "Unknown object encoding"

        if hasattr(obj, '__setstate__'):
            obj.__setstate__(obj_attrs)
        else:
            for k, v in obj_attrs.iteritems():
                setattr(obj, k, v)

        return obj

    def _readXML(self, legacy=False):
        """
        Reads an object from the stream.

        @type legacy: C{bool}
        @param legacy: The read XML is in 'legacy' format.
        """
        ref = self.readUnsignedInteger()

        if ref & REFERENCE_BIT == 0:
            return self.context.getObject(ref >> 1)

        xmlstring = self.stream.read(ref >> 1)

        x = util.ET.XML(xmlstring)
        self.context.addObject(x)

        if legacy is True:
            self.context.addLegacyXML(x)

        return x

    def readXMLString(self):
        """
        Reads a string from the data stream and converts it into
        an XML Tree.

        @return: The XML Document.
        @rtype: L{ET<util.ET>}
        """
        return self._readXML()

    def readXML(self):
        """
        Read a legacy XML Document from the stream.

        @return: The XML Document.
        @rtype: L{ET<util.ET>}
        """
        return self._readXML(True)

    def readByteArray(self):
        """
        Reads a string of data from the stream.

        Detects if the L{ByteArray} was compressed using C{zlib}.

        @see: L{ByteArray}
        @note: This is not supported in ActionScript 1.0 and 2.0.
        """
        ref = self.readUnsignedInteger()

        if ref & REFERENCE_BIT == 0:
            return self.context.getObject(ref >> 1)

        buffer = self.stream.read(ref >> 1)

        try:
            buffer = zlib.decompress(buffer)
            compressed = True
        except zlib.error:
            compressed = False

        obj = ByteArray(buffer, context=self.context)
        obj.compressed = compressed

        self.context.addObject(obj)

        return obj

class Encoder(pyamf.BaseEncoder):
    """
    Encodes an AMF3 data stream.
    """
    context_class = Context

    type_map = [
        ((types.BuiltinFunctionType, types.BuiltinMethodType,
            types.FunctionType, types.GeneratorType, types.ModuleType,
            types.LambdaType, types.MethodType), "writeFunc"),
        ((bool,), "writeBoolean"),
        ((types.NoneType,), "writeNull"),
        ((int,long), "writeInteger"),
        ((float,), "writeNumber"),
        ((types.StringTypes,), "writeString"),
        ((ByteArray,), "writeByteArray"),
        ((datetime.date, datetime.datetime), "writeDate"),
        ((util.ET._ElementInterface,), "writeXML"),
        ((lambda x: x is pyamf.Undefined,), "writeUndefined"),
        ((types.InstanceType, types.ObjectType,), "writeInstance"),
    ]

    def writeElement(self, data, use_references=True):
        """
        Writes the data.

        @type   data: C{mixed}
        @param  data: The data to be encoded to the AMF3 data stream.
        @type   use_references: C{bool}
        @param  use_references: Default is C{True}.
        @raise EncodeError: Cannot find encoder func for C{data}.
        @raise EncodeError: Unable to encode data.
        """
        func = self._writeElementFunc(data)

        if func is None:
            raise pyamf.EncodeError("Cannot find encoder func for %r" % (data,))
        else:
            try:
                if isinstance(func, pyamf.CustomTypeFunc):
                    func(data)
                else:
                    func(data, use_references=use_references)
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                raise pyamf.EncodeError, "Unable to encode '%r'" % data

    def writeType(self, type):
        """
        Writes the data type to the stream.

        @param type: ActionScript type.
        @raise EncodeError: AMF3 type is not recognized.
        @see: L{ACTIONSCRIPT_TYPES}
        """
        if type not in ACTIONSCRIPT_TYPES:
            raise pyamf.EncodeError("Unknown AMF3 type 0x%02x at %d" % (
                type, self.stream.tell() - 1))

        self.stream.write_uchar(type)

    def writeUndefined(self, d, use_references=True):
        """
        Writes an C{pyamf.Undefined} value to the stream.

        @param d: The C{undefined} data to be encoded to the AMF3 data stream.
        @type use_references: C{bool}
        @param use_references: Default is C{True}.
        """
        self.writeType(ASTypes.UNDEFINED)

    def writeNull(self, n, use_references=True):
        """
        Writes a C{null} value to the stream.

        @param n: The C{null} data to be encoded to the AMF3 data stream. 
        @type n: C{null} data.
        @type use_references: C{bool}
        @param use_references: Default is C{True}.
        """
        self.writeType(ASTypes.NULL)

    def writeBoolean(self, n, use_references=True):
        """
        Writes a Boolean to the stream.

        @param n: The C{boolean} data to be encoded to the AMF3 data stream.
        @type n: C{bool}
        @type   use_references: C{bool}
        @param  use_references: Default is C{True}.
        """
        if n:
            self.writeType(ASTypes.BOOL_TRUE)
        else:
            self.writeType(ASTypes.BOOL_FALSE)

    def _writeInteger(self, n):
        """
        AMF3 integers are encoded.

        @param n: The integer data to be encoded to the AMF3 data stream.
        @type n: integer data
        
        @see: U{Parsing Integers on OSFlash
        <http://osflash.org/documentation/amf3/parsing_integers>}
        for more info.
        """
        self.stream.write(_encode_int(n))

    def writeInteger(self, n, use_references=True):
        """
        Writes an integer to the stream.

        @type   n: integer data
        @param  n: The integer data to be encoded to the AMF3 data stream.
        @type   use_references: C{bool}
        @param  use_references: Default is C{True}.
        """
        if n & 0xf0000000 not in [0, 0xf0000000]:
            self.writeNumber(n)

            return

        self.writeType(ASTypes.INTEGER)
        self.stream.write(_encode_int(n))

    def writeNumber(self, n, use_references=True):
        """
        Writes a non integer to the stream.

        @type   n: number data
        @param  n: The number data to be encoded to the AMF3 data stream.
        @type   use_references: C{bool}
        @param  use_references: Default is C{True}
        """
        self.writeType(ASTypes.NUMBER)
        self.stream.write_double(n)

    def _writeString(self, n, use_references=True):
        """
        Writes a raw string to the stream.

        @type   n: C{str} or C{unicode}
        @param  n: The string data to be encoded to the AMF3 data stream.
        @type   use_references: C{bool}
        @param  use_references: Default is C{True}.
        """
        if not isinstance(n, basestring):
            bytes = unicode(n).encode('utf8')
            n = bytes
        elif isinstance(n, unicode):
            bytes = n.encode('utf8')
        else:
            bytes = n

        if len(bytes) == 0:
            self._writeInteger(REFERENCE_BIT)

            return

        if use_references:
            try:
                ref = self.context.getStringReference(n)
                self._writeInteger(ref << 1)

                return
            except pyamf.ReferenceError:
                self.context.addString(n)

        self._writeInteger((len(bytes) << 1) | REFERENCE_BIT)
        self.stream.write(bytes)

    def writeString(self, n, use_references=True):
        """
        Writes a string to the stream. If C{n} is not a unicode string, an
        attempt will be made to convert it.

        @type   n: C{basestring}
        @param  n: The string data to be encoded to the AMF3 data stream.
        @type   use_references: C{bool}
        @param  use_references: Default is C{True}.
        """
        self.writeType(ASTypes.STRING)
        self._writeString(n, use_references)

    def writeDate(self, n, use_references=True):
        """
        Writes a C{datetime} instance to the stream.

        @type n: L{datetime}
        @param n: The C{Date} data to be encoded to the AMF3 data stream.
        @type   use_references: C{bool}
        @param  use_references: Default is C{True}.
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
        Writes a C{tuple}, C{set} or C{list} to the stream.

        @type n: One of C{__builtin__.tuple}, C{__builtin__.set}
            or C{__builtin__.list}
        @param n: The C{list} data to be encoded to the AMF3 data stream.
        @type use_references: C{bool}
        @param use_references: Default is C{True}.
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
        Writes a C{dict} to the stream.

        @type n: C{__builtin__.dict}
        @param n: The C{dict} data to be encoded to the AMF3 data stream.
        @type use_references: C{bool}
        @param use_references: Default is C{True}.
        @raise ValueError: Non C{int}/C{str} key value found in the C{dict}
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
                raise ValueError, "Non int/str key value found in dict"

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
                raise pyamf.EncodeError, "dicts cannot contain empty string keys"

            self._writeString(x)
            self.writeElement(n[x])

        self.stream.write_uchar(0x01)

        for k in int_keys:
            self.writeElement(n[k])

    def _getClassDefinition(self, obj):
        """
        Builds a class definition based on the C{obj}.

        @raise pyamf.EncodeError: Unable to determine object attributes.
        """
        encoding = ObjectEncoding.DYNAMIC

        alias = self.context.getClassAlias(obj.__class__)

        if alias:
            if 'dynamic' in alias.metadata:
                encoding = ObjectEncoding.DYNAMIC
            elif 'static' in alias.metadata:
                encoding = ObjectEncoding.STATIC
            elif 'external' in alias.metadata:
                encoding = ObjectEncoding.EXTERNAL

        class_def = ClassDefinition(alias, encoding)

        if alias and encoding == ObjectEncoding.STATIC:
            if alias.attrs is not None:
                import copy

                class_def.static_attrs = copy.copy(alias.attrs)
            else:
                if hasattr(obj, 'keys'):
                    for k in obj.keys():
                        class_def.static_attrs.append(unicode(k))
                elif hasattr(obj, 'iteritems'):
                    for k, v in obj.iteritems():
                        class_def.static_attrs.append(unicode(k))
                elif hasattr(obj, '__dict__'):
                    for k in obj.__dict__.keys():
                        class_def.static_attrs.append(unicode(k))
                else:
                    raise pyamf.EncodeError, 'Unable to determine object attributes'

        return class_def

    def writeInstance(self, obj, use_references=True):
        """
        Read class definition.

        @param obj: The class instance data to be encoded to the AMF3
            data stream.
        @type obj: instance data
        @type use_references: C{bool}
        @param use_references: Default is C{True}.
        """
        if obj.__class__ == pyamf.MixedArray:
            self.writeDict(obj, use_references)
        elif obj.__class__ in (list, set, tuple):
            self.writeList(obj, use_references)
        else:
            self.writeObject(obj, use_references)

    def writeObject(self, obj, use_references=True):
        """
        Writes an object to the stream.

        @param obj: The object data to be encoded to the AMF3 data stream.
        @type obj: object data
        @param use_references: Default is C{True}.
        @type use_references: C{bool}
        @raise EncodeError: Encoding an object in amf3 tagged as amf0 only.
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
            self.context.addClassDefinition(class_def)
            class_ref = False
            ref = 0

            if class_def.alias and 'amf0' in class_def.alias.metadata:
                raise pyamf.EncodeError, "Encoding an object in amf3 tagged as amf0 only"

            if class_def.encoding != ObjectEncoding.EXTERNAL:
                if class_def.alias and class_def.alias.attrs is not None:
                    ref += len(class_def.alias.attrs) << 4

            self._writeInteger(ref | class_def.encoding << 2 | REFERENCE_BIT << 1 | REFERENCE_BIT)
            self._writeString(class_def.name)
        else:
            class_def = self._getClassDefinition(obj)

        if class_def.encoding in (ObjectEncoding.EXTERNAL, ObjectEncoding.PROXY):
            obj.__writeamf__(DataOutput(self))
        else:
            static_attrs, dynamic_attrs = class_def.getAttrs(obj)

            if static_attrs is not None:
                if not class_ref:
                    [self._writeString(attr) for attr in static_attrs.keys()]
                    [self.writeElement(attr) for attr in static_attrs.values()]

            if class_def.encoding == ObjectEncoding.DYNAMIC and dynamic_attrs is not None:
                for attr, value in dynamic_attrs.iteritems():
                    self._writeString(attr)
                    self.writeElement(value)

                self._writeString("")

    def writeByteArray(self, n, use_references=True):
        """
        Writes a L{ByteArray} to the data stream.

        @type   n: L{ByteArray}
        @param  n: The L{ByteArray} data to be encoded to the AMF3 data stream.
        @type   use_references: C{bool}
        @param  use_references: Default is C{True}.
        """
        self.writeType(ASTypes.BYTEARRAY)

        if use_references:
            try:
                ref = self.context.getObjectReference(n)
                self._writeInteger(ref << 1)

                return
            except pyamf.ReferenceError:
                self.context.addObject(n)

        buf = str(n)
        l = len(buf)
        self._writeInteger(l << 1 | REFERENCE_BIT)
        self.stream.write(buf)

    def writeXML(self, n, use_references=True):
        """
        Writes a XML string to the data stream.

        @type   n: L{ET<util.ET>}
        @param  n: The XML Document to be encoded to the AMF3 data stream.
        @type   use_references: C{bool}
        @param  use_references: Default is C{True}.
        """
        try:
            self.context.getLegacyXMLReference(n)
            is_legacy = True
        except pyamf.ReferenceError:
            is_legacy = False

        if is_legacy is True:
            self.writeType(ASTypes.XML)
        else:
            self.writeType(ASTypes.XMLSTRING)

        if use_references:
            try:
                ref = self.context.getObjectReference(n)
                self._writeInteger(ref << 1)

                return
            except pyamf.ReferenceError:
                self.context.addObject(n)

        self._writeString(util.ET.tostring(n, 'utf-8'), False)

def decode(stream, context=None):
    """
    A helper function to decode an AMF3 datastream.

    @type   stream: L{BufferedByteStream<util.BufferedByteStream>}
    @param  stream: AMF3 data.
    @type   context: L{Context}
    @param  context: Context.
    """
    decoder = Decoder(stream, context)

    while 1:
        try:
            yield decoder.readElement()
        except pyamf.EOStream:
            break

def encode(*args, **kwargs):
    """
    A helper function to encode an element into AMF3 format.

    @type args: List of args to encode.
    @keyword context: Any initial context to use.
    @type context: L{Context}
    @return: C{StringIO} type object containing the encoded AMF3 data.
    @rtype: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
    """
    context = kwargs.get('context', None)
    buf = util.BufferedByteStream()
    encoder = Encoder(buf, context)

    for element in args:
        encoder.writeElement(element)

    return buf

def _encode_int(n):
    """
    @raise ValueError: Out of range.
    """
    if n & 0xf0000000 not in [0, 0xf0000000]:
        raise ValueError, "Out of range"

    bytes = ''
    real_value = None

    if n < 0:
        n += 0x20000000

    if n > 0x1fffff:
        real_value = n
        n >>= 1
        bytes += chr(0x80 | ((n >> 21) & 0xff))

    if n > 0x3fff:
        bytes += chr(0x80 | ((n >> 14) & 0xff))

    if n > 0x7f:
        bytes += chr(0x80 | ((n >> 7) & 0xff))

    if real_value is not None:
        n = real_value

    if n > 0x1fffff:
        bytes += chr(n & 0xff)
    else:
        bytes += chr(n & 0x7f)

    return bytes
