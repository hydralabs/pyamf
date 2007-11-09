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

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import pyamf

class DataOutput(object):
    """
    I provide a set of methods for writing binary data.
    
    This class is the I/O counterpart to the L{DataInput} class, which reads
    binary data.

    @see: U{http://livedocs.adobe.com/flex/201/langref/flash/utils/IDataOutput.html}
    """
    def __init__(self, encoder):
        self.encoder = encoder
        self.stream = encoder.output

    def writeBoolean(self, value):
        """
        @type value:
        @param value:
        
        @raise ValueError: None boolean value is found.
        """
        if value is True:
            self.stream.write('\x01')
        elif value is False:
            self.stream.write('\x00')
        else:
            raise ValueError("None boolean value found")

    def writeByte(self, value):
        self.stream.write_char(value)

    def writeDouble(self, value):
        self.stream.write_double(value)

    def writeFloat(self, value):
        self.stream.write_float(value)

    def writeInt(self, value):
        self.stream.write_long(value)

    def writeMultiByte(self, value, charset):
        self.stream.write(unicode(value).encode(charset))

    def writeObject(self, value, use_references=True):
        self.encoder.writeElement(value, use_references=True)

    def writeShort(self, value):
        self.stream.write_short(value)

    def writeUnsignedInt(self, value):
        self.stream.write_ulong(value)

    def writeUTF(self, value):
        from pyamf import amf3

        self.stream.write(amf3.encode_utf8_modified(unicode(value, 'utf8')))

    def writeUTFBytes(self, value):
        from pyamf import amf3

        self.stream.write(amf3.encode_utf8_modified(unicode(value, 'utf8'))[2:])

class DataInput(object):
    """
    I provide a set of methods for reading binary data.
    
    This class is the I/O counterpart to the L{DataOutput} class,
    which writes binary data.

    @see: U{http://livedocs.adobe.com/flex/201/langref/flash/utils/IDataInput.html}
    """
    def __init__(self, decoder):
        self.decoder = decoder
        self.stream = decoder.input

    def readBoolean(self):
        byte = self.stream.read(1)

        if byte == '\x00':
            return False
        elif byte == '\x01':
            return True
        else:
            raise ValueError("Error reading boolean")

    def readByte(self):
        return self.stream.read_char()

    def readDouble(self):
        return self.stream.read_double()

    def readFloat(self):
        return self.stream.read_float()

    def readInt(self):
        return self.stream.read_long()

    def readObject(self):
        return self.decoder.readElement()

    def readShort(self):
        return self.stream.read_short()

    def readUnsignedByte(self):
        return self.stream.read_uchar()

    def readUnsignedInt(self):
        return self.stream.read_ulong()

    def readUnsignedShort(self):
        return self.stream.read_ushort()

    def readMultiByte(self, length, charset):
        #FIXME nick: how to work out the code point byte size (on the fly)?
        bytes = self.stream.read(length)

        return unicode(bytes, charset)

    def readUTF(self):
        from pyamf import amf3

        data = self.stream.peek(2)
        length = ((ord(data[0]) << 8) & 0xff) + ((ord(data[1]) << 0) & 0xff)
        
        return amf3.decode_utf8_modified(self.stream.read(length + 2))        

    def readUTFBytes(self, length):
        return self.readMultiByte(length, 'utf-8')

class ArrayCollection(dict):
    """
    I represent the ActionScript 3 based class C{flex.messaging.io.ArrayCollection}
    used in the Flex framework.
    
    The ArrayCollection class is a wrapper class that exposes an Array as
    a collection that can be accessed and manipulated using the methods
    and properties of the ICollectionView or IList interfaces in the Flex
    framework.

    @see: U{http://livedocs.adobe.com/flex/2/langref/mx/collections/ArrayCollection.html}
    """

    def __repr__(self):
        return "<flex.messaging.io.ArrayCollection %s>" % dict.__repr__(self)

def read_ArrayCollection(obj, input):
    data = input.readObject()

    if hasattr(data, 'iteritems'):
        for (k, v) in data.iteritems():
            obj[k] = v
    else:
        count = 0
        for i in data:
            obj[count] = i
            count += 1   

def write_ArrayCollection(obj, output):
    output.writeObject(obj.__dict__, use_references=False)

pyamf.register_class(ArrayCollection, 'flex.messaging.io.ArrayCollection',
    read_func=read_ArrayCollection, write_func=write_ArrayCollection)

class ObjectProxy(pyamf.Bag):
    """
    I represent an C{flex.messaging.io.ObjectProxy} ActionScript object.

    This class provides the ability to track changes to an item managed by this proxy.
    
    @see: U{http://livedocs.adobe.com/flex/2/langref/mx/utils/ObjectProxy.html}
    """

    def __repr__(self):
        return "<flex.messaging.io.ObjectProxy %s>" % dict.__repr__(self.__dict__)

pyamf.register_class(ObjectProxy, 'flex.messaging.io.ObjectProxy',
    read_func=read_ArrayCollection, write_func=write_ArrayCollection)
