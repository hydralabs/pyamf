# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Tests for AMF3 Implementation.

@author: U{Arnar Birgisson<mailto:arnarbi@gmail.com>}
@author: U{Thijs Triemstra<mailto:info@collab.nl>}
@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import unittest

import pyamf
from pyamf import amf3, util
from pyamf.tests.util import EncoderTester, DecoderTester

class Foo(object):
    """
    A generic object to use for object encoding
    """
    def __init__(self, d={}):
        self.__dict__ = dict(d)

class TypesTestCase(unittest.TestCase):
    """
    Tests the type mappings.
    """
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

class ContextTestCase(unittest.TestCase):
    def test_create(self):
        c = amf3.Context()

        self.assertEquals(c.strings, [])
        self.assertEquals(c.objects, [])
        self.assertEquals(c.classes, [])
        self.assertEquals(c.legacy_xml, [])
        self.assertEquals(len(c.strings), 0)
        self.assertEquals(len(c.classes), 0)
        self.assertEquals(len(c.objects), 0)
        self.assertEquals(len(c.legacy_xml), 0)

    def test_add_object(self):
        x = amf3.Context()
        y = [1, 2, 3]

        self.assertEquals(x.addObject(y), 0)
        self.assertTrue(y in x.objects)
        self.assertEquals(len(x.objects), 1)

    def test_add_string(self):
        x = amf3.Context()
        y = 'abc'

        self.assertEquals(x.addString(y), 0)
        self.assertTrue(y in x.strings)
        self.assertEquals(len(x.strings), 1)

    def test_add_class(self):
        x = amf3.Context()

        # TODO nick: fill this out ...

    def test_add_legacy_xml(self):
        x = amf3.Context()
        y = 'abc'

        self.assertEquals(x.addLegacyXML(y), 0)
        self.assertTrue(y in x.legacy_xml)
        self.assertEquals(len(x.legacy_xml), 1)

    def test_clear(self):
        x = amf3.Context()
        y = [1, 2, 3]
        z = '<a></a>'

        x.addObject(y)
        x.strings.append('foobar')
        x.addLegacyXML(z)
        x.clear()

        self.assertEquals(x.objects, [])
        self.assertEquals(len(x.objects), 0)
        self.assertFalse(y in x.objects)

        self.assertEquals(x.strings, [])
        self.assertEquals(len(x.strings), 0)
        self.assertFalse('foobar' in x.strings)

        self.assertEquals(x.legacy_xml, [])
        self.assertEquals(len(x.legacy_xml), 0)
        self.assertFalse('<a></a>' in x.legacy_xml)

    def test_get_by_reference(self):
        x = amf3.Context()
        y = [1, 2, 3]
        z = {'foo': 'bar'}

        x.addObject(y)
        x.addObject(z)
        x.addString('abc')
        x.addString('def')
        x.addLegacyXML('<a></a>')
        x.addLegacyXML('<b></b>')

        self.assertEquals(x.getObject(0), y)
        self.assertEquals(x.getObject(1), z)
        self.assertRaises(pyamf.ReferenceError, x.getObject, 2)
        self.assertRaises(TypeError, x.getObject, '')
        self.assertRaises(TypeError, x.getObject, 2.2323)

        self.assertEquals(x.getString(0), 'abc')
        self.assertEquals(x.getString(1), 'def')
        self.assertRaises(pyamf.ReferenceError, x.getString, 2)
        self.assertRaises(TypeError, x.getString, '')
        self.assertRaises(TypeError, x.getString, 2.2323)

        self.assertEquals(x.getLegacyXML(0), '<a></a>')
        self.assertEquals(x.getLegacyXML(1), '<b></b>')
        self.assertRaises(pyamf.ReferenceError, x.getLegacyXML, 2)

    def test_empty_string(self):
        x = amf3.Context()

        self.assertRaises(ValueError, x.addString, '')

    def test_get_reference(self):
        x = amf3.Context()
        y = [1, 2, 3]
        z = {'foo': 'bar'}

        ref1 = x.addObject(y)
        ref2 = x.addObject(z)
        x.addString('abc')
        x.addString('def')
        x.addLegacyXML('<a></a>')
        x.addLegacyXML('<b></b>')

        self.assertEquals(x.getObjectReference(y), ref1)
        self.assertEquals(x.getObjectReference(z), ref2)
        self.assertRaises(pyamf.ReferenceError, x.getObjectReference, {})

        self.assertEquals(x.getStringReference('abc'), 0)
        self.assertEquals(x.getStringReference('def'), 1)
        self.assertRaises(pyamf.ReferenceError, x.getStringReference, 'asdfas')

        self.assertEquals(x.getLegacyXMLReference('<a></a>'), 0)
        self.assertEquals(x.getLegacyXMLReference('<b></b>'), 1)
        self.assertRaises(pyamf.ReferenceError, x.getLegacyXMLReference, '<c/>')

    def test_copy(self):
        import copy

        old = amf3.Context()

        old.addObject([1, 2, 3])
        old.addString('asdfasdf')

        new = copy.copy(old)

        self.assertEquals(new.objects, [])
        self.assertEquals(len(new.objects), 0)

        self.assertEquals(new.strings, [])
        self.assertEquals(len(new.strings), 0)

        self.assertEquals(new.classes, [])
        self.assertEquals(len(new.classes), 0)

        self.assertEquals(new.legacy_xml, [])
        self.assertEquals(len(new.legacy_xml), 0)

class ClassDefinitionTestCase(unittest.TestCase):
    def test_create(self):
        x = amf3.ClassDefinition('')

        self.assertEquals(x.alias, None)
        self.assertEquals(x.encoding, 0)
        self.assertEquals(x.attrs, [])
        self.assertEquals(len(x.attrs), 0)
        self.assertEquals(x.num_attrs, None)

        x = amf3.ClassDefinition(None)

        self.assertEquals(x.alias, None)
        self.assertEquals(x.encoding, 0)
        self.assertEquals(x.attrs, [])
        self.assertEquals(len(x.attrs), 0)
        self.assertEquals(x.num_attrs, None)

        pyamf.register_class(Foo, 'foo.bar')

        x = amf3.ClassDefinition('foo.bar')
        self.assertTrue(isinstance(x.alias, pyamf.ClassAlias))
        self.assertEquals(x.alias, pyamf.get_class_alias('foo.bar'))
        self.assertEquals(x.encoding, 0)
        self.assertEquals(x.attrs, [])
        self.assertEquals(len(x.attrs), 0)
        self.assertEquals(x.num_attrs, None)

        pyamf.unregister_class(Foo)

    def test_name(self):
        x = amf3.ClassDefinition('')
        self.assertEquals(x.name, '')

        x = amf3.ClassDefinition(None)
        self.assertEquals(x.name, '')

        pyamf.register_class(Foo, 'foo.bar')

        x = amf3.ClassDefinition('foo.bar')
        self.assertEquals(x.name, 'foo.bar')

        pyamf.unregister_class(Foo)

    def test_get_class(self):
        # anonymous class
        x = amf3.ClassDefinition('')
        self.assertEquals(x.getClass(), pyamf.ASObject)

        x = amf3.ClassDefinition(None)
        self.assertEquals(x.getClass(), pyamf.ASObject)

        pyamf.register_class(Foo, 'foo.bar')

        x = amf3.ClassDefinition('foo.bar')
        self.assertEquals(x.getClass(), Foo)

        pyamf.unregister_class(Foo)

    def test_get_alias(self):
        pyamf.register_class(Foo, 'foo.bar')

        x = amf3.ClassDefinition('foo.bar')
        alias = x.getClassAlias()

        self.assertEquals(alias.klass, Foo)
        self.assertEquals(alias.alias, 'foo.bar')

        pyamf.unregister_class(Foo)

        x = amf3.ClassDefinition(None)
        self.assertRaises(pyamf.UnknownClassAlias, x.getClassAlias)

        x = amf3.ClassDefinition('')
        self.assertRaises(pyamf.UnknownClassAlias, x.getClassAlias)

class EncoderTestCase(unittest.TestCase):
    """
    Tests the output from the AMF3 L{Encoder<pyamf.amf3.Encoder>} class.
    """
    def setUp(self):
        self.buf = util.BufferedByteStream()
        self.context = amf3.Context()
        self.encoder = amf3.Encoder(self.buf, context=self.context)

    def _run(self, data):
        self.context.clear()

        e = EncoderTester(self.encoder, data)
        e.run(self)

    def test_undefined(self):
        def x():
            self._run([(ord, '\x00')])

        self.assertRaises(AttributeError, x)

        self._run([(pyamf.Undefined, '\x00')])

    def test_null(self):
        self._run([(None, '\x01')])

    def test_boolean(self):
        self._run([(True, '\x03'), (False, '\x02')])

    def test_integer(self):
        self._run([(0, '\x04\x00')])
        self._run([(0x7f, '\x04\x7f')])
        self._run([(0x80, '\x04\x81\x00')])
        self._run([(0x3fff, '\x04\xff\x7f')])
        self._run([(0x4000, '\x04\x81\x80\x00')])
        self._run([(0x1fffff, '\x04\xff\xff\x7f')])
        self._run([(0x200000, '\x04\x80\xc0\x80\x00')])
        self._run([(0x3fffffff, '\x04\xff\xff\xff\xff')])

    def test_number(self):
        self._run([
            (0.1, '\x05\x3f\xb9\x99\x99\x99\x99\x99\x9a'),
            (0.123456789, '\x05\x3f\xbf\x9a\xdd\x37\x39\x63\x5f')])

    def test_string(self):
        self._run([
            ('hello', '\x06\x0bhello'),
            (u'ᚠᛇᚻ', '\x06\x07\xe1\x9a\xa0\xe1\x9b\x87\xe1\x9a\xbb')])

    def test_string_references(self):
        self._run([
            ('hello', '\x06\x0bhello'),
            ('hello', '\x06\x00'),
            ('hello', '\x06\x00')])

    def test_date(self):
        import datetime

        x = datetime.datetime(2005, 3, 18, 1, 58, 31)

        self._run([
            (x, '\x08\x01Bp+6!\x15\x80\x00'),
            (datetime.date(2003, 12, 1), '\x08\x01Bo%\xe2\xb2\x80\x00\x00')])

    def test_date_references(self):
        import datetime

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
            ({'foo': 'bar'}, '\n\x13\x01\x07foo\x06\x07bar')])

        self._run([
            ({'a': u'a', 'b': u'b', 'c': u'c', 'd': u'd'}, '\nC\x01\x03a\x03c'
                '\x03b\x03d\x06\x00\x06\x02\x06\x04\x06\x06')])

        x = amf3.Decoder('\nC\x01\x03a\x03c\x03b\x03d\x06\x00\x06\x02\x06\x04\x06\x06')
        self.assertEqual(x.readElement(), {'a': u'a', 'b': u'b', 'c': u'c', 'd': u'd'})

    def test_mixed_array(self):
        x = pyamf.MixedArray()
        x.update({0:u'hello', 'foo': u'bar'})
        
        self._run([
            (x, '\x09\x03\x07\x66\x6f\x6f\x06\x07\x62\x61\x72\x01\x06\x0b\x68'
                '\x65\x6c\x6c\x6f')])

        x = pyamf.MixedArray()
        x.update({0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 'a': 'a'})
        self._run([(x, '\x09\x0d\x03\x61\x06\x00\x01\x04\x00\x04\x01\x04\x02'
            '\x04\x03\x04\x04\x04\x05')])

        x = amf3.Decoder('\x09\x09\x03\x62\x06\x00\x03\x64\x06\x02\x03\x61\x06'
        '\x04\x03\x63\x06\x06\x01\x04\x00\x04\x01\x04\x02\x04\x03')

        y = x.readElement()
        self.assertTrue(isinstance(y,pyamf.MixedArray))
        self.assertEqual(y, {'a': u'a', 'b': u'b', 'c': u'c', 'd': u'd',
                0: 0, 1: 1, 2: 2, 3: 3})

    def test_empty_key_string(self):
        """
        Test to see if there is an empty key in the dict. There is a design
        bug in Flash 9 which means that it cannot read this specific data.

        @bug: See U{http://www.docuverse.com/blog/donpark/2007/05/14/flash-9-amf3-bug}
        for more info.
        """
        def x():
            y = pyamf.MixedArray()
            y.update({'': 1, 0: 1})
            self._run([(y, '\x09\x03\x01\x04\x01\x01\x04\x01')])

        self.failUnlessRaises(pyamf.EncodeError, x)

    def test_object(self):
        self._run([
            ({'a': u'foo', 'b': 5},
                '\n\x23\x01\x03a\x03b\x06\x07foo\x04\x05')])

        pyamf.register_class(Foo, 'com.collab.dev.pyamf.foo')

        obj = Foo()
        obj.baz = 'hello'

        self.encoder.writeElement(obj)

        self.assertEqual(self.buf.getvalue(), '\n\x131com.collab.dev.pyamf.foo'
            '\x07baz\x06\x0bhello')

        pyamf.unregister_class(Foo)

    def test_byte_array(self):
        self._run([(amf3.ByteArray('hello'), '\x0c\x0bhello')])

    def test_xml(self):
        x = util.ET.fromstring('<a><b>hello world</b></a>')
        self.context.addLegacyXML(x)
        self.encoder.writeElement(x)

        self.assertEquals(self.buf.getvalue(),
            '\x07\x33<a><b>hello world</b></a>')
        self.buf.truncate()
        self.encoder.writeElement(x)

        self.assertEquals(self.buf.getvalue(), '\x07\x00')

    def test_xmlstring(self):
        x = util.ET.fromstring('<a><b>hello world</b></a>')
        self.encoder.writeElement(x)

        self.assertEquals(self.buf.getvalue(),
            '\x0b\x33<a><b>hello world</b></a>')
        self.buf.truncate()

        self.encoder.writeElement(x)
        self.assertEquals(self.buf.getvalue(), '\x0b\x00')

    def test_get_class_definition(self):
        pyamf.register_class(Foo, 'abc.xyz')

        x = Foo({'foo': 'bar'})

        class_def = self.encoder._getClassDefinition(x)

        self.assertEquals(class_def.name, 'abc.xyz')
        self.assertEquals(class_def.klass, Foo)
        self.assertEquals(class_def.attrs, ['foo'])

        pyamf.unregister_class(Foo)

        # test anonymous object
        x = {'foo': 'bar'}

        class_def = self.encoder._getClassDefinition(x)

        self.assertEquals(class_def.name, '')
        self.assertEquals(class_def.klass, pyamf.ASObject)
        self.assertEquals(class_def.attrs, ['foo'])

        # test supplied attributes
        attrs = ['foo', 'bar']
        pyamf.register_class(Foo, 'abc.xyz', attrs=attrs)

        x = Foo({'foo': 'bar'})

        class_def = self.encoder._getClassDefinition(x)

        self.assertEquals(class_def.name, 'abc.xyz')
        self.assertEquals(class_def.klass, Foo)
        self.assertEquals(class_def.attrs, attrs)
        self.assertNotEquals(id(class_def.attrs), id(attrs))

        pyamf.unregister_class(Foo)

    def test_anonymous(self):
        pyamf.register_class(Foo)

        x = Foo({'foo': 'bar'})

        self._run([(x, '\n\x13\x01\x07foo\x06\x07bar')])
        pyamf.unregister_class(Foo)

    def test_custom_type(self):
        def write_as_list(list_interface_obj):
            list_interface_obj.ran = True

            return list(list_interface_obj)

        class ListWrapper(object):
            ran = False

            def __iter__(self):
                return iter([1, 2, 3])

        pyamf.add_type(ListWrapper, write_as_list)
        x = ListWrapper()

        self.encoder.writeElement(x)
        self.assertEquals(x.ran, True)

        self.assertEquals(self.buf.getvalue(), '\t\x07\x01\x04\x01\x04\x02\x04\x03')

class DecoderTestCase(unittest.TestCase):
    """
    Tests the output from the AMF3 L{Decoder<pyamf.amf3.Decoder>} class.
    """
    def setUp(self):
        self.buf = util.BufferedByteStream()
        self.context = amf3.Context()
        self.decoder = amf3.Decoder(context=self.context)
        self.decoder.stream = self.buf

    def _run(self, data):
        self.context.clear()
        e = DecoderTester(self.decoder, data)
        e.run(self)

    def test_types(self):
        for x in amf3.ACTIONSCRIPT_TYPES:
            self.buf.write(chr(x))
            self.buf.seek(0)
            self.decoder.readType()
            self.buf.truncate(0)

        self.buf.write('x')
        self.buf.seek(0)
        self.assertRaises(pyamf.DecodeError, self.decoder.readType)

    def test_undefined(self):
        self._run([(pyamf.Undefined, '\x00')])

    def test_number(self):
        self._run([
            (0,    '\x04\x00'),
            (0.2,  '\x05\x3f\xc9\x99\x99\x99\x99\x99\x9a'),
            (1,    '\x04\x01'),
            (42,   '\x04\x2a'),
            (-123, '\x05\xc0\x5e\xc0\x00\x00\x00\x00\x00'),
            (1.23456789, '\x05\x3f\xf3\xc0\xca\x42\x83\xde\x1b')])

    def test_integer(self):
        self._run([(0, '\x04\x00')])
        self._run([(0x7f, '\x04\x7f')])
        self._run([(0x80, '\x04\x81\x00')])
        self._run([(0x3fff, '\x04\xff\x7f')])
        self._run([(0x4000, '\x04\x81\x80\x00')])
        self._run([(0x1fffff, '\x04\xff\xff\x7f')])
        self._run([(0x200000, '\x04\x80\xc0\x80\x00')])
        self._run([(0x3fffffff, '\x04\xff\xff\xff\xff')])

    def test_boolean(self):
        self._run([(True, '\x03'), (False, '\x02')])

    def test_null(self):
        self._run([(None, '\x01')])

    def test_undefined(self):
        self._run([(pyamf.Undefined, '\x00')])

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
        self.decoder.str_refs = []

        self._run([
            ('hello', '\x06\x0bhello'),
            ('hello', '\x06\x00'),
            ('hello', '\x06\x00')])

    def test_xml(self):
        self.buf.write('\x07\x33<a><b>hello world</b></a>')
        self.buf.seek(0, 0)
        x = self.decoder.readElement()

        self.assertEquals(util.ET.tostring(x), '<a><b>hello world</b></a>')
        self.assertEquals(self.context.getLegacyXMLReference(x), 0)

        self.buf.truncate()
        self.buf.write('\x07\x00')
        self.buf.seek(0, 0)
        y = self.decoder.readElement()

        self.assertEquals(x, y)

    def test_xmlstring(self):
        self.buf.write('\x0b\x33<a><b>hello world</b></a>')
        self.buf.seek(0, 0)
        x = self.decoder.readElement()

        self.assertEquals(util.ET.tostring(x), '<a><b>hello world</b></a>')
        self.assertRaises(pyamf.ReferenceError,
            self.context.getLegacyXMLReference, x)

        self.buf.truncate()
        self.buf.write('\x0b\x00')
        self.buf.seek(0, 0)
        y = self.decoder.readElement()

        self.assertEquals(x, y)

    def test_list(self):
        self._run([
            ([], '\x09\x01\x01'),
            ([0, 1, 2, 3], '\x09\x09\x01\x04\x00\x04\x01\x04\x02\x04\x03'),
            (["Hello", 2, 3, 4, 5], '\x09\x0b\x01\x06\x0b\x48\x65\x6c\x6c\x6f'
                '\x04\x02\x04\x03\x04\x04\x04\x05')])

    def test_list_references(self):
        y = [0, 1, 2, 3]
        z = [0, 1, 2]

        self._run([
            (y, '\x09\x09\x01\x04\x00\x04\x01\x04\x02\x04\x03'),
            (y, '\x09\x00'),
            (z, '\x09\x07\x01\x04\x00\x04\x01\x04\x02'),
            (z, '\x09\x02')])

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
        pyamf.register_class(Foo, 'com.collab.dev.pyamf.foo')

        self.buf.truncate(0)
        self.buf.write('\x0a\x13\x31\x63\x6f\x6d\x2e\x63\x6f\x6c\x6c\x61\x62'
            '\x2e\x64\x65\x76\x2e\x70\x79\x61\x6d\x66\x2e\x66\x6f\x6f\x07\x62'
            '\x61\x7a\x06\x0b\x68\x65\x6c\x6c\x6f')
        self.buf.seek(0)

        obj = self.decoder.readElement()

        self.assertEquals(obj.__class__, Foo)

        self.failUnless(hasattr(obj, 'baz'))
        self.assertEquals(obj.baz, 'hello')

        pyamf.unregister_class(Foo)

    def test_byte_array(self):
        self._run([(amf3.ByteArray('hello'), '\x0c\x0bhello')])

    def test_date(self):
        import datetime

        self._run([
            (datetime.datetime(2005, 3, 18, 1, 58, 31),
                '\x08\x01Bp+6!\x15\x80\x00')])

    def test_get_class_definition(self):
        pyamf.register_class(Foo, 'abc.xyz')

        self.buf.write('\x0fabc.xyz')
        self.buf.seek(0, 0)

        is_ref, class_def = self.decoder._getClassDefinition(0x01)

        self.assertFalse(is_ref)
        self.assertTrue(isinstance(class_def, amf3.ClassDefinition))
        self.assertTrue(class_def.getClass(), Foo)
        self.assertTrue(class_def.name, 'abc.xyz')
        self.assertEquals(class_def.encoding, amf3.ObjectEncoding.STATIC)

        self.assertTrue(class_def in self.context.classes)

        self.context.classes.remove(class_def)
        self.buf.write('\x0fabc.xyz')
        self.buf.seek(0, 0)

        is_ref, class_def = self.decoder._getClassDefinition(0x03)

        self.assertFalse(is_ref)
        self.assertTrue(isinstance(class_def, amf3.ClassDefinition))
        self.assertTrue(class_def.getClass(), Foo)
        self.assertTrue(class_def.name, 'abc.xyz')
        self.assertEquals(class_def.encoding, amf3.ObjectEncoding.EXTERNAL)

        self.assertTrue(class_def in self.context.classes)

        self.context.classes.remove(class_def)
        self.buf.write('\x0fabc.xyz')
        self.buf.seek(0, 0)

        is_ref, class_def = self.decoder._getClassDefinition(0x05)

        self.assertFalse(is_ref)
        self.assertTrue(isinstance(class_def, amf3.ClassDefinition))
        self.assertTrue(class_def.getClass(), Foo)
        self.assertTrue(class_def.name, 'abc.xyz')
        self.assertEquals(class_def.encoding, amf3.ObjectEncoding.DYNAMIC)

        self.assertTrue(class_def in self.context.classes)
        self.context.classes.remove(class_def)

        pyamf.unregister_class(Foo)

class ObjectEncodingTestCase(unittest.TestCase):
    def setUp(self):
        self.stream = util.BufferedByteStream()
        self.context = amf3.Context()
        self.encoder = amf3.Encoder(self.stream, self.context)

    def test_object_references(self):
        obj = pyamf.ASObject(a='b')

        self.encoder.writeElement(obj)
        pos = self.stream.tell()
        self.encoder.writeElement(obj)
        self.assertEquals(self.stream.getvalue()[pos:], '\x0a\x00')
        self.stream.truncate()

        self.encoder.writeElement(obj)
        self.assertEquals(self.stream.getvalue(), '\x0a\x00')
        self.stream.truncate()

        self.encoder.writeElement(obj, False)
        self.assertNotEquals(self.stream.getvalue(), '\x0a\x00')

    def test_class_references(self):
        pyamf.register_class(Foo, 'abc.xyz')

        x = Foo({'foo': 'bar'})
        y = Foo({'foo': 'baz'})

        self.encoder.writeElement(x)

        pyamf.unregister_class(Foo)

        #self.assertEquals(self.stream.getvalue(), '\x0a\x03')
        #from pyamf.util import hexdump
        #print hexdump(self.stream.getvalue())

        #pos = self.stream.tell()
        #self.encoder.writeElement(y)
        #self.assertEquals(self.stream.getvalue()[pos:], '\x0a\x00')

    def test_static(self):
        pyamf.register_class(Foo, 'abc.xyz', metadata='static')

        x = Foo({'foo': 'bar'})
        self.encoder.writeElement(x)
        buf = self.stream.getvalue()

        # an inline object with and inline class-def, encoding = 0x00, 1 attr
        self.assertEquals(buf[:2], '\x0a\x13')
        # class alias name
        self.assertEquals(buf[2:10], '\x0fabc.xyz')
        # first key
        self.assertEquals(buf[10:14], '\x07foo')
        # first value
        self.assertEquals(buf[14:19], '\x06\x07bar')

        self.assertEquals(len(buf), 19)

        pyamf.unregister_class(Foo)

    def test_dynamic(self):
        pyamf.register_class(Foo, 'abc.xyz', metadata='dynamic')

        x = Foo({'foo': 'bar'})
        self.encoder.writeElement(x)

        buf = self.stream.getvalue()

        # an inline object with and inline class-def, encoding = 0x01, 1 attr
        self.assertEquals(buf[:2], '\x0a\x1b')
        # class alias name
        self.assertEquals(buf[2:10], '\x0fabc.xyz')
        # first key
        self.assertEquals(buf[10:14], '\x07foo')
        # first value
        self.assertEquals(buf[14:19], '\x06\x07bar')
        # empty key
        self.assertEquals(buf[19:21], '\x06\x01')

        self.assertEquals(len(buf), 21)

        pyamf.unregister_class(Foo)

    def test_external(self):
        def read(self, x):
            pass

        pyamf.register_class(Foo, 'abc.xyz', read_func=read, write_func=read)

        x = Foo({'foo': 'bar'})
        self.encoder.writeElement(x)

        buf = self.stream.getvalue()

        # an inline object with and inline class-def, encoding = 0x01, 1 attr

        self.assertEquals(buf[:2], '\x0a\x07')
        # class alias name
        self.assertEquals(buf[2:10], '\x0fabc.xyz')

        self.assertEquals(len(buf), 10)

        pyamf.unregister_class(Foo)

class ObjectDecodingTestCase(unittest.TestCase):
    def setUp(self):
        self.stream = util.BufferedByteStream()
        self.context = amf3.Context()
        self.decoder = amf3.Decoder(self.stream, self.context)

    def test_object_references(self):
        self.stream.write('\x0a\x23\x01\x03a\x03b\x06\x07foo\x04\x05')
        self.stream.seek(0, 0)

        obj1 = self.decoder.readElement()

        self.stream.truncate()
        self.stream.write('\n\x00')
        self.stream.seek(0, 0)

        obj2 = self.decoder.readElement()

        self.assertEquals(id(obj1), id(obj2))

    def test_class_references(self):
        pass

    def test_static(self):
        pyamf.register_class(Foo, 'abc.xyz', metadata='static')

        self.assertEquals(self.context.objects, [])
        self.assertEquals(self.context.strings, [])
        self.assertEquals(self.context.classes, [])

        self.stream.write('\x0a\x13\x0fabc.xyz\x07foo\x06\x07bar')
        self.stream.seek(0, 0)

        obj = self.decoder.readElement()

        class_def = self.context.classes[0]

        self.assertEquals(class_def.attrs, ['foo'])
        self.assertEquals(class_def.num_attrs, 1)

        self.assertTrue(isinstance(obj, Foo))
        self.assertEquals(obj.__dict__, {'foo': 'bar'})

        pyamf.unregister_class(Foo)

    def test_dynamic(self):
        pyamf.register_class(Foo, 'abc.xyz', metadata='dynamic')

        self.assertEquals(self.context.objects, [])
        self.assertEquals(self.context.strings, [])
        self.assertEquals(self.context.classes, [])

        self.stream.write('\x0a\x0b\x0fabc.xyz\x07foo\x06\x07bar\x01')
        self.stream.seek(0, 0)

        obj = self.decoder.readElement()

        class_def = self.context.classes[0]

        self.assertEquals(class_def.attrs, [])
        self.assertEquals(class_def.num_attrs, 0)

        self.assertTrue(isinstance(obj, Foo))
        self.assertEquals(obj.__dict__, {'foo': 'bar'})

        pyamf.unregister_class(Foo)

    def test_combined(self):
        """
        This tests an object encoding with static properties and dynamic
        properties
        """
        pyamf.register_class(Foo, 'abc.xyz', metadata='dynamic')

        self.assertEquals(self.context.objects, [])
        self.assertEquals(self.context.strings, [])
        self.assertEquals(self.context.classes, [])

        self.stream.write('\x0a\x1b\x0fabc.xyz\x07foo\x06\x07bar\x07baz\x06\x07'
            'nat\x01')
        self.stream.seek(0, 0)

        obj = self.decoder.readElement()

        class_def = self.context.classes[0]

        self.assertEquals(class_def.attrs, ['foo'])
        self.assertEquals(class_def.num_attrs, 1)

        self.assertTrue(isinstance(obj, Foo))
        self.assertEquals(obj.__dict__, {'foo': 'bar', 'baz': 'nat'})

        pyamf.unregister_class(Foo)

    def test_external(self):
        pass

class DataOutputTestCase(unittest.TestCase):
    def setUp(self):
        self.stream = util.BufferedByteStream()
        self.encoder = amf3.Encoder(self.stream)

    def test_create(self):
        x = amf3.DataOutput(self.encoder)

        self.assertEquals(x.encoder, self.encoder)
        self.assertEquals(x.stream, self.stream)
        self.assertEquals(x.stream, self.encoder.stream)

    def test_boolean(self):
        x = amf3.DataOutput(self.encoder)

        x.writeBoolean(True)
        self.assertEquals(self.stream.getvalue(), '\x01')
        self.stream.truncate()

        x.writeBoolean(False)
        self.assertEquals(self.stream.getvalue(), '\x00')

    def test_byte(self):
        x = amf3.DataOutput(self.encoder)

        for y in xrange(10):
            x.writeByte(y)

        self.assertEquals(self.stream.getvalue(),
            '\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09')

    def test_double(self):
        x = amf3.DataOutput(self.encoder)

        x.writeDouble(0.0)
        self.assertEquals(self.stream.getvalue(), '\x00' * 8)
        self.stream.truncate()

        x.writeDouble(1234.5678)
        self.assertEquals(self.stream.getvalue(), '@\x93JEm\\\xfa\xad')

    def test_float(self):
        x = amf3.DataOutput(self.encoder)

        x.writeFloat(0.0)
        self.assertEquals(self.stream.getvalue(), '\x00' * 4)
        self.stream.truncate()

        x.writeFloat(1234.5678)
        self.assertEquals(self.stream.getvalue(), 'D\x9aR+')

    def test_int(self):
        x = amf3.DataOutput(self.encoder)

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
        x = amf3.DataOutput(self.encoder)

        x.writeMultiByte('this is a test', 'utf-8')
        self.assertEquals(self.stream.getvalue(), u'this is a test')
        self.stream.truncate()

        x.writeMultiByte(u'ἔδωσαν', 'utf-8')
        self.assertEquals(self.stream.getvalue(), '\xe1\xbc\x94\xce\xb4\xcf'
            '\x89\xcf\x83\xce\xb1\xce\xbd')

    def test_object(self):
        x = amf3.DataOutput(self.encoder)
        obj = pyamf.MixedArray(foo='bar')

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
        x = amf3.DataOutput(self.encoder)

        x.writeShort(55)
        self.assertEquals(self.stream.getvalue(), '\x007')
        self.stream.truncate()

        x.writeShort(-55)
        self.assertEquals(self.stream.getvalue(), '\xff\xc9')

    def test_uint(self):
        x = amf3.DataOutput(self.encoder)

        x.writeUnsignedInt(55)
        self.assertEquals(self.stream.getvalue(), '\x00\x00\x007')
        self.stream.truncate()

        self.assertRaises(ValueError, x.writeUnsignedInt, -55)

    def test_utf(self):
        x = amf3.DataOutput(self.encoder)

        x.writeUTF(u'ἔδωσαν')

        self.assertEquals(self.stream.getvalue(), '\r\xe1\xbc\x94\xce'
            '\xb4\xcf\x89\xcf\x83\xce\xb1\xce\xbd')

    def test_utf_bytes(self):
        x = amf3.DataOutput(self.encoder)

        x.writeUTFBytes(u'ἔδωσαν')

        self.assertEquals(self.stream.getvalue(),
            '\xe1\xbc\x94\xce\xb4\xcf\x89\xcf\x83\xce\xb1\xce\xbd')

class DataInputTestCase(unittest.TestCase):
    def setUp(self):
        self.stream = util.BufferedByteStream()
        self.decoder = amf3.Decoder(self.stream)

    def test_create(self):
        x = amf3.DataInput(self.decoder)

        self.assertEquals(x.decoder, self.decoder)
        self.assertEquals(x.stream, self.stream)
        self.assertEquals(x.stream, self.decoder.stream)

    def _test(self, bytes, value, func, *params):
        self.stream.write(bytes)
        self.stream.seek(0)

        self.assertEquals(func(*params), value)
        self.stream.truncate()

    def test_boolean(self):
        x = amf3.DataInput(self.decoder)

        self.stream.write('\x01')
        self.stream.seek(-1, 2)
        self.assertEquals(x.readBoolean(), True)

        self.stream.write('\x00')
        self.stream.seek(-1, 2)
        self.assertEquals(x.readBoolean(), False)

    def test_byte(self):
        x = amf3.DataInput(self.decoder)

        self.stream.write('\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09')
        self.stream.seek(0)

        for y in xrange(10):
            self.assertEquals(x.readByte(), y)

    def test_double(self):
        x = amf3.DataInput(self.decoder)

        self._test('\x00' * 8, 0.0, x.readDouble)
        self._test('@\x93JEm\\\xfa\xad', 1234.5678, x.readDouble)

    def test_float(self):
        x = amf3.DataInput(self.decoder)

        self._test('\x00' * 4, 0.0, x.readFloat)
        self._test('?\x00\x00\x00', 0.5, x.readFloat)

    def test_int(self):
        x = amf3.DataInput(self.decoder)

        self._test('\x00\x00\x00\x00', 0, x.readInt)
        self._test('\xff\xff\xcf\xc7', -12345, x.readInt)
        self._test('\x00\x00\x00b', 98, x.readInt)

    def test_multi_byte(self):
        # TODO nick: test multiple charsets
        x = amf3.DataInput(self.decoder)

        self._test(u'this is a test', u'this is a test', x.readMultiByte,
            14, 'utf-8')
        self._test('\xe1\xbc\x94\xce\xb4\xcf\x89\xcf\x83\xce\xb1\xce\xbd',
            u'ἔδωσαν', x.readMultiByte, 13, 'utf-8')

    def test_object(self):
        x = amf3.DataInput(self.decoder)

        self._test('\t\x01\x07foo\x06\x07bar\x01', {'foo': 'bar'}, x.readObject)
        # check references
        self._test('\t\x00', {'foo': 'bar'}, x.readObject)

    def test_short(self):
        x = amf3.DataInput(self.decoder)

        self._test('\x007', 55, x.readShort)
        self._test('\xff\xc9', -55, x.readShort)

    def test_uint(self):
        x = amf3.DataInput(self.decoder)

        self._test('\x00\x00\x007', 55, x.readUnsignedInt)

    def test_utf(self):
        x = amf3.DataInput(self.decoder)

        self._test('\x0bhello world', u'hello world', x.readUTF)
        self._test('\r\xe1\xbc\x94\xce\xb4\xcf\x89\xcf\x83\xce\xb1\xce\xbd',
            u'ἔδωσαν', x.readUTF)

    def test_utf_bytes(self):
        x = amf3.DataInput(self.decoder)

        self._test('\xe1\xbc\x94\xce\xb4\xcf\x89\xcf\x83\xce\xb1\xce\xbd',
            u'ἔδωσαν', x.readUTFBytes, 13)

def suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(TypesTestCase))
    suite.addTest(unittest.makeSuite(ClassDefinitionTestCase))
    suite.addTest(unittest.makeSuite(ContextTestCase))
    suite.addTest(unittest.makeSuite(EncoderTestCase))
    suite.addTest(unittest.makeSuite(DecoderTestCase))
    suite.addTest(unittest.makeSuite(ObjectEncodingTestCase))
    suite.addTest(unittest.makeSuite(ObjectDecodingTestCase))
    suite.addTest(unittest.makeSuite(DataOutputTestCase))
    suite.addTest(unittest.makeSuite(DataInputTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
