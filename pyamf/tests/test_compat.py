# -*- encoding: utf-8 -*-
#
# Copyright (c) 2007 The PyAMF Project. All rights reserved.
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
Flex/Flash compatibility tests.

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import unittest

import pyamf
from pyamf import compat, util, amf3

class DataOutputTestCase(unittest.TestCase):
    def setUp(self):
        self.stream = util.BufferedByteStream()
        self.encoder = amf3.Encoder(self.stream)

    def test_create(self):
        x = compat.DataOutput(self.encoder)

        self.assertEquals(x.encoder, self.encoder)
        self.assertEquals(x.stream, self.stream)
        self.assertEquals(x.stream, self.encoder.stream)

    def test_boolean(self):
        x = compat.DataOutput(self.encoder)

        x.writeBoolean(True)
        self.assertEquals(self.stream.getvalue(), '\x01')
        self.stream.truncate()

        x.writeBoolean(False)
        self.assertEquals(self.stream.getvalue(), '\x00')

    def test_byte(self):
        x = compat.DataOutput(self.encoder)

        for y in xrange(10):
            x.writeByte(y)

        self.assertEquals(self.stream.getvalue(),
            '\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09')

    def test_double(self):
        x = compat.DataOutput(self.encoder)

        x.writeDouble(0.0)
        self.assertEquals(self.stream.getvalue(), '\x00' * 8)
        self.stream.truncate()

        x.writeDouble(1234.5678)
        self.assertEquals(self.stream.getvalue(), '@\x93JEm\\\xfa\xad')

    def test_float(self):
        x = compat.DataOutput(self.encoder)

        x.writeFloat(0.0)
        self.assertEquals(self.stream.getvalue(), '\x00' * 4)
        self.stream.truncate()

        x.writeFloat(1234.5678)
        self.assertEquals(self.stream.getvalue(), 'D\x9aR+')

    def test_int(self):
        x = compat.DataOutput(self.encoder)

        x.writeInt(0)
        self.assertEquals(self.stream.getvalue(), '\x00\x00\x00\x00')
        self.stream.truncate()

        x.writeInt(-12345)
        self.assertEquals(self.stream.getvalue(), '\xff\xff\xcf\xc7')
        self.stream.truncate()

        x.writeInt(98)
        self.assertEquals(self.stream.getvalue(), '\x00\x00\x00b')

    def test_multi_byte(self):
        # TODO nick: test multiple charsets
        x = compat.DataOutput(self.encoder)

        x.writeMultiByte('this is a test', 'utf-8')
        self.assertEquals(self.stream.getvalue(), u'this is a test')
        self.stream.truncate()

        x.writeMultiByte(u'ἔδωσαν', 'utf-8')
        self.assertEquals(self.stream.getvalue(), '\xe1\xbc\x94\xce\xb4\xcf'
            '\x89\xcf\x83\xce\xb1\xce\xbd')

    def test_object(self):
        x = compat.DataOutput(self.encoder)
        obj = {'foo': 'bar'}

        x.writeObject(obj)
        self.assertEquals(self.stream.getvalue(),
            '\t\x01\x07foo\x06\x07bar\x01')
        self.stream.truncate()

        # check references
        x.writeObject(obj)
        self.assertEquals(self.stream.getvalue(), '\t\x00')
        self.stream.truncate()

        # check force no references, should include class def ref and refs to
        # string
        x.writeObject(obj, False)
        self.assertEquals(self.stream.getvalue(), '\t\x01\x00\x06\x02\x01')

    def test_short(self):
        x = compat.DataOutput(self.encoder)

        x.writeShort(55)
        self.assertEquals(self.stream.getvalue(), '\x007')
        self.stream.truncate()

        x.writeShort(-55)
        self.assertEquals(self.stream.getvalue(), '\xff\xc9')

    def test_uint(self):
        x = compat.DataOutput(self.encoder)

        x.writeUnsignedInt(55)
        self.assertEquals(self.stream.getvalue(), '\x00\x00\x007')
        self.stream.truncate()

        self.assertRaises(ValueError, x.writeUnsignedInt, -55)

    def test_utf(self):
        x = compat.DataOutput(self.encoder)

        x.writeUTF(u'ἔδωσαν')

        self.assertEquals(self.stream.getvalue(), '\x00\r\xe1\xbc\x94\xce\xb4'
            '\xcf\x89\xcf\x83\xce\xb1\xce\xbd')

    def test_utf_bytes(self):
        x = compat.DataOutput(self.encoder)

        x.writeUTFBytes(u'ἔδωσαν')

        self.assertEquals(self.stream.getvalue(),
            '\xe1\xbc\x94\xce\xb4\xcf\x89\xcf\x83\xce\xb1\xce\xbd')

class DataInputTestCase(unittest.TestCase):
    def setUp(self):
        self.stream = util.BufferedByteStream()
        self.decoder = amf3.Decoder(self.stream)

    def test_create(self):
        x = compat.DataInput(self.decoder)

        self.assertEquals(x.decoder, self.decoder)
        self.assertEquals(x.stream, self.stream)
        self.assertEquals(x.stream, self.decoder.stream)

    def _test(self, bytes, value, func, *params):
        self.stream.write(bytes)
        self.stream.seek(0)

        self.assertEquals(func(*params), value)
        self.stream.truncate()

    def test_boolean(self):
        x = compat.DataInput(self.decoder)

        self.stream.write('\x01')
        self.stream.seek(-1, 2)
        self.assertEquals(x.readBoolean(), True)

        self.stream.write('\x00')
        self.stream.seek(-1, 2)
        self.assertEquals(x.readBoolean(), False)

    def test_byte(self):
        x = compat.DataInput(self.decoder)

        self.stream.write('\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09')
        self.stream.seek(0)

        for y in xrange(10):
            self.assertEquals(x.readByte(), y)

    def test_double(self):
        x = compat.DataInput(self.decoder)

        self._test('\x00' * 8, 0.0, x.readDouble)
        self._test('@\x93JEm\\\xfa\xad', 1234.5678, x.readDouble)

    def test_float(self):
        x = compat.DataInput(self.decoder)

        self._test('\x00' * 4, 0.0, x.readFloat)
        self._test('?\x00\x00\x00', 0.5, x.readFloat)

    def test_int(self):
        x = compat.DataInput(self.decoder)

        self._test('\x00\x00\x00\x00', 0, x.readInt)
        self._test('\xff\xff\xcf\xc7', -12345, x.readInt)
        self._test('\x00\x00\x00b', 98, x.readInt)

    def test_multi_byte(self):
        # TODO nick: test multiple charsets
        x = compat.DataInput(self.decoder)

        self._test(u'this is a test', u'this is a test', x.readMultiByte,
            14, 'utf-8')
        self._test('\xe1\xbc\x94\xce\xb4\xcf\x89\xcf\x83\xce\xb1\xce\xbd',
            u'ἔδωσαν', x.readMultiByte, 13, 'utf-8')

    def test_object(self):
        x = compat.DataInput(self.decoder)
        
        self._test('\t\x01\x07foo\x06\x07bar\x01', {'foo': 'bar'}, x.readObject)
        # check references
        self._test('\t\x00', {'foo': 'bar'}, x.readObject)

    def test_short(self):
        x = compat.DataInput(self.decoder)

        self._test('\x007', 55, x.readShort)
        self._test('\xff\xc9', -55, x.readShort)

    def test_uint(self):
        x = compat.DataInput(self.decoder)

        self._test('\x00\x00\x007', 55, x.readUnsignedInt)

    def test_utf(self):
        x = compat.DataInput(self.decoder)

        self._test('\x00\r\xe1\xbc\x94\xce\xb4\xcf\x89\xcf\x83\xce\xb1\xce\xbd',
            u'ἔδωσαν', x.readUTF)

    def test_utf_bytes(self):
        x = compat.DataInput(self.decoder)

        self._test('\xe1\xbc\x94\xce\xb4\xcf\x89\xcf\x83\xce\xb1\xce\xbd',
            u'ἔδωσαν', x.readUTFBytes, 13)

class ArrayCollectionTestCase(unittest.TestCase):
    def test_encode(self):
        stream = util.BufferedByteStream()
        encoder = amf3.Encoder(stream)

        x = compat.ArrayCollection()

        x['foo'] = 'bar'

        encoder.writeElement(x)

        self.assertEquals(stream.getvalue(),
            '\n\x07Cflex.messaging.io.ArrayCollection'
            '\t\x01\x07foo\x06\x07bar\x01')

    def test_decode(self):
        stream = util.BufferedByteStream(
            '\n\x07Cflex.messaging.io.ArrayCollection'
            '\t\x01\x07foo\x06\x07bar\x01')
        decoder = amf3.Decoder(stream)

        x = decoder.readElement()

        self.assertEquals(x.__class__, compat.ArrayCollection)
        self.assertEquals(x.keys(), ['foo'])
        self.assertEquals(x.items(), [('foo', u'bar')])

class ObjectProxyTestCase(unittest.TestCase):
    def test_encode(self):
        stream = util.BufferedByteStream()
        encoder = amf3.Encoder(stream)

        x = compat.ObjectProxy({'a': 'foo', 'b': 5})

        encoder.writeElement(x)

        self.assertEquals(stream.getvalue(),
            '\x0a\x07;flex.messaging.io.ObjectProxy\x09\x01\x03a\x06\x07foo'
            '\x03b\x04\x05\x01')

    def test_decode(self):
        stream = util.BufferedByteStream(
            '\x0a\x07;flex.messaging.io.ObjectProxy\x09\x01\x03a\x06\x07foo'
            '\x03b\x04\x05\x01')
        decoder = amf3.Decoder(stream)

        x = decoder.readElement()

        self.assertEquals(x.__class__, compat.ObjectProxy)
        self.assertEquals(x._amf_object, {'a': 'foo', 'b': 5})

def suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(DataOutputTestCase))
    suite.addTest(unittest.makeSuite(DataInputTestCase))
    suite.addTest(unittest.makeSuite(ArrayCollectionTestCase))
    suite.addTest(unittest.makeSuite(ObjectProxyTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
