# -*- encoding: utf8 -*-
#
# Copyright (c) 2007 The PyAMF Project. All rights reserved.
#
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
Contains compatibility classes/functions for Python -> Flex and vice versa.

@note: Not available in Actionscript 1.0 and 2.0.

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import pyamf

class DataOutput(object):
    """
    I provide a set of methods for writing binary data with ActionScript 3.0.
    
    This class is the I/O counterpart to the L{DataInput} class, which reads
    binary data.

    @see: U{Livedocs (external)
    <http://livedocs.adobe.com/flex/201/langref/flash/utils/IDataOutput.html>}
    """
    def __init__(self, encoder):
        """
        @param encoder: Encoder containing the stream.
        @type encoder: L{Encoder<pyamf.amf3.Encoder>}
        """
        self.encoder = encoder
        self.stream = encoder.stream

    def writeBoolean(self, value):
        """
        Writes a Boolean value.
        
        @type value: bool
        @param value: A Boolean value determining which byte is written.
        If the parameter is C{True}, 1 is written; if C{False}, 0 is written.

        @raise ValueError: Non-boolean value is found.
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
        
        @type value: int
        @param value:
        """
        self.stream.write_char(value)

    def writeDouble(self, value):
        """
        Writes an IEEE 754 double-precision (64-bit) floating
        point number.

        @type value: number
        @param value:
        """
        self.stream.write_double(value)

    def writeFloat(self, value):
        """
        Writes an IEEE 754 single-precision (32-bit) floating
        point number.

        @type value: number
        @param value:
        """
        self.stream.write_float(value)

    def writeInt(self, value):
        """
        Writes a 32-bit signed integer.

        @type value: int
        @param value:
        """
        self.stream.write_long(value)

    def writeMultiByte(self, value, charset):
        """
        Writes a multibyte string to the datastream using the
        specified character set.

        @type value: str
        @param value: The string value to be written.
        @type charset: str
        @param charset: The string denoting the character
        set to use. Possible character set strings include
        C{shift-jis}, C{cn-gb}, C{iso-8859-1} and others.
        @see: U{Supported Character Sets on Livedocs (external)
        <http://livedocs.adobe.com/labs/flex/3/langref/charset-codes.html>}
        """
        self.stream.write(unicode(value).encode(charset))

    def writeObject(self, value, use_references=True):
        """
        Writes an object to data stream in AMF serialized format.

        @type value:
        @param value: The object to be serialized.
        @type use_references: bool
        @param use_references:
        """
        self.encoder.writeElement(value, use_references)

    def writeShort(self, value):
        """
        Writes a 16-bit integer.

        @type value: int
        @param value: A byte value as an integer.
        """
        self.stream.write_short(value)

    def writeUnsignedInt(self, value):
        """
        Writes a 32-bit unsigned integer.

        @type value: int
        @param value: A byte value as an unsigned integer.
        """
        self.stream.write_ulong(value)

    def writeUTF(self, value):
        """
        Writes a UTF-8 string to the data stream.

        The length of the UTF-8 string in bytes is written first,
        as a 16-bit integer, followed by the bytes representing the
        characters of the string.

        @type value: str
        @param value: The string value to be written.
        """
        from pyamf import amf3

        val = None

        if isinstance(value, unicode):
            val = value
        else:
            val = unicode(value, 'utf8')

        self.stream.write(amf3.encode_utf8_modified(val))

    def writeUTFBytes(self, value):
        """
        Writes a UTF-8 string. Similar to L{writeUTF}, but does
        not prefix the string with a 16-bit length word.

        @type value: str
        @param value: The string value to be written.
        """
        from pyamf import amf3

        val = None

        if isinstance(value, unicode):
            val = value
        else:
            val = unicode(value, 'utf8')

        self.stream.write(amf3.encode_utf8_modified(val)[2:])

class DataInput(object):
    """
    I provide a set of methods for reading binary data with ActionScript 3.0.
    
    This class is the I/O counterpart to the L{DataOutput} class,
    which writes binary data.

    @see: U{Livedocs (external)
    <http://livedocs.adobe.com/flex/201/langref/flash/utils/IDataInput.html>}
    """
    def __init__(self, decoder):
        """
        @param decoder: AMF3 decoder containing the stream.
        @type decoder: L{Decoder<pyamf.amf3.Decoder>}
        """
        self.decoder = decoder
        self.stream = decoder.stream

    def readBoolean(self):
        """
        Read Boolean.

        @raise ValueError: Error reading Boolean.
        @rtype: bool
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

        @rtype: int
        @return: The returned value is in the range -128 to 127.
        """
        return self.stream.read_char()

    def readDouble(self):
        """
        Reads an IEEE 754 double-precision floating point number from the
        data stream.

        @rtype: number
        @return: An IEEE 754 double-precision floating point number.
        """
        return self.stream.read_double()

    def readFloat(self):
        """
        Reads an IEEE 754 single-precision floating point number from the
        data stream.

        @rtype: number
        @return: An IEEE 754 single-precision floating point number.
        """
        return self.stream.read_float()

    def readInt(self):
        """
        Reads a signed 32-bit integer from the data stream.

        @rtype: int
        @return: The returned value is in the range -2147483648 to 2147483647.
        """
        return self.stream.read_long()

    def readMultiByte(self, length, charset):
        """
        Reads a multibyte string of specified length from the data stream
        using the specified character set.

        @type length: int
        @param length: The number of bytes from the data stream to read.
        
        @type charset: str
        @param charset: The string denoting the character set to use.

        @rtype: str
        @return: UTF-8 encoded string.
        """
        #FIXME nick: how to work out the code point byte size (on the fly)?
        bytes = self.stream.read(length)

        return unicode(bytes, charset)

    def readObject(self):
        """
        Reads an object from the data stream.

        @rtype: 
        @return: The deserialized object.
        """
        return self.decoder.readElement()

    def readShort(self):
        """
        Reads a signed 16-bit integer from the data stream.

        @rtype: uint
        @return: The returned value is in the range -32768 to 32767.
        """
        return self.stream.read_short()

    def readUnsignedByte(self):
        """
        Reads an unsigned byte from the data stream.

        @rtype: uint
        @return: The returned value is in the range 0 to 255.
        """
        return self.stream.read_uchar()

    def readUnsignedInt(self):
        """
        Reads an unsigned 32-bit integer from the data stream.

        @rtype: uint
        @return: The returned value is in the range 0 to 4294967295.
        """
        return self.stream.read_ulong()

    def readUnsignedShort(self):
        """
        Reads an unsigned 16-bit integer from the data stream.

        @rtype: uint
        @return: The returned value is in the range 0 to 65535.
        """
        return self.stream.read_ushort()

    def readUTF(self):
        """
        Reads a UTF-8 string from the data stream.

        The string is assumed to be prefixed with an unsigned
        short indicating the length in bytes.

        @rtype: str
        @return: A UTF-8 string produced by the byte
        representation of characters.
        """
        from pyamf import amf3

        data = self.stream.peek(2)
        length = ((ord(data[0]) << 8) & 0xff) + ((ord(data[1]) << 0) & 0xff)
        
        return amf3.decode_utf8_modified(self.stream.read(length + 2))        

    def readUTFBytes(self, length):
        """
        Reads a sequence of C{length} UTF-8 bytes from the data
        stream and returns a string.

        @type length: int
        @param length: The number of bytes from the data stream to read.
        @rtype: str
        @return: A UTF-8 string produced by the byte
        representation of characters of specified length.
        """
        return self.readMultiByte(length, 'utf-8')

class ArrayCollection(dict):
    """
    I represent the ActionScript 3 based class
    C{flex.messaging.io.ArrayCollection} used in the Flex framework.

    The ArrayCollection class is a wrapper class that exposes an Array 
    as a collection that can be accessed and manipulated using the 
    methods and properties of the ICollectionView or IList interfaces 
    in the Flex framework.

    @see: U{Livedocs (external)
    <http://livedocs.adobe.com/flex/201/langref/mx/collections/ArrayCollection.html>}
    """

    def __repr__(self):
        return "<flex.messaging.io.ArrayCollection %s>" % dict.__repr__(self)

    def __readamf__(self, input):
        data = input.readObject()

        if hasattr(data, 'iteritems'):
            for (k, v) in data.iteritems():
                self[k] = v
        else:
            count = 0
            for i in data:
                self[count] = i
                count += 1   

    def __writeamf__(self, output):
        output.writeObject(dict(self), use_references=False)

pyamf.register_class(ArrayCollection, 'flex.messaging.io.ArrayCollection',
    read_func=ArrayCollection.__readamf__,
    write_func=ArrayCollection.__writeamf__)

class ObjectProxy(object):
    """
    I represent the ActionScript 3 based class C{flex.messaging.io.ObjectProxy}
    used in the Flex framework.

    @see: U{Livedocs (external)
    <http://livedocs.adobe.com/flex/201/langref/mx/utils/ObjectProxy.html>}
    """

    def __init__(self, object=None):
        self._amf_object = object

    def __repr__(self):
        return "<flex.messaging.io.ObjectProxy %s>" % self.__dict__

    def __getattr__(self, name):
        if name == '_amf_object':
            return self._amf_object

        return getattr(self._amf_object, name)

    def __setattr__(self, name, value):
        if name == '_amf_object':
            self.__dict__['_amf_object'] = value
        else:
            return setattr(self._amf_object, name, value)

    def __readamf__(self, input):
        self._amf_object = input.readObject()

    def __writeamf__(self, output):
        output.writeObject(self._amf_object)

pyamf.register_class(ObjectProxy, 'flex.messaging.io.ObjectProxy',
    read_func=ObjectProxy.__readamf__,
    write_func=ObjectProxy.__writeamf__)
