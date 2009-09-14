# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.

"""
AMF3 implementation.

C{AMF3} is the default serialization for
U{ActionScript<http://en.wikipedia.org/wiki/ActionScript>} 3.0 and provides
various advantages over L{AMF0<pyamf.amf0>}, which is used for ActionScript 1.0
and 2.0. It adds support for sending C{int} and C{uint} objects as integers and
supports data types that are available only in ActionScript 3.0, such as
L{ByteArray} and L{ArrayCollection}.

@see: U{Official AMF3 Specification in English (external)
<http://opensource.adobe.com/wiki/download/attachments/1114283/amf3_spec_05_05_08.pdf>}
@see: U{Official AMF3 Specification in Japanese (external)
<http://opensource.adobe.com/wiki/download/attachments/1114283/JP_amf3_spec_121207.pdf>}
@see: U{AMF3 documentation on OSFlash (external)
<http://osflash.org/documentation/amf3>}

@since: 0.1
"""

import types
import datetime
import zlib

import pyamf
from pyamf import util
from pyamf.flex import ObjectProxy, ArrayCollection

#: If True encode/decode lists/tuples to L{ArrayCollections<ArrayCollection>}
#: and dicts to L{ObjectProxy}
use_proxies_default = False

try:
    set()
except NameError:
    from sets import Set as set


#: The undefined type is represented by the undefined type marker. No further
#: information is encoded for this value.
TYPE_UNDEFINED = '\x00'
#: The null type is represented by the null type marker. No further
#: information is encoded for this value.
TYPE_NULL = '\x01'
#: The false type is represented by the false type marker and is used to
#: encode a Boolean value of C{false}. No further information is encoded for
#: this value.
TYPE_BOOL_FALSE = '\x02'
#: The true type is represented by the true type marker and is used to encode
#: a Boolean value of C{true}. No further information is encoded for this
#: value.
TYPE_BOOL_TRUE = '\x03'
#: In AMF 3 integers are serialized using a variable length signed 29-bit
#: integer.
#: @see: U{Parsing Integers on OSFlash (external)
#: <http://osflash.org/documentation/amf3/parsing_integers>}
TYPE_INTEGER = '\x04'
#: This type is used to encode an ActionScript Number or an ActionScript
#: C{int} of value greater than or equal to 2^28 or an ActionScript uint of
#: value greater than or equal to 2^29. The encoded value is is always an 8
#: byte IEEE-754 double precision floating point value in network byte order
#: (sign bit in low memory). The AMF 3 number type is encoded in the same
#: manner as the AMF 0 L{Number<pyamf.amf0.TYPE_NUMBER>} type.
TYPE_NUMBER = '\x05'
#: ActionScript String values are represented using a single string type in
#: AMF 3 - the concept of string and long string types from AMF 0 is not used.
#: Strings can be sent as a reference to a previously occurring String by
#: using an index to the implicit string reference table. Strings are encoding
#: using UTF-8 - however the header may either describe a string literal or a
#: string reference.
TYPE_STRING = '\x06'
#: ActionScript 3.0 introduced a new XML type however the legacy C{XMLDocument}
#: type from ActionScript 1.0 and 2.0.is retained in the language as
#: C{flash.xml.XMLDocument}. Similar to AMF 0, the structure of an
#: C{XMLDocument} needs to be flattened into a string representation for
#: serialization. As with other strings in AMF, the content is encoded in
#: UTF-8. XMLDocuments can be sent as a reference to a previously occurring
#: C{XMLDocument} instance by using an index to the implicit object reference
#: table.
#: @see: U{OSFlash documentation (external)
#: <http://osflash.org/documentation/amf3#x07_-_xml_legacy_flash.xml.xmldocument_class>}
TYPE_XML = '\x07'
#: In AMF 3 an ActionScript Date is serialized simply as the number of
#: milliseconds elapsed since the epoch of midnight, 1st Jan 1970 in the
#: UTC time zone. Local time zone information is not sent.
TYPE_DATE = '\x08'
#: ActionScript Arrays are described based on the nature of their indices,
#: i.e. their type and how they are positioned in the Array.
TYPE_ARRAY = '\x09'
#: A single AMF 3 type handles ActionScript Objects and custom user classes.
TYPE_OBJECT = '\x0A'
#: ActionScript 3.0 introduces a new top-level XML class that supports
#: U{E4X<http://en.wikipedia.org/wiki/E4X>} syntax.
#: For serialization purposes the XML type needs to be flattened into a
#: string representation. As with other strings in AMF, the content is
#: encoded using UTF-8.
TYPE_XMLSTRING = '\x0B'
#: ActionScript 3.0 introduces the L{ByteArray} type to hold an Array
#: of bytes. AMF 3 serializes this type using a variable length encoding
#: 29-bit integer for the byte-length prefix followed by the raw bytes
#: of the L{ByteArray}.
#: @see: U{Parsing ByteArrays on OSFlash (external)
#: <http://osflash.org/documentation/amf3/parsing_byte_arrays>}
TYPE_BYTEARRAY = '\x0C'

#: Reference bit.
REFERENCE_BIT = 0x01

#: The maximum that can be represented by an signed 29 bit integer.
MAX_29B_INT = 0x0FFFFFFF

#: The minimum that can be represented by an signed 29 bit integer.
MIN_29B_INT = -0x10000000

ENCODED_INT_CACHE = {}


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

    def writeUnsignedByte(self, value):
        """
        Writes an unsigned byte.

        @type value: C{int}
        @since: 0.5
        """
        return self.stream.write_uchar(value)

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
        @param charset: The string denoting the character set to use. Possible
            character set strings include C{shift-jis}, C{cn-gb},
            C{iso-8859-1} and others.
        @see: U{Supported character sets on Livedocs (external)
            <http://livedocs.adobe.com/flex/201/langref/charset-codes.html>}
        """
        self.stream.write(unicode(value).encode(charset))

    def writeObject(self, value, use_references=True, use_proxies=None):
        """
        Writes an object to data stream in AMF serialized format.

        @param value: The object to be serialized.
        @type use_references: C{bool}
        @param use_references:
        """
        self.encoder.writeElement(value, use_references, use_proxies)

    def writeShort(self, value):
        """
        Writes a 16-bit integer.

        @type value: C{int}
        @param value: A byte value as an integer.
        """
        self.stream.write_short(value)

    def writeUnsignedShort(self, value):
        """
        Writes a 16-bit unsigned integer.

        @type value: C{int}
        @param value: A byte value as an integer.
        @since: 0.5
        """
        self.stream.write_ushort(value)

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

    class __amf__:
        amf3 = True

    def __init__(self, *args, **kwargs):
        self.context = kwargs.pop('context', Context())

        util.BufferedByteStream.__init__(self, *args, **kwargs)
        DataInput.__init__(self, Decoder(self, self.context))
        DataOutput.__init__(self, Encoder(self, self.context))

        self.compressed = False

    def __cmp__(self, other):
        if isinstance(other, ByteArray):
            return cmp(self.getvalue(), other.getvalue())

        return cmp(self.getvalue(), other)

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
    """

    def __init__(self, alias):
        self.alias = alias
        self.reference = None

        alias.compile()

        self.attr_len = 0

        if alias.static_attrs:
            self.attr_len = len(alias.static_attrs)

        self.encoding = ObjectEncoding.DYNAMIC

        if alias.external:
            self.encoding = ObjectEncoding.EXTERNAL
        elif not alias.dynamic:
            if alias.static_attrs == alias.encodable_properties:
                self.encoding = ObjectEncoding.STATIC

    def __repr__(self):
        return '<%s.ClassDefinition reference=%r encoding=%r alias=%r at 0x%x>' % (
            self.__class__.__module__, self.reference, self.encoding, self.alias, id(self))


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

    def __init__(self, exceptions=True):
        self.strings = util.IndexedCollection(use_hash=True, exceptions=False)
        self.classes = {}
        self.class_ref = {}
        self.legacy_xml = util.IndexedCollection(exceptions=False)
        self.object_aliases = util.IndexedMap(exceptions=False) # Maps one object to another

        self.class_idx = 0

        pyamf.BaseContext.__init__(self, exceptions=exceptions)

    def clear(self):
        """
        Clears the context.
        """
        pyamf.BaseContext.clear(self)

        self.strings.clear()
        self.classes = {}
        self.class_ref = {}
        self.legacy_xml.clear()
        self.object_aliases.clear()

        self.class_idx = 0

    def setObjectAlias(self, obj, alias):
        """
        Maps an object to an aliased object.

        @since: 0.4
        """
        self.object_aliases.map(obj, alias)

    def getObjectAlias(self, obj):
        """
        Get an alias of an object.

        @since: 0.4
        @raise pyamf.ReferenceError: Unknown object alias.
        @raise pyamf.ReferenceError: Unknown mapped alias.
        """
        ref = self.object_aliases.getReferenceTo(obj)

        if ref is None:
            if self.exceptions is False:
                return None

            raise pyamf.ReferenceError('Unknown object alias for %r' % (obj,))

        mapped = self.object_aliases.getMappedByReference(ref)

        if mapped is None:
            if self.exceptions is False:
                return None

            raise pyamf.ReferenceError('Unknown mapped alias for %r' % (obj,))

        return mapped

    def getString(self, ref):
        """
        Gets a string based on a reference C{ref}.

        @param ref: The reference index.
        @type ref: C{str}
        @raise pyamf.ReferenceError: The referenced string could not be found.

        @rtype: C{str}
        @return: The referenced string.
        """
        i = self.strings.getByReference(ref)

        if i is None and self.exceptions:
            raise pyamf.ReferenceError("String reference %r not found" % (ref,))

        return i

    def getStringReference(self, s):
        """
        Return string reference.

        @type s: C{str}
        @param s: The referenced string.
        @raise pyamf.ReferenceError: The string reference could not be found.
        @return: The reference index to the string.
        @rtype: C{int}
        """
        i = self.strings.getReferenceTo(s)

        if i is None and self.exceptions:
            raise pyamf.ReferenceError("Reference for string %r not found" % (s,))

        return i

    def addString(self, s):
        """
        Creates a reference to C{s}. If the reference already exists, that
        reference is returned.

        @type s: C{str}
        @param s: The string to be referenced.
        @rtype: C{int}
        @return: The reference index.

        @raise TypeError: The parameter C{s} is not of C{basestring} type.
        @raise pyamf.ReferenceError: Trying to store a reference to an empty string.
        """
        if not isinstance(s, basestring):
            raise TypeError

        if len(s) == 0:
            if not self.exceptions:
                return None

            # do not store empty string references
            raise pyamf.ReferenceError("Cannot store a reference to an empty string")

        return self.strings.append(s)

    def getClassByReference(self, ref):
        """
        Return class reference.

        @raise pyamf.ReferenceError: The class reference could not be found.
        @return: Class reference.
        """
        try:
            return self.class_ref[ref]
        except KeyError:
            if not self.exceptions:
                return None

            raise pyamf.ReferenceError("Class reference %r not found" % (
                ref,))

    def getClass(self, klass):
        """
        Return class reference.

        @raise pyamf.ReferenceError: The class reference could not be found.
        @return: Class reference.
        """
        try:
            return self.classes[klass]
        except KeyError:
            if not self.exceptions:
                return None

            raise pyamf.ReferenceError("Class alias for %r not found" % (
                klass,))

    def addClass(self, alias, klass):
        """
        Creates a reference to C{class_def}.

        @param alias: C{ClassDefinition} instance.
        """
        ref = self.class_idx

        self.class_ref[ref] = alias
        cd = self.classes[klass] = alias

        cd.reference = ref

        self.class_idx += 1

        return ref

    def getLegacyXML(self, ref):
        """
        Return the legacy XML reference. This is the C{flash.xml.XMLDocument}
        class in ActionScript 3.0 and the top-level C{XML} class in
        ActionScript 1.0 and 2.0.

        @type ref: C{int}
        @param ref: The reference index.
        @raise pyamf.ReferenceError: The legacy XML reference could not be found.
        @return: Instance of L{ET<util.ET>}
        """
        i = self.legacy_xml.getByReference(ref)

        if i is None:
            if not self.exceptions:
                return None

            raise pyamf.ReferenceError("Legacy XML reference %r not found" % (ref,))

        return i

    def getLegacyXMLReference(self, doc):
        """
        Return legacy XML reference.

        @type doc: L{ET<util.ET>}
        @param doc: The XML document to reference.
        @raise pyamf.ReferenceError: The reference could not be found.
        @return: The reference to C{doc}.
        @rtype: C{int}
        """
        i = self.legacy_xml.getReferenceTo(doc)

        if i is None:
            if not self.exceptions:
                return None

            raise pyamf.ReferenceError("Reference for document %r not found" % (doc,))

        return i

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
        return self.legacy_xml.append(doc)

    def __copy__(self):
        return self.__class__(exceptions=self.exceptions)


class Decoder(pyamf.BaseDecoder):
    """
    Decodes an AMF3 data stream.
    """
    context_class = Context

    type_map = {
        TYPE_UNDEFINED:  'readUndefined',
        TYPE_NULL:       'readNull',
        TYPE_BOOL_FALSE: 'readBoolFalse',
        TYPE_BOOL_TRUE:  'readBoolTrue',
        TYPE_INTEGER:    'readSignedInteger',
        TYPE_NUMBER:     'readNumber',
        TYPE_STRING:     'readString',
        TYPE_XML:        'readXML',
        TYPE_DATE:       'readDate',
        TYPE_ARRAY:      'readArray',
        TYPE_OBJECT:     'readObject',
        TYPE_XMLSTRING:  'readXMLString',
        TYPE_BYTEARRAY:  'readByteArray',
    }

    def __init__(self, *args, **kwargs):
        self.use_proxies = kwargs.pop('use_proxies', use_proxies_default)

        pyamf.BaseDecoder.__init__(self, *args, **kwargs)

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
        return decode_int(self.stream, signed)

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

        if length == 0:
            return u''

        result = self.stream.read_utf8_string(length)

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

        if self.timezone_offset is not None:
            result += self.timezone_offset

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

        key = self.readString().encode('utf8')

        if key == '':
            # integer indexes only -> python list
            result = []
            self.context.addObject(result)

            for i in xrange(size):
                result.append(self.readElement())

            return result

        result = pyamf.MixedArray()
        self.context.addObject(result)

        while key != "":
            result[key] = self.readElement()
            key = self.readString().encode('utf8')

        for i in xrange(size):
            el = self.readElement()
            result[i] = el

        return result

    def _getClassDefinition(self, ref):
        """
        Reads class definition from the stream.
        """
        is_ref = ref & REFERENCE_BIT == 0
        ref >>= 1

        if is_ref:
            class_def = self.context.getClassByReference(ref)

            return class_def, class_def.alias

        name = self.readString()
        alias = None

        if name == '':
            name = pyamf.ASObject

        try:
            alias = pyamf.get_class_alias(name)
        except pyamf.UnknownClassAlias:
            if self.strict:
                raise

            alias = pyamf.TypedObjectClassAlias(pyamf.TypedObject, name)

        class_def = ClassDefinition(alias)

        class_def.encoding = ref & 0x03
        class_def.attr_len = ref >> 2
        class_def.static_properties = []

        if class_def.attr_len > 0:
            for i in xrange(class_def.attr_len):
                key = self.readString().encode('utf8')

                class_def.static_properties.append(key)

        self.context.addClass(class_def, alias.klass)

        return class_def, alias

    def readObject(self, use_proxies=None):
        """
        Reads an object from the stream.

        @raise pyamf.EncodeError: Decoding an object in amf3 tagged as amf0
            only is not allowed.
        @raise pyamf.DecodeError: Unknown object encoding.
        """
        if use_proxies is None:
            use_proxies = self.use_proxies

        def readStatic(class_def, obj):
            for attr in class_def.static_properties:
                obj[attr] = self.readElement()

        def readDynamic(class_def, obj):
            attr = self.readString().encode('utf8')

            while attr != '':
                obj[attr] = self.readElement()
                attr = self.readString().encode('utf8')

        ref = self.readUnsignedInteger()

        if ref & REFERENCE_BIT == 0:
            obj = self.context.getObject(ref >> 1)

            if use_proxies is True:
                obj = self.readProxyObject(obj)

            return obj

        ref >>= 1

        class_def, alias = self._getClassDefinition(ref)

        obj = alias.createInstance(codec=self)
        obj_attrs = dict()

        self.context.addObject(obj)

        if class_def.encoding in (ObjectEncoding.EXTERNAL, ObjectEncoding.PROXY):
            obj.__readamf__(DataInput(self))
        elif class_def.encoding == ObjectEncoding.DYNAMIC:
            readStatic(class_def, obj_attrs)
            readDynamic(class_def, obj_attrs)
        elif class_def.encoding == ObjectEncoding.STATIC:
            readStatic(class_def, obj_attrs)
        else:
            raise pyamf.DecodeError("Unknown object encoding")

        alias.applyAttributes(obj, obj_attrs, codec=self)

        if use_proxies is True:
            obj = self.readProxyObject(obj)

        return obj

    def readProxyObject(self, proxy):
        """
        Return the source object of a proxied object.

        @since: 0.4
        """
        if isinstance(proxy, ArrayCollection):
            return list(proxy)
        elif isinstance(proxy, ObjectProxy):
            return proxy._amf_object

        return proxy

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

        x = util.ET.fromstring(xmlstring)
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
        (types.StringTypes, "writeString"),
        ((ByteArray,), "writeByteArray"),
        ((datetime.date, datetime.datetime, datetime.time), "writeDate"),
        ((util.is_ET_element,), "writeXML"),
        ((pyamf.UndefinedType,), "writeUndefined"),
        ((types.ClassType, types.TypeType), "writeClass"),
        ((types.InstanceType, types.ObjectType,), "writeInstance"),
    ]

    def __init__(self, *args, **kwargs):
        self.use_proxies = kwargs.pop('use_proxies', use_proxies_default)
        self.string_references = kwargs.pop('string_references', True)

        pyamf.BaseEncoder.__init__(self, *args, **kwargs)

    def writeElement(self, data, use_references=True, use_proxies=None):
        """
        Writes the data.

        @param data: The data to be encoded to the AMF3 data stream.
        @type data: C{mixed}
        @param use_references: Default is C{True}.
        @type use_references: C{bool}
        @raise EncodeError: Cannot find encoder func for C{data}.
        """
        func = self._writeElementFunc(data)

        if func is None:
            raise pyamf.EncodeError("Unknown type %r" % (data,))

        func(data, use_references=use_references, use_proxies=use_proxies)

    def writeClass(self, *args, **kwargs):
        """
        Classes cannot be serialised.
        """
        raise pyamf.EncodeError("Class objects cannot be serialised")

    def writeUndefined(self, *args, **kwargs):
        """
        Writes an C{pyamf.Undefined} value to the stream.
        """
        self.stream.write(TYPE_UNDEFINED)

    def writeNull(self, *args, **kwargs):
        """
        Writes a C{null} value to the stream.
        """
        self.stream.write(TYPE_NULL)

    def writeBoolean(self, n, **kwargs):
        """
        Writes a Boolean to the stream.
        """
        t = TYPE_BOOL_TRUE

        if not n:
            t = TYPE_BOOL_FALSE

        self.stream.write(t)

    def _writeInteger(self, n):
        """
        AMF3 integers are encoded.

        @param n: The integer data to be encoded to the AMF3 data stream.
        @type n: integer data

        @see: U{Parsing Integers on OSFlash
        <http://osflash.org/documentation/amf3/parsing_integers>}
        for more info.
        """
        try:
            self.stream.write(ENCODED_INT_CACHE[n])
        except KeyError:
            ENCODED_INT_CACHE[n] = encode_int(n)
            self.stream.write(ENCODED_INT_CACHE[n])

    def writeInteger(self, n, **kwargs):
        """
        Writes an integer to the stream.

        @type   n: integer data
        @param  n: The integer data to be encoded to the AMF3 data stream.
        @type   use_references: C{bool}
        @kwarg  use_references: Default is C{True}.
        """
        if n < MIN_29B_INT or n > MAX_29B_INT:
            self.writeNumber(float(n))

            return

        self.stream.write(TYPE_INTEGER)
        self.stream.write(encode_int(n))

    def writeNumber(self, n, **kwargs):
        """
        Writes a float to the stream.

        @type n: C{float}
        """
        self.stream.write(TYPE_NUMBER)
        self.stream.write_double(n)

    def _writeString(self, n, **kwargs):
        """
        Writes a raw string to the stream.

        @type   n: C{str} or C{unicode}
        @param  n: The string data to be encoded to the AMF3 data stream.
        """
        if n == '':
            self.stream.write_uchar(REFERENCE_BIT)

            return

        t = type(n)

        if t is str:
            bytes = n
        elif t is unicode:
            bytes = n.encode('utf8')
        else:
            bytes = unicode(n).encode('utf8')
            n = bytes

        if self.string_references:
            ref = self.context.getStringReference(n)

            if ref is not None:
                self._writeInteger(ref << 1)

                return

            self.context.addString(n)

        self._writeInteger((len(bytes) << 1) | REFERENCE_BIT)
        self.stream.write(bytes)

    def writeString(self, n, writeType=True, **kwargs):
        """
        Writes a string to the stream. If C{n} is not a unicode string, an
        attempt will be made to convert it.

        @type   n: C{basestring}
        @param  n: The string data to be encoded to the AMF3 data stream.
        """
        if writeType:
            self.stream.write(TYPE_STRING)

        self._writeString(n, **kwargs)

    def writeDate(self, n, use_references=True, **kwargs):
        """
        Writes a C{datetime} instance to the stream.

        @type n: L{datetime}
        @param n: The C{Date} data to be encoded to the AMF3 data stream.
        @type use_references: C{bool}
        @param use_references: Default is C{True}.
        """
        if isinstance(n, datetime.time):
            raise pyamf.EncodeError('A datetime.time instance was found but '
                'AMF3 has no way to encode time objects. Please use '
                'datetime.datetime instead (got:%r)' % (n,))

        self.stream.write(TYPE_DATE)

        if use_references is True:
            ref = self.context.getObjectReference(n)

            if ref is not None:
                self._writeInteger(ref << 1)

                return

            self.context.addObject(n)

        self.stream.write_uchar(REFERENCE_BIT)

        if self.timezone_offset is not None:
            n -= self.timezone_offset

        ms = util.get_timestamp(n)
        self.stream.write_double(ms * 1000.0)

    def writeList(self, n, use_references=True, use_proxies=None):
        """
        Writes a C{tuple}, C{set} or C{list} to the stream.

        @type n: One of C{__builtin__.tuple}, C{__builtin__.set}
            or C{__builtin__.list}
        @param n: The C{list} data to be encoded to the AMF3 data stream.
        @type use_references: C{bool}
        @param use_references: Default is C{True}.
        """
        # Encode lists as ArrayCollections
        if use_proxies is None:
            use_proxies = self.use_proxies

        if use_proxies:
            ref_obj = self.context.getObjectAlias(n)

            if ref_obj is None:
                proxy = ArrayCollection(n)
                self.context.setObjectAlias(n, proxy)
                ref_obj = proxy

            self.writeObject(ref_obj, use_references, use_proxies=False)

            return

        self.stream.write(TYPE_ARRAY)

        if use_references:
            ref = self.context.getObjectReference(n)

            if ref is not None:
                self._writeInteger(ref << 1)

                return

            self.context.addObject(n)

        self._writeInteger((len(n) << 1) | REFERENCE_BIT)
        self.stream.write_uchar(0x01)

        [self.writeElement(x) for x in n]

    def writeDict(self, n, use_references=True, use_proxies=None):
        """
        Writes a C{dict} to the stream.

        @type n: C{__builtin__.dict}
        @param n: The C{dict} data to be encoded to the AMF3 data stream.
        @type use_references: C{bool}
        @param use_references: Default is C{True}.
        @raise ValueError: Non C{int}/C{str} key value found in the C{dict}
        @raise EncodeError: C{dict} contains empty string keys.
        """

        # Design bug in AMF3 that cannot read/write empty key strings
        # http://www.docuverse.com/blog/donpark/2007/05/14/flash-9-amf3-bug
        # for more info
        if '' in n:
            raise pyamf.EncodeError("dicts cannot contain empty string keys")

        if use_proxies is None:
            use_proxies = self.use_proxies

        if use_proxies is True:
            ref_obj = self.context.getObjectAlias(n)

            if ref_obj is None:
                proxy = ObjectProxy(pyamf.ASObject(n))
                self.context.setObjectAlias(n, proxy)
                ref_obj = proxy

            self.writeObject(ref_obj, use_references, use_proxies=False)

            return

        self.stream.write(TYPE_ARRAY)

        if use_references:
            ref = self.context.getObjectReference(n)

            if ref is not None:
                self._writeInteger(ref << 1)

                return

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
            self._writeString(x)
            self.writeElement(n[x])

        self.stream.write_uchar(0x01)

        for k in int_keys:
            self.writeElement(n[k])

    def writeInstance(self, obj, **kwargs):
        """
        Read class definition.

        @param obj: The class instance to be encoded.
        """
        kls = obj.__class__

        if kls is pyamf.MixedArray:
            f = self._write_elem_func_cache[kls] = self.writeDict
        elif kls in (list, set, tuple):
            f = self._write_elem_func_cache[kls] = self.writeList
        else:
            f = self._write_elem_func_cache[kls] = self.writeObject

        f(obj, **kwargs)

    def writeObject(self, obj, use_references=True, use_proxies=None):
        """
        Writes an object to the stream.

        @param obj: The object data to be encoded to the AMF3 data stream.
        @type obj: object data
        @param use_references: Default is C{True}.
        @type use_references: C{bool}
        @raise EncodeError: Encoding an object in amf3 tagged as amf0 only.
        """
        if use_proxies is None:
            use_proxies = self.use_proxies

        if use_proxies is True and obj.__class__ is dict:
            ref_obj = self.context.getObjectAlias(obj)

            if ref_obj is None:
                proxy = ObjectProxy(obj)
                self.context.setObjectAlias(obj, proxy)
                ref_obj = proxy

            self.writeObject(ref_obj, use_references, use_proxies=False)

            return

        self.stream.write(TYPE_OBJECT)

        if use_references:
            ref = self.context.getObjectReference(obj)

            if ref is not None:
                self._writeInteger(ref << 1)

                return

            self.context.addObject(obj)

        # object is not referenced, serialise it
        kls = obj.__class__
        definition = self.context.getClass(kls)
        alias = None
        class_ref = False # if the class definition is a reference

        if definition:
            class_ref = True
            alias = definition.alias

            if alias.anonymous and definition.reference is not None:
                class_ref = True
        else:
            try:
                alias = pyamf.get_class_alias(kls)
            except pyamf.UnknownClassAlias:
                alias_klass = util.get_class_alias(kls)
                meta = util.get_class_meta(kls)

                alias = alias_klass(kls, defer=True, **meta)

            definition = ClassDefinition(alias)

            self.context.addClass(definition, alias.klass)

        if class_ref:
            self.stream.write(definition.reference)
        else:
            ref = 0

            if definition.encoding != ObjectEncoding.EXTERNAL:
                ref += definition.attr_len << 4

            final_reference = encode_int(ref | definition.encoding << 2 |
                REFERENCE_BIT << 1 | REFERENCE_BIT)

            self.stream.write(final_reference)

            definition.reference = encode_int(
                definition.reference << 2 | REFERENCE_BIT)

            if alias.anonymous:
                self.stream.write_uchar(0x01)
            else:
                self._writeString(alias.alias)

            # work out what the final reference for the class will be.
            # this is okay because the next time an object of the same
            # class is encoded, class_ref will be True and never get here
            # again.

        if alias.external:
            obj.__writeamf__(DataOutput(self))

            return

        sa, da = alias.getEncodableAttributes(obj, codec=self)

        if sa:
            if not class_ref:
                [self._writeString(attr) for attr in alias.static_attrs]

            [self.writeElement(sa[attr]) for attr in alias.static_attrs]

            if definition.encoding == ObjectEncoding.STATIC:
                return

        if definition.encoding == ObjectEncoding.DYNAMIC:
            if da:
                for attr, value in da.iteritems():
                    self._writeString(attr)
                    self.writeElement(value)

            self.stream.write_uchar(0x01)

    def writeByteArray(self, n, use_references=True, **kwargs):
        """
        Writes a L{ByteArray} to the data stream.

        @param n: The L{ByteArray} data to be encoded to the AMF3 data stream.
        @type n: L{ByteArray}
        @param use_references: Default is C{True}.
        @type use_references: C{bool}
        """
        self.stream.write(TYPE_BYTEARRAY)

        if use_references:
            ref = self.context.getObjectReference(n)

            if ref is not None:
                self._writeInteger(ref << 1)

                return

            self.context.addObject(n)

        buf = str(n)
        l = len(buf)
        self._writeInteger(l << 1 | REFERENCE_BIT)
        self.stream.write(buf)

    def writeXML(self, n, use_references=True, use_proxies=None):
        """
        Writes a XML string to the data stream.

        @type   n: L{ET<util.ET>}
        @param  n: The XML Document to be encoded to the AMF3 data stream.
        @type   use_references: C{bool}
        @param  use_references: Default is C{True}.
        """
        i = self.context.getLegacyXMLReference(n)

        if i is None:
            is_legacy = True
        else:
            is_legacy = False

        if is_legacy is True:
            self.stream.write(TYPE_XMLSTRING)
        else:
            self.stream.write(TYPE_XML)

        if use_references:
            ref = self.context.getObjectReference(n)

            if ref is not None:
                self._writeInteger(ref << 1)

                return

            self.context.addObject(n)

        self._writeString(util.ET.tostring(n, 'utf-8'))


def decode(stream, context=None, strict=False):
    """
    A helper function to decode an AMF3 datastream.

    @type   stream: L{BufferedByteStream<util.BufferedByteStream>}
    @param  stream: AMF3 data.
    @type   context: L{Context}
    @param  context: Context.
    """
    decoder = Decoder(stream, context, strict)

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


def encode_int(n):
    """
    Encodes an int as a variable length signed 29-bit integer as defined by
    the spec.

    @param n: The integer to be encoded
    @return: The encoded string
    @rtype: C{str}
    @raise OverflowError: Out of range.
    """
    if n < MIN_29B_INT or n > MAX_29B_INT:
        raise OverflowError("Out of range")

    if n < 0:
        n += 0x20000000

    bytes = ''
    real_value = None

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


def decode_int(stream, signed=False):
    """
    Decode C{int}.
    """
    n = result = 0
    b = stream.read_uchar()

    while b & 0x80 != 0 and n < 3:
        result <<= 7
        result |= b & 0x7f
        b = stream.read_uchar()
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

try:
    from cpyamf.amf3 import encode_int, decode_int
except ImportError:
    pass


pyamf.register_class(ByteArray)

for x in range(0, 20):
    ENCODED_INT_CACHE[x] = encode_int(x)
del x
