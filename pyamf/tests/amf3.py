# -*- encoding: utf-8 -*-
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

import unittest

import pyamf
from pyamf import amf3, util
from pyamf.tests.util import GenericObject, EncoderTester, ParserTester

class TypesTestCase(unittest.TestCase):
    def test_types(self):
        self.assertEquals(amf3.ASTypes.UNDEFINED, 0x00)
        self.assertEquals(amf3.ASTypes.NULL, 0x01)
        self.assertEquals(amf3.ASTypes.BOOL_FALSE, 0x02)
        self.assertEquals(amf3.ASTypes.BOOL_TRUE, 0x03)
        self.assertEquals(amf3.ASTypes.INTEGER, 0x04)
        self.assertEquals(amf3.ASTypes.NUMBER, 0x05)
        self.assertEquals(amf3.ASTypes.STRING, 0x06)
        self.assertEquals(amf3.ASTypes.XML, 0x07)
        self.assertEquals(amf3.ASTypes.DATE, 0x08)
        self.assertEquals(amf3.ASTypes.ARRAY, 0x09)
        self.assertEquals(amf3.ASTypes.OBJECT, 0x0a)
        self.assertEquals(amf3.ASTypes.XMLSTRING, 0x0b)
        self.assertEquals(amf3.ASTypes.BYTEARRAY, 0x0c)

class EncoderTestCase(unittest.TestCase):
    def setUp(self):
        self.buf = util.BufferedByteStream()
        self.context = pyamf.Context()
        self.e = amf3.Encoder(self.buf, context=self.context)

    def _run(self, data):
        self.context.clear()

        e = EncoderTester(self.e, data)
        e.run(self)

    def test_undefined(self):
        def x():
            self._run([(ord, '\x00')])

        self.assertRaises(AttributeError, x)

    def test_null(self):
        self._run([(None, '\x01')])

    def test_boolean(self):
        self._run([(True, '\x03'), (False, '\x02')])

    def test_integer(self):
        self._run([
            (0, '\x04\x00'),
            (94L, '\x04\x5e'),
            (-3422345L, '\x04\xff\x97\xc7\x77')])

    def test_number(self):
        self._run([
            (0.1, '\x05\x3f\xb9\x99\x99\x99\x99\x99\x9a'),
            (0.123456789, '\x05\x3f\xbf\x9a\xdd\x37\x39\x63\x5f')])

    def test_string(self):
        self._run([
            ('hello', '\x06\x0bhello'),
            (u'ᚠᛇᚻ', '\x06\x13\xe1\x9a\xa0\xe1\x9b\x87\xe1\x9a\xbb')])

    def test_string_references(self):
        self._run([
            ('hello', '\x06\x0bhello'),
            ('hello', '\x06\x00'),
            ('hello', '\x06\x00')])

    def test_date(self):
        import datetime

        self._run([
            (datetime.datetime(2005, 3, 18, 1, 58, 31),
                '\x08\x01Bp+6!\x15\x80\x00')])

    def test_date_references(self):
        import datetime

        self.e.obj_refs = []

        x = datetime.datetime(2005, 3, 18, 1, 58, 31)

        self._run([
            (x, '\x08\x01Bp+6!\x15\x80\x00'),
            (x, '\x08\x00'),
            (x, '\x08\x00')])

    def test_list(self):
        self._run([
            ([0, 1, 2, 3], '\x09\x09\x01\x04\x00\x04\x01\x04\x02\x04\x03')])

    def test_list_references(self):
        y = [0, 1, 2, 3]

        self._run([
            (y, '\x09\x09\x01\x04\x00\x04\x01\x04\x02\x04\x03'),
            (y, '\x09\x00'),
            (y, '\x09\x00')])

    def test_dict(self):
        self._run([
            ({0: u'hello', 'foo': u'bar'},
            '\x09\x03\x07\x66\x6f\x6f\x06\x07\x62\x61\x72\x01\x06\x0b\x68\x65'
            '\x6c\x6c\x6f')])
        self._run([({0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 'a': 'a'},
            '\x09\x0d\x03\x61\x06\x00\x01\x04\x00\x04\x01\x04\x02\x04\x03\x04'
            '\x04\x04\x05')])

        x = amf3.Parser('\x09\x09\x03\x62\x06\x00\x03\x64\x06\x02\x03\x61\x06'
        '\x04\x03\x63\x06\x06\x01\x04\x00\x04\x01\x04\x02\x04\x03')

        self.assertEqual(
            x.readElement(),
            {'a': u'a', 'b': u'b', 'c': u'c', 'd': u'd',
                0: 0, 1: 1, 2: 2, 3: 3})

    def test_empty_key_string(self):
        """
        Test to see if there is an empty key in the dict. There is a design
        bug in Flash 9 which means that it cannot read this specific data.
        
        See http://www.docuverse.com/blog/donpark/2007/05/14/flash-9-amf3-bug
        for more info.
        """
        def x():
            self._run([({'': 1, 0: 1}, '\x09\x03\x01\x04\x01\x01\x04\x01')])

        self.failUnlessRaises(pyamf.EncodeError, x)

    def test_object(self):
        class Foo(object):
            pass

        pyamf.CLASS_CACHE = {}

        pyamf.register_class(Foo, 'com.collab.dev.pyamf.foo')

        obj = Foo()
        obj.baz = 'hello'

        self.e.writeElement(obj)

        self.assertEqual(self.buf.getvalue(), '\x0a\x13\x31\x63\x6f\x6d\x2e\x63\x6f\x6c\x6c\x61\x62'
            '\x2e\x64\x65\x76\x2e\x70\x79\x61\x6d\x66\x2e\x66\x6f\x6f\x07\x62'
            '\x61\x7a\x06\x0b\x68\x65\x6c\x6c\x6f')

    def test_byte_array(self):
        self._run([(amf3.ByteArray('hello'), '\x0c\x0bhello')])

class ParserTestCase(unittest.TestCase):
    def setUp(self):
        self.buf = util.BufferedByteStream()
        self.context = pyamf.Context()
        self.parser = amf3.Parser(context=self.context)
        self.parser.input = self.buf

    def _run(self, data):
        self.context.clear()
        e = ParserTester(self.parser, data)
        e.run(self)

    def test_types(self):
        for x in amf3.ACTIONSCRIPT_TYPES:
            self.buf.write(chr(x))
            self.buf.seek(0)
            self.parser.readType()
            self.buf.truncate(0)

        self.buf.write('x')
        self.buf.seek(0)
        self.assertRaises(pyamf.ParseError, self.parser.readType)

    def test_number(self):
        self._run([
            (0,    '\x04\x00'),
            (0.2,  '\x05\x3f\xc9\x99\x99\x99\x99\x99\x9a'),
            (1,    '\x04\x01'),
            (42,   '\x04\x2a'),
            (-123, '\x05\xc0\x5e\xc0\x00\x00\x00\x00\x00'),
            (1.23456789, '\x05\x3f\xf3\xc0\xca\x42\x83\xde\x1b')])

    def test_boolean(self):
        self._run([(True, '\x03'), (False, '\x02')])

    def test_null(self):
        self._run([(None, '\x01')])

    def test_undefined(self):
        self._run([(None, '\x00')])

    def test_string(self):
        self._run([
            ('', '\x06\x01'),
            ('hello', '\x06\x0bhello'),
            (u'ღმერთსი შემვედრე, ნუთუ კვლა დამხსნას სოფლისა შრომასა, ცეცხლს',
                '\x06\x82\x45\xe1\x83\xa6\xe1\x83\x9b\xe1\x83\x94\xe1\x83\xa0'
                '\xe1\x83\x97\xe1\x83\xa1\xe1\x83\x98\x20\xe1\x83\xa8\xe1\x83'
                '\x94\xe1\x83\x9b\xe1\x83\x95\xe1\x83\x94\xe1\x83\x93\xe1\x83'
                '\xa0\xe1\x83\x94\x2c\x20\xe1\x83\x9c\xe1\x83\xa3\xe1\x83\x97'
                '\xe1\x83\xa3\x20\xe1\x83\x99\xe1\x83\x95\xe1\x83\x9a\xe1\x83'
                '\x90\x20\xe1\x83\x93\xe1\x83\x90\xe1\x83\x9b\xe1\x83\xae\xe1'
                '\x83\xa1\xe1\x83\x9c\xe1\x83\x90\xe1\x83\xa1\x20\xe1\x83\xa1'
                '\xe1\x83\x9d\xe1\x83\xa4\xe1\x83\x9a\xe1\x83\x98\xe1\x83\xa1'
                '\xe1\x83\x90\x20\xe1\x83\xa8\xe1\x83\xa0\xe1\x83\x9d\xe1\x83'
                '\x9b\xe1\x83\x90\xe1\x83\xa1\xe1\x83\x90\x2c\x20\xe1\x83\xaa'
                '\xe1\x83\x94\xe1\x83\xaa\xe1\x83\xae\xe1\x83\x9a\xe1\x83\xa1'
                )])

    def test_string_references(self):
        self.parser.str_refs = []

        self._run([
            ('hello', '\x06\x0bhello'),
            ('hello', '\x06\x00'),
            ('hello', '\x06\x00')])

    def test_xml(self):
        self.buf.truncate(0)
        self.buf.write('\x07\x33<a><b>hello world</b></a>')
        self.buf.seek(0)

        self.assertEquals(
            util.ET.tostring(util.ET.fromstring('<a><b>hello world</b></a>')),
            util.ET.tostring(self.parser.readElement()))

    def test_xmlstring(self):
        self._run([
            ('<a><b>hello world</b></a>', '\x06\x33<a><b>hello world</b></a>')
        ])

    def test_list(self):
        self._run([
            ([], '\x09\x01\x01'),
            ([0, 1, 2, 3], '\x09\x09\x01\x04\x00\x04\x01\x04\x02\x04\x03'),
            (["Hello", 2, 3, 4, 5], '\x09\x0b\x01\x06\x0b\x48\x65\x6c\x6c\x6f'
                '\x04\x02\x04\x03\x04\x04\x04\x05')])

    def test_list_references(self):
        y = [0, 1, 2, 3]

        self._run([
            (y, '\x09\x09\x01\x04\x00\x04\x01\x04\x02\x04\x03'),
            (y, '\x09\x00')])

    def test_dict(self):
        self._run([
            ({0: u'hello', 'foo': u'bar'},
            '\x09\x03\x07\x66\x6f\x6f\x06\x07\x62\x61\x72\x01\x06\x0b\x68\x65'
            '\x6c\x6c\x6f')])
        self._run([({0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 'a': 'a'},
            '\x09\x0d\x03\x61\x06\x00\x01\x04\x00\x04\x01\x04\x02\x04\x03\x04'
            '\x04\x04\x05')])
        self._run([(
            {'a': u'a', 'b': u'b', 'c': u'c', 'd': u'd',
                0: 0, 1: 1, 2: 2, 3: 3},
            '\x09\x09\x03\x62\x06\x00\x03\x64\x06\x02\x03\x61\x06\x04\x03\x63'
            '\x06\x06\x01\x04\x00\x04\x01\x04\x02\x04\x03')
            ])
        self._run([
            ({'a': 1, 'b': 2}, '\x0a\x0b\x01\x03\x62\x04\x02\x03\x61\x04\x01'
                '\x01')])
        self._run([
            ({'baz': u'hello'}, '\x0a\x0b\x01\x07\x62\x61\x7a\x06\x0b\x68\x65'
                '\x6c\x6c\x6f\x01')])
        self._run([
            ({'baz': u'hello'}, '\x0a\x13\x01\x07\x62\x61\x7a\x06\x0b\x68\x65'
                '\x6c\x6c\x6f')])

    def test_object(self):
        class Foo(object):
            pass

        pyamf.CLASS_CACHE = {}

        pyamf.register_class(Foo, 'com.collab.dev.pyamf.foo')

        self.buf.truncate(0)
        self.buf.write('\x0a\x13\x31\x63\x6f\x6d\x2e\x63\x6f\x6c\x6c\x61\x62'
            '\x2e\x64\x65\x76\x2e\x70\x79\x61\x6d\x66\x2e\x66\x6f\x6f\x07\x62'
            '\x61\x7a\x06\x0b\x68\x65\x6c\x6c\x6f')
        self.buf.seek(0)

        obj = self.parser.readElement()

        self.assertEquals(obj.__class__, Foo)

        self.failUnless(hasattr(obj, 'baz'))
        self.assertEquals(obj.baz, 'hello')

    def test_byte_array(self):
        self._run([(amf3.ByteArray('hello'), '\x0c\x0bhello')])

    def test_date(self):
        import datetime

        self._run([
            (datetime.datetime(2005, 3, 18, 1, 58, 31),
                '\x08\x01Bp+6!\x15\x80\x00')])

class ModifiedUTF8TestCase(unittest.TestCase):
    data = [
        ('hello', '\x00\x05\x68\x65\x6c\x6c\x6f'),
        (u'ᚠᛇᚻ᛫ᛒᛦᚦ᛫ᚠᚱᚩᚠᚢᚱ᛫ᚠᛁᚱᚪ᛫ᚷᛖᚻᚹᛦᛚᚳᚢᛗᛋᚳᛖᚪᛚ᛫ᚦᛖᚪᚻ᛫ᛗᚪᚾᚾᚪ᛫ᚷᛖᚻᚹᛦᛚᚳ᛫ᛗᛁᚳᛚᚢᚾ᛫ᚻᛦᛏ᛫ᛞᚫ'
            u'ᛚᚪᚾᚷᛁᚠ᛫ᚻᛖ᛫ᚹᛁᛚᛖ᛫ᚠᚩᚱ᛫ᛞᚱᛁᚻᛏᚾᛖ᛫ᛞᚩᛗᛖᛋ᛫ᚻᛚᛇᛏᚪᚾ᛬',
            '\x01\x41\xe1\x9a\xa0\xe1\x9b\x87\xe1\x9a\xbb\xe1\x9b\xab\xe1\x9b'
            '\x92\xe1\x9b\xa6\xe1\x9a\xa6\xe1\x9b\xab\xe1\x9a\xa0\xe1\x9a\xb1'
            '\xe1\x9a\xa9\xe1\x9a\xa0\xe1\x9a\xa2\xe1\x9a\xb1\xe1\x9b\xab\xe1'
            '\x9a\xa0\xe1\x9b\x81\xe1\x9a\xb1\xe1\x9a\xaa\xe1\x9b\xab\xe1\x9a'
            '\xb7\xe1\x9b\x96\xe1\x9a\xbb\xe1\x9a\xb9\xe1\x9b\xa6\xe1\x9b\x9a'
            '\xe1\x9a\xb3\xe1\x9a\xa2\xe1\x9b\x97\xe1\x9b\x8b\xe1\x9a\xb3\xe1'
            '\x9b\x96\xe1\x9a\xaa\xe1\x9b\x9a\xe1\x9b\xab\xe1\x9a\xa6\xe1\x9b'
            '\x96\xe1\x9a\xaa\xe1\x9a\xbb\xe1\x9b\xab\xe1\x9b\x97\xe1\x9a\xaa'
            '\xe1\x9a\xbe\xe1\x9a\xbe\xe1\x9a\xaa\xe1\x9b\xab\xe1\x9a\xb7\xe1'
            '\x9b\x96\xe1\x9a\xbb\xe1\x9a\xb9\xe1\x9b\xa6\xe1\x9b\x9a\xe1\x9a'
            '\xb3\xe1\x9b\xab\xe1\x9b\x97\xe1\x9b\x81\xe1\x9a\xb3\xe1\x9b\x9a'
            '\xe1\x9a\xa2\xe1\x9a\xbe\xe1\x9b\xab\xe1\x9a\xbb\xe1\x9b\xa6\xe1'
            '\x9b\x8f\xe1\x9b\xab\xe1\x9b\x9e\xe1\x9a\xab\xe1\x9b\x9a\xe1\x9a'
            '\xaa\xe1\x9a\xbe\xe1\x9a\xb7\xe1\x9b\x81\xe1\x9a\xa0\xe1\x9b\xab'
            '\xe1\x9a\xbb\xe1\x9b\x96\xe1\x9b\xab\xe1\x9a\xb9\xe1\x9b\x81\xe1'
            '\x9b\x9a\xe1\x9b\x96\xe1\x9b\xab\xe1\x9a\xa0\xe1\x9a\xa9\xe1\x9a'
            '\xb1\xe1\x9b\xab\xe1\x9b\x9e\xe1\x9a\xb1\xe1\x9b\x81\xe1\x9a\xbb'
            '\xe1\x9b\x8f\xe1\x9a\xbe\xe1\x9b\x96\xe1\x9b\xab\xe1\x9b\x9e\xe1'
            '\x9a\xa9\xe1\x9b\x97\xe1\x9b\x96\xe1\x9b\x8b\xe1\x9b\xab\xe1\x9a'
            '\xbb\xe1\x9b\x9a\xe1\x9b\x87\xe1\x9b\x8f\xe1\x9a\xaa\xe1\x9a\xbe'
            '\xe1\x9b\xac')]

    def test_encode(self):
        for x in self.data:
            self.assertEqual(amf3.encode_utf8_modified(x[0]), x[1])

    def test_decode(self):
        for x in self.data:
            self.assertEqual(amf3.decode_utf8_modified(x[1]), x[0])

def suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(TypesTestCase, 'test'))
    suite.addTest(unittest.makeSuite(ModifiedUTF8TestCase, 'test'))
    suite.addTest(unittest.makeSuite(EncoderTestCase, 'test'))
    suite.addTest(unittest.makeSuite(ParserTestCase, 'test'))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
