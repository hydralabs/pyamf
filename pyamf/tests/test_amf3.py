# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Tests for AMF3 Implementation.

@since: 0.1.0
"""

import unittest, types

import pyamf
from pyamf import amf3, util
from pyamf.tests import util as _util
from pyamf.tests.util import Spam, ClassicSpam

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
        x.strings.append('spameggs')
        x.addLegacyXML(z)
        x.clear()

        self.assertEquals(x.objects, [])
        self.assertEquals(len(x.objects), 0)
        self.assertFalse(y in x.objects)

        self.assertEquals(x.strings, [])
        self.assertEquals(len(x.strings), 0)
        self.assertFalse('spameggs' in x.strings)

        self.assertEquals(x.legacy_xml, [])
        self.assertEquals(len(x.legacy_xml), 0)
        self.assertFalse('<a></a>' in x.legacy_xml)

    def test_get_by_reference(self):
        x = amf3.Context()
        y = [1, 2, 3]
        z = {'spam': 'eggs'}

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
        z = {'spam': 'eggs'}

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

class ClassDefinitionTestCase(_util.ClassCacheClearingTestCase):
    def test_create(self):
        x = amf3.ClassDefinition('')

        self.assertEquals(x.alias, None)
        self.assertEquals(x.encoding, 2)
        self.assertEquals(x.static_attrs, [])
        self.assertEquals(len(x.static_attrs), 0)

        x = amf3.ClassDefinition(None)

        self.assertEquals(x.alias, None)
        self.assertEquals(x.encoding, 2)
        self.assertEquals(x.static_attrs, [])
        self.assertEquals(len(x.static_attrs), 0)

        pyamf.register_class(Spam, 'spam.eggs')

        x = amf3.ClassDefinition('spam.eggs')
        self.assertTrue(isinstance(x.alias, pyamf.ClassAlias))
        self.assertEquals(x.alias, pyamf.get_class_alias('spam.eggs'))
        self.assertEquals(x.encoding, 2)
        self.assertEquals(x.static_attrs, [])
        self.assertEquals(len(x.static_attrs), 0)

    def test_name(self):
        x = amf3.ClassDefinition('')
        self.assertEquals(x.name, '')

        x = amf3.ClassDefinition(None)
        self.assertEquals(x.name, '')

        pyamf.register_class(Spam, 'spam.eggs')

        x = amf3.ClassDefinition('spam.eggs')
        self.assertEquals(x.name, 'spam.eggs')

    def test_get_class(self):
        # anonymous class
        x = amf3.ClassDefinition('')
        self.assertEquals(x.getClass(), pyamf.ASObject)

        x = amf3.ClassDefinition(None)
        self.assertEquals(x.getClass(), pyamf.ASObject)

        pyamf.register_class(Spam, 'spam.eggs')

        x = amf3.ClassDefinition('spam.eggs')
        self.assertEquals(x.getClass(), Spam)

    def test_get_alias(self):
        pyamf.register_class(Spam, 'spam.eggs')

        x = amf3.ClassDefinition('spam.eggs')
        alias = x.getClassAlias()

        self.assertEquals(alias.klass, Spam)
        self.assertEquals(alias.alias, 'spam.eggs')

        pyamf.unregister_class(Spam)

        x = amf3.ClassDefinition(None)
        self.assertRaises(pyamf.UnknownClassAlias, x.getClassAlias)

        x = amf3.ClassDefinition('')
        self.assertRaises(pyamf.UnknownClassAlias, x.getClassAlias)

class EncoderTestCase(_util.ClassCacheClearingTestCase):
    """
    Tests the output from the AMF3 L{Encoder<pyamf.amf3.Encoder>} class.
    """
    def setUp(self):
        _util.ClassCacheClearingTestCase.setUp(self)

        self.buf = util.BufferedByteStream()
        self.context = amf3.Context()
        self.encoder = amf3.Encoder(self.buf, context=self.context)

    def _run(self, data):
        self.context.clear()

        e = _util.EncoderTester(self.encoder, data)
        e.run(self)

    def test_undefined(self):
        def x():
            self._run([(ord, '\x00')])

        self.assertRaises(pyamf.EncodeError, x)

        self._run([(pyamf.Undefined, '\x00')])

    def test_null(self):
        self._run([(None, '\x01')])

    def test_boolean(self):
        self._run([(True, '\x03'), (False, '\x02')])

    def test_integer(self):
        self._run([(0, '\x04\x00')])
        self._run([(0x35, '\x04\x35')])
        self._run([(0x7f, '\x04\x7f')])
        self._run([(0x80, '\x04\x81\x00')])
        self._run([(0xd4, '\x04\x81\x54')])
        self._run([(0x3fff, '\x04\xff\x7f')])
        self._run([(0x4000, '\x04\x81\x80\x00')])
        self._run([(0x1a53f, '\x04\x86\xca\x3f')])
        self._run([(0x1fffff, '\x04\xff\xff\x7f')])
        self._run([(0x200000, '\x04\x80\xc0\x80\x00')])
        self._run([(-0x01, '\x04\xff\xff\xff\xff')])
        self._run([(-0x2a, '\x04\xff\xff\xff\xd6')])
        self._run([(0xfffffff, '\x04\xbf\xff\xff\xff')])
        self._run([(-0x10000000, '\x04\xc0\x80\x80\x00')])
        self._run([(0x10000000, '\x05\x41\xb0\x00\x00\x00\x00\x00\x00')])
        self._run([(-0x10000001, '\x05\xc1\xb0\x00\x00\x01\x00\x00\x00')])

    def test_number(self):
        self._run([
            (0.1, '\x05\x3f\xb9\x99\x99\x99\x99\x99\x9a'),
            (0.123456789, '\x05\x3f\xbf\x9a\xdd\x37\x39\x63\x5f')])

    def test_string(self):
        self._run([
            ('hello', '\x06\x0bhello'),
            (u'ᚠᛇᚻ', '\x06\x13\xe1\x9a\xa0\xe1\x9b\x87\xe1\x9a\xbb')])

    def test_bytestring(self):
        class UnicodeObject:
            def __unicode__(self):
                return u'MÃÂ¶tley CrÃÂ¼e'

        class StrObject:
            def __str__(self):
                return u'MÃÂ¶tley CrÃÂ¼e'

        class ReprObject:
            def __repr__(self):
                return u'MÃÂ¶tley CrÃÂ¼e'

        self.encoder.writeString(UnicodeObject())
        self.assertEquals(self.buf.getvalue(), '\x06+M\xc3\x83\xc3\x82\xc2'
            '\xb6tley Cr\xc3\x83\xc3\x82\xc2\xbce')
        self.buf.truncate()
        self.context.clear()

        self.encoder.writeString(StrObject())
        self.assertEquals(self.buf.getvalue(), '\x06+M\xc3\x83\xc3\x82\xc2'
            '\xb6tley Cr\xc3\x83\xc3\x82\xc2\xbce')
        self.buf.truncate()
        self.context.clear()

        self.encoder.writeString(ReprObject())
        self.assertEquals(self.buf.getvalue(), '\x06+M\xc3\x83\xc3\x82\xc2'
            '\xb6tley Cr\xc3\x83\xc3\x82\xc2\xbce')
        self.buf.truncate()
        self.context.clear()

        self.encoder.writeString('M\xc3\x83\xc3\x82\xc2\xb6tley Cr\xc3\x83'
            '\xc3\x82\xc2\xbce')
        self.assertEquals(self.buf.getvalue(), '\x06+M\xc3\x83\xc3\x82\xc2'
            '\xb6tley Cr\xc3\x83\xc3\x82\xc2\xbce')

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
            ({'spam': 'eggs'}, '\n\x0b\x01\tspam\x06\teggs\x01')])

        self._run([
            ({'a': u'a', 'b': u'b', 'c': u'c', 'd': u'd'},
                '\n\x0b\x01\x03a\x06\x00\x03c\x06\x02\x03b\x06\x04\x03d\x06\x06\x01')])

        x = amf3.Decoder('\n\x0b\x01\x03a\x06\x00\x03c\x06\x02\x03b\x06\x04\x03d\x06\x06\x01')
        self.assertEqual(x.readElement(), {'a': u'a', 'b': u'b', 'c': u'c', 'd': u'd'})

    def test_mixed_array(self):
        x = pyamf.MixedArray()
        x.update({0:u'hello', 'spam': u'eggs'})

        self._run([
            (x, '\t\x03\tspam\x06\teggs\x01\x06\x0bhello')])

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
        Test to see if there is an empty key in the C{dict}. There is a design
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
            ({'a': u'spam', 'b': 5},
                '\n\x0b\x01\x03a\x06\tspam\x03b\x04\x05\x01')])

        pyamf.register_class(Spam, 'org.pyamf.spam')

        obj = Spam()
        obj.baz = 'hello'

        self.encoder.writeElement(obj)

        self.assertEqual(self.buf.getvalue(), '\n\x0b\x1dorg.pyamf.spam\x07baz'
            '\x06\x0bhello\x01')

        pyamf.unregister_class(Spam)

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
        pyamf.register_class(Spam, 'abc.xyz')

        x = Spam({'spam': 'eggs'})

        class_def = self.encoder._getClassDefinition(x)

        self.assertEquals(class_def.name, 'abc.xyz')
        self.assertEquals(class_def.klass, Spam)
        self.assertEquals(class_def.static_attrs, [])

        pyamf.unregister_class(Spam)

        # test anonymous object
        x = {'spam': 'eggs'}

        class_def = self.encoder._getClassDefinition(x)

        self.assertEquals(class_def.name, '')
        self.assertEquals(class_def.klass, pyamf.ASObject)
        self.assertEquals(class_def.static_attrs, [])

    def test_get_class_definition_attrs(self):
        # test supplied attributes
        attrs = ['spam', 'eggs']
        pyamf.register_class(Spam, 'abc.xyz', attrs=attrs)

        x = Spam({'spam': 'eggs'})

        class_def = self.encoder._getClassDefinition(x)

        self.assertEquals(class_def.name, 'abc.xyz')
        self.assertEquals(class_def.klass, Spam)
        self.assertEquals(class_def.static_attrs, attrs)

    def test_anonymous(self):
        pyamf.register_class(Spam)

        x = Spam({'spam': 'eggs'})

        self._run([(x, '\n\x0b\x01\x09spam\x06\x09eggs\x01')])

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

    def test_old_style_classes(self):
        class Person:
            pass

        pyamf.register_class(Person, 'spam.eggs.Person')

        u = Person()
        u.family_name = 'Doe'
        u.given_name = 'Jane'

        self.encoder.writeElement(u)

        self.assertEquals(self.buf.getvalue(), '\n\x0b!spam.eggs.Person\x17'
            'family_name\x06\x07Doe\x15given_name\x06\tJane\x01')

        pyamf.unregister_class(Person)

    def test_getstate(self):
        self.executed = False

        class Foo(object):
            tc = self

            def __getstate__(self):
                self.tc.executed = True
                return {'spam': 'hello', 'eggs': True}

        pyamf.register_class(Foo, 'foo')

        foo = Foo()
        self.encoder.writeElement(foo)

        self.assertEquals(self.buf.getvalue(), '\x0a\x0b\x07\x66\x6f\x6f\x09'
            '\x65\x67\x67\x73\x03\x09\x73\x70\x61\x6d\x06\x0b\x68\x65\x6c\x6c'
            '\x6f\x01')
        self.assertTrue(self.executed)

    def test_elementtree_tag(self):
        class NotAnElement(object):
            items = lambda self: []

            def __iter__(self):
                return iter([])

        foo = NotAnElement()
        foo.tag = 'foo'
        foo.text = 'bar'
        foo.tail = None

        self.encoder.writeElement(foo)

        self.assertEquals(self.buf.getvalue(),
            '\n\x0b\x01\ttext\x06\x07bar\ttail\x01\x07tag\x06\x07foo\x01')

    def test_unknown_func(self):
        self.encoder._writeElementFunc = lambda x: None

        self.assertRaises(pyamf.EncodeError, self.encoder.writeElement, None)

    def test_funcs(self):
        def x():
            yield 2

        self.assertRaises(pyamf.EncodeError, self.encoder.writeElement, chr)
        self.assertRaises(pyamf.EncodeError, self.encoder.writeElement, self.assertRaises)
        self.assertRaises(pyamf.EncodeError, self.encoder.writeElement, lambda x: x)
        self.assertRaises(pyamf.EncodeError, self.encoder.writeElement, x())
        self.assertRaises(pyamf.EncodeError, self.encoder.writeElement, pyamf)
        self.assertRaises(pyamf.EncodeError, self.encoder.writeElement, ''.startswith)

class DecoderTestCase(_util.ClassCacheClearingTestCase):
    """
    Tests the output from the AMF3 L{Decoder<pyamf.amf3.Decoder>} class.
    """
    def setUp(self):
        _util.ClassCacheClearingTestCase.setUp(self)

        self.buf = util.BufferedByteStream()
        self.context = amf3.Context()
        self.decoder = amf3.Decoder(context=self.context)
        self.decoder.stream = self.buf

    def _run(self, data):
        self.context.clear()
        e = _util.DecoderTester(self.decoder, data)
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
        self._run([(0x35, '\x04\x35')])
        self._run([(0x7f, '\x04\x7f')])
        self._run([(0x80, '\x04\x81\x00')])
        self._run([(0xd4, '\x04\x81\x54')])
        self._run([(0x3fff, '\x04\xff\x7f')])
        self._run([(0x4000, '\x04\x81\x80\x00')])
        self._run([(0x1a53f, '\x04\x86\xca\x3f')])
        self._run([(0x1fffff, '\x04\xff\xff\x7f')])
        self._run([(0x200000, '\x04\x80\xc0\x80\x00')])
        self._run([(-0x01, '\x04\xff\xff\xff\xff')])
        self._run([(-0x2a, '\x04\xff\xff\xff\xd6')])
        self._run([(0xfffffff, '\x04\xbf\xff\xff\xff')])
        self._run([(-0x10000000, '\x04\xc0\x80\x80\x00')])

    def test_unsignedInteger(self):
        tests = [
            (0, '\x00'),
            (0x7f, '\x7f'),
            (0x80, '\x81\x00'),
            (0x3fff, '\xff\x7f'),
            (0x4000, '\x81\x80\x00'),
            (0x1fffff, '\xff\xff\x7f'),
            (0x200000, '\x80\xc0\x80\x00'),
            (0x3fffffff, '\xff\xff\xff\xff')
        ]

        for n, s in tests:
            self.buf.truncate(0)
            self.buf.write(s)
            self.buf.seek(0)
            self.assertEqual(self.decoder.readUnsignedInteger(), n)

    def test_infinites(self):
        self.buf.truncate()
        self.buf.write('\x05\xff\xf8\x00\x00\x00\x00\x00\x00')
        self.buf.seek(0)
        x = self.decoder.readElement()
        self.assertTrue(_util.isNaN(x))

        self.buf.truncate()
        self.buf.write('\x05\xff\xf0\x00\x00\x00\x00\x00\x00')
        self.buf.seek(0)
        x = self.decoder.readElement()
        self.assertTrue(_util.isNegInf(x))

        self.buf.truncate()
        self.buf.write('\x05\x7f\xf0\x00\x00\x00\x00\x00\x00')
        self.buf.seek(0)
        x = self.decoder.readElement()
        self.assertTrue(_util.isPosInf(x))

    def test_boolean(self):
        self._run([(True, '\x03'), (False, '\x02')])

    def test_null(self):
        self._run([(None, '\x01')])

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
        pyamf.register_class(Spam, 'org.pyamf.spam')

        self.buf.truncate(0)
        self.buf.write('\x0a\x13\x1dorg.pyamf.spam\x07baz\x06\x0b\x68\x65\x6c\x6c\x6f')
        self.buf.seek(0)

        obj = self.decoder.readElement()

        self.assertEquals(obj.__class__, Spam)

        self.failUnless(hasattr(obj, 'baz'))
        self.assertEquals(obj.baz, 'hello')

    def test_byte_array(self):
        self._run([(amf3.ByteArray('hello'), '\x0c\x0bhello')])

    def test_date(self):
        import datetime

        self._run([
            (datetime.datetime(2005, 3, 18, 1, 58, 31),
                '\x08\x01Bp+6!\x15\x80\x00')])

    def test_get_class_definition(self):
        pyamf.register_class(Spam, 'abc.xyz')

        self.buf.write('\x0fabc.xyz')
        self.buf.seek(0, 0)

        is_ref, class_def, num_attrs = self.decoder._getClassDefinition(0x01)

        self.assertFalse(is_ref)
        self.assertTrue(isinstance(class_def, amf3.ClassDefinition))
        self.assertTrue(class_def.getClass(), Spam)
        self.assertTrue(class_def.klass, Spam)
        self.assertTrue(class_def.name, 'abc.xyz')
        self.assertEquals(class_def.encoding, amf3.ObjectEncoding.STATIC)

        self.assertTrue(class_def in self.context.classes)
        self.assertTrue(id(class_def) in self.context.rev_classes)

        self.context.classes.remove(class_def)
        self.buf.write('\x0fabc.xyz')
        self.buf.seek(0, 0)

        is_ref, class_def, num_attrs = self.decoder._getClassDefinition(0x03)

        self.assertFalse(is_ref)
        self.assertTrue(isinstance(class_def, amf3.ClassDefinition))
        self.assertTrue(class_def.getClass(), Spam)
        self.assertTrue(class_def.name, 'abc.xyz')
        self.assertEquals(class_def.encoding, amf3.ObjectEncoding.EXTERNAL)

        self.assertTrue(class_def in self.context.classes)

        self.context.classes.remove(class_def)
        self.buf.write('\x0fabc.xyz')
        self.buf.seek(0, 0)

        is_ref, class_def, num_attrs = self.decoder._getClassDefinition(0x05)

        self.assertFalse(is_ref)
        self.assertTrue(isinstance(class_def, amf3.ClassDefinition))
        self.assertTrue(class_def.getClass(), Spam)
        self.assertTrue(class_def.name, 'abc.xyz')
        self.assertEquals(class_def.encoding, amf3.ObjectEncoding.DYNAMIC)

        self.assertTrue(class_def in self.context.classes)
        self.context.classes.remove(class_def)

    def test_setstate_newstyle(self):
        self.executed = False

        class Foo(object):
            tc = self

            def __init__(self, *args, **kwargs):
                self.tc.fail("__init__ called")

            def __setstate__(self, state):
                self.tc.executed = True
                self.__dict__.update(state)

        pyamf.register_class(Foo, 'foo')

        self.buf.write('\x0a\x0b\x07\x66\x6f\x6f\x09\x65\x67\x67\x73' + \
            '\x03\x09\x73\x70\x61\x6d\x06\x0b\x68\x65\x6c\x6c\x6f\x01')
        self.buf.seek(0)

        foo = self.decoder.readElement()

        self.assertEquals(foo.spam, 'hello')
        self.assertEquals(foo.eggs, True)
        self.assertTrue(self.executed)

    def test_setstate_classic(self):
        self.executed = False

        class Foo:
            tc = self

            def __init__(self, *args, **kwargs):
                self.tc.fail("__init__ called")

            def __setstate__(self, state):
                self.tc.executed = True
                self.__dict__.update(state)

        pyamf.register_class(Foo, 'foo')

        self.buf.write('\x0a\x0b\x07\x66\x6f\x6f\x09\x65\x67\x67\x73' + \
            '\x03\x09\x73\x70\x61\x6d\x06\x0b\x68\x65\x6c\x6c\x6f\x01')
        self.buf.seek(0)

        foo = self.decoder.readElement()

        self.assertEquals(foo.spam, 'hello')
        self.assertEquals(foo.eggs, True)
        self.assertTrue(self.executed)

    def test_classic_class(self):
        pyamf.register_class(ClassicSpam, 'spam.eggs')

        self.buf.write('\n\x0b\x13spam.eggs\x07foo\x06\x07bar\x01')
        self.buf.seek(0)

        foo = self.decoder.readElement()

        self.assertEquals(foo.foo, 'bar')

class ObjectEncodingTestCase(_util.ClassCacheClearingTestCase):
    def setUp(self):
        _util.ClassCacheClearingTestCase.setUp(self)

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
        pyamf.register_class(Spam, 'abc.xyz')

        x = Spam({'spam': 'eggs'})
        y = Spam({'spam': 'baz'})

        self.encoder.writeElement(x)

        pyamf.unregister_class(Spam)

        #self.assertEquals(self.stream.getvalue(), '\x0a\x03')
        #from pyamf.util import hexdump
        #print hexdump(self.stream.getvalue())

        #pos = self.stream.tell()
        #self.encoder.writeElement(y)
        #self.assertEquals(self.stream.getvalue()[pos:], '\x0a\x00')

    def test_static(self):
        pyamf.register_class(Spam, 'abc.xyz', metadata='static', attrs=[])

        x = Spam({'spam': 'eggs'})
        self.encoder.writeElement(x)
        self.assertEquals(self.stream.getvalue(), '\n\x03\x0fabc.xyz')
        pyamf.unregister_class(Spam)
        self.stream.truncate()
        self.encoder.context.clear()

        pyamf.register_class(Spam, 'abc.xyz', metadata='static', attrs=['spam'])

        x = Spam({'spam': 'eggs'})
        self.encoder.writeElement(x)
        self.assertEquals(self.stream.getvalue(), '\n\x13\x0fabc.xyz\tspam\x06\teggs')
        pyamf.unregister_class(Spam)

    def test_dynamic(self):
        pyamf.register_class(Spam, 'abc.xyz', metadata='dynamic')

        x = Spam({'spam': 'eggs'})
        self.encoder.writeElement(x)

        self.assertEquals(self.stream.getvalue(), '\n\x0b\x0fabc.xyz\tspam\x06\teggs\x01')

        pyamf.unregister_class(Spam)

    def test_combined(self):
        def wf(obj):
            return ['eggs']

        pyamf.register_class(Spam, 'abc.xyz', attrs=['spam'], attr_func=wf)

        x = Spam({'spam': 'foo', 'eggs': 'bar'})
        self.encoder.writeElement(x)

        buf = self.stream.getvalue()

        self.assertEquals(buf, '\n\x1b\x0fabc.xyz\tspam\x06\x07foo\teggs\x06\x07bar\x01')

        pyamf.unregister_class(Spam)

    def test_external(self):
        pyamf.register_class(Spam, 'abc.xyz', metadata=['external'])

        x = Spam({'spam': 'eggs'})
        self.encoder.writeElement(x)

        buf = self.stream.getvalue()

        # an inline object with and inline class-def, encoding = 0x01, 1 attr

        self.assertEquals(buf[:2], '\x0a\x07')
        # class alias name
        self.assertEquals(buf[2:10], '\x0fabc.xyz')

        self.assertEquals(len(buf), 10)

        pyamf.unregister_class(Spam)

class ObjectDecodingTestCase(_util.ClassCacheClearingTestCase):
    def setUp(self):
        _util.ClassCacheClearingTestCase.setUp(self)

        self.stream = util.BufferedByteStream()
        self.context = amf3.Context()
        self.decoder = amf3.Decoder(self.stream, self.context)

    def test_object_references(self):
        self.stream.write('\x0a\x23\x01\x03a\x03b\x06\x09spam\x04\x05')
        self.stream.seek(0, 0)

        obj1 = self.decoder.readElement()

        self.stream.truncate()
        self.stream.write('\n\x00')
        self.stream.seek(0, 0)

        obj2 = self.decoder.readElement()

        self.assertEquals(id(obj1), id(obj2))

    def test_static(self):
        pyamf.register_class(Spam, 'abc.xyz')

        self.assertEquals(self.context.objects, [])
        self.assertEquals(self.context.strings, [])
        self.assertEquals(self.context.classes, [])

        self.stream.write('\x0a\x13\x0fabc.xyz\x09spam\x06\x09eggs')
        self.stream.seek(0, 0)

        obj = self.decoder.readElement()

        class_def = self.context.classes[0]

        self.assertEquals(class_def.static_attrs, ['spam'])

        self.assertTrue(isinstance(obj, Spam))
        self.assertEquals(obj.__dict__, {'spam': 'eggs'})

    def test_dynamic(self):
        pyamf.register_class(Spam, 'abc.xyz', metadata='dynamic')

        self.assertEquals(self.context.objects, [])
        self.assertEquals(self.context.strings, [])
        self.assertEquals(self.context.classes, [])

        self.stream.write('\x0a\x0b\x0fabc.xyz\x09spam\x06\x09eggs\x01')
        self.stream.seek(0, 0)

        obj = self.decoder.readElement()

        class_def = self.context.classes[0]

        self.assertEquals(class_def.static_attrs, [])

        self.assertTrue(isinstance(obj, Spam))
        self.assertEquals(obj.__dict__, {'spam': 'eggs'})

    def test_combined(self):
        """
        This tests an object encoding with static properties and dynamic
        properties
        """
        pyamf.register_class(Spam, 'abc.xyz', metadata='dynamic')

        self.assertEquals(self.context.objects, [])
        self.assertEquals(self.context.strings, [])
        self.assertEquals(self.context.classes, [])

        self.stream.write('\x0a\x1b\x0fabc.xyz\x09spam\x06\x09eggs\x07baz\x06\x07'
            'nat\x01')
        self.stream.seek(0, 0)

        obj = self.decoder.readElement()

        class_def = self.context.classes[0]

        self.assertEquals(class_def.static_attrs, ['spam'])

        self.assertTrue(isinstance(obj, Spam))
        self.assertEquals(obj.__dict__, {'spam': 'eggs', 'baz': 'nat'})

    def test_external(self):
        pyamf.register_class(Spam, 'abc.xyz', metadata=['external'])

        self.stream.write('\x0a\x07\x0fabc.xyz')
        self.stream.seek(0)
        x = self.decoder.readElement()

        self.assertTrue(isinstance(x, Spam))
        self.assertEquals(x.__dict__, {})

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
        obj = pyamf.MixedArray(spam='eggs')

        x.writeObject(obj)
        self.assertEquals(self.stream.getvalue(),
            '\t\x01\x09spam\x06\x09eggs\x01')
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

        self.assertEquals(self.stream.getvalue(), '\x00\r\xe1\xbc\x94\xce'
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

        self._test('\t\x01\x09spam\x06\x09eggs\x01', {'spam': 'eggs'}, x.readObject)
        # check references
        self._test('\t\x00', {'spam': 'eggs'}, x.readObject)

    def test_short(self):
        x = amf3.DataInput(self.decoder)

        self._test('\x007', 55, x.readShort)
        self._test('\xff\xc9', -55, x.readShort)

    def test_uint(self):
        x = amf3.DataInput(self.decoder)

        self._test('\x00\x00\x007', 55, x.readUnsignedInt)

    def test_utf(self):
        x = amf3.DataInput(self.decoder)

        self._test('\x00\x0bhello world', u'hello world', x.readUTF)
        self._test('\x00\r\xe1\xbc\x94\xce\xb4\xcf\x89\xcf\x83\xce\xb1\xce\xbd',
            u'ἔδωσαν', x.readUTF)

    def test_utf_bytes(self):
        x = amf3.DataInput(self.decoder)

        self._test('\xe1\xbc\x94\xce\xb4\xcf\x89\xcf\x83\xce\xb1\xce\xbd',
            u'ἔδωσαν', x.readUTFBytes, 13)

class ClassInheritanceTestCase(_util.ClassCacheClearingTestCase):
    def test_simple(self):
        class A(object):
            pass

        pyamf.register_class(A, 'A', attrs=['a'])

        class B(A):
            pass

        pyamf.register_class(B, 'B', attrs=['b'])

        x = B()
        x.a = 'spam'
        x.b = 'eggs'

        stream = util.BufferedByteStream()
        encoder = pyamf._get_encoder_class(pyamf.AMF3)(stream)

        encoder.writeElement(x)

        self.assertEquals(stream.getvalue(), '\n\x1b\x03B\x03b\x06\teggs\x03a'
            '\x06\tspam\x02\x06\x04\x01')

    def test_deep(self):
        class A(object):
            pass

        pyamf.register_class(A, 'A', attrs=['a'])

        class B(A):
            pass

        pyamf.register_class(B, 'B', attrs=['b'])

        class C(B):
            pass

        pyamf.register_class(C, 'C', attrs=['c'])

        x = C()
        x.a = 'spam'
        x.b = 'eggs'
        x.c = 'foo'

        stream = util.BufferedByteStream()
        encoder = pyamf._get_encoder_class(pyamf.AMF3)(stream)

        encoder.writeElement(x)

        self.assertEquals(stream.getvalue(), '\n\x1b\x03C\x03c\x06\x07foo\x03'
            'a\x06\tspam\x02\x06\x04\x03b\x06\teggs\x01')

class HelperTestCase(unittest.TestCase):
    def test_encode(self):
        buf = amf3.encode(1)

        self.assertTrue(isinstance(buf, util.BufferedByteStream))

        self.assertEquals(amf3.encode(1).getvalue(), '\x04\x01')
        self.assertEquals(amf3.encode('foo', 'bar').getvalue(), '\x06\x07foo\x06\x07bar')

    def test_encode_with_context(self):
        context = amf3.Context()

        obj = object()
        context.addObject(obj)
        self.assertEquals(amf3.encode(obj, context=context).getvalue(), '\n\x00')

    def test_decode(self):
        gen = amf3.decode('\x04\x01')
        self.assertTrue(isinstance(gen, types.GeneratorType))

        self.assertEquals(gen.next(), 1)
        self.assertRaises(StopIteration, gen.next)

        self.assertEquals([x for x in amf3.decode('\x06\x07foo\x06\x07bar')], ['foo', 'bar'])

    def test_decode_with_context(self):
        context = amf3.Context()

        obj = object()
        context.addObject(obj)
        self.assertEquals([x for x in amf3.decode('\n\x00', context=context)], [obj])

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
    suite.addTest(unittest.makeSuite(ClassInheritanceTestCase))
    suite.addTest(unittest.makeSuite(HelperTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
