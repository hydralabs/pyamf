# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.

"""
Tests for AMF3 Implementation.

@since: 0.1.0
"""

import unittest
import types
import datetime

import pyamf
from pyamf import amf3, util
from pyamf.tests import util as _util
from pyamf.tests.util import Spam, check_buffer, assert_buffer


class MockAlias(object):
    def __init__(self):
        self.get_attributes = []
        self.get_static_attrs = []
        self.apply_attrs = []

        self.static_attrs = {}
        self.attrs = ({}, {})
        self.create_instance = []
        self.expected_instance = object()

    def getStaticAttrs(self, *args, **kwargs):
        self.get_static_attrs.append([args, kwargs])

        return self.static_attrs

    def getAttributes(self, *args, **kwargs):
        self.get_attributes.append([args, kwargs])

        return self.attrs

    def createInstance(self, *args, **kwargs):
        self.create_instance.append([args, kwargs])

        return self.expected_instance

    def applyAttributes(self, *args, **kwargs):
        self.apply_attrs.append([args, kwargs])


class TypesTestCase(unittest.TestCase):
    """
    Tests the type mappings.
    """
    def test_types(self):
        self.assertEquals(amf3.TYPE_UNDEFINED, '\x00')
        self.assertEquals(amf3.TYPE_NULL, '\x01')
        self.assertEquals(amf3.TYPE_BOOL_FALSE, '\x02')
        self.assertEquals(amf3.TYPE_BOOL_TRUE, '\x03')
        self.assertEquals(amf3.TYPE_INTEGER, '\x04')
        self.assertEquals(amf3.TYPE_NUMBER, '\x05')
        self.assertEquals(amf3.TYPE_STRING, '\x06')
        self.assertEquals(amf3.TYPE_XML, '\x07')
        self.assertEquals(amf3.TYPE_DATE, '\x08')
        self.assertEquals(amf3.TYPE_ARRAY, '\x09')
        self.assertEquals(amf3.TYPE_OBJECT, '\x0a')
        self.assertEquals(amf3.TYPE_XMLSTRING, '\x0b')
        self.assertEquals(amf3.TYPE_BYTEARRAY, '\x0c')


class ContextTestCase(_util.ClassCacheClearingTestCase):
    def test_create(self):
        c = amf3.Context()

        self.assertEquals(c.exceptions, True)
        self.assertEquals(c.strings, [])
        self.assertEquals(c.objects, [])
        self.assertEquals(c.classes, {})
        self.assertEquals(c.legacy_xml, [])
        self.assertEquals(c.object_aliases, [])
        self.assertEquals(len(c.strings), 0)
        self.assertEquals(len(c.classes), 0)
        self.assertEquals(len(c.legacy_xml), 0)
        self.assertEquals(len(c.object_aliases), 0)

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

        self.assertRaises(pyamf.ReferenceError, x.addString, '')

        x.exceptions = False
        self.assertEquals(x.addString(''), None)

        self.assertRaises(TypeError, x.addString, 132)

    def test_add_class(self):
        x = amf3.Context()

        alias = pyamf.register_class(Spam, 'spam.eggs')
        y = amf3.ClassDefinition(alias)

        self.assertEquals(x.addClass(y, Spam), 0)
        self.assertEquals(x.classes, {Spam: y})
        self.assertEquals(x.class_ref, {0: y})
        self.assertEquals(len(x.class_ref), 1)

    def test_add_legacy_xml(self):
        x = amf3.Context()
        y = 'abc'

        self.assertEquals(x.addLegacyXML(y), 0)
        self.assertTrue(y in x.legacy_xml)
        self.assertEquals(len(x.legacy_xml), 1)

    def test_set_object_alias(self):
        x = amf3.Context()
        obj = {'label': 'original'}
        alias = {'label': 'aliased'}

        x.setObjectAlias(obj, alias)
        self.assertEquals(len(x.object_aliases), 1)

    def test_get_object_alias(self):
        x = amf3.Context()
        obj = {'label': 'original'}
        alias = {'label': 'aliased'}

        x.setObjectAlias(obj, alias)
        self.assertEquals(alias, x.getObjectAlias(obj))
        self.assertEquals('aliased', x.getObjectAlias(obj)['label'])
        self.assertRaises(pyamf.ReferenceError, x.getObjectAlias, object())

        x.exceptions = False
        self.assertEquals(x.getObjectAlias(object()), None)

    def test_clear(self):
        x = amf3.Context()
        y = [1, 2, 3]
        z = '<a></a>'

        x.addObject(y)
        x.addString('spameggs')
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

        alias_spam = pyamf.register_class(Spam, 'spam.eggs')

        class Foo:
            pass

        class Bar:
            pass

        alias_foo = pyamf.register_class(Foo, 'foo.bar')

        a = amf3.ClassDefinition(alias_spam)
        b = amf3.ClassDefinition(alias_foo)

        x.addObject(y)
        x.addObject(z)
        x.addString('abc')
        x.addString('def')
        x.addLegacyXML('<a></a>')
        x.addLegacyXML('<b></b>')
        x.addClass(a, Foo)
        x.addClass(b, Bar)

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

        self.assertEquals(x.getClass(Foo), a)
        self.assertEquals(x.getClass(Bar), b)
        self.assertRaises(pyamf.ReferenceError, x.getClass, 2)

        self.assertEquals(x.getClassByReference(0), a)
        self.assertEquals(x.getClassByReference(1), b)
        self.assertRaises(pyamf.ReferenceError, x.getClassByReference, 2)

        x.exceptions = False

        self.assertEquals(x.getObject(2), None)
        self.assertEquals(x.getString(2), None)
        self.assertEquals(x.getClass(2), None)
        self.assertEquals(x.getLegacyXML(2), None)
        self.assertEquals(x.getClassByReference(2), None)
        self.assertEquals(x.getLegacyXMLReference(object()), None)

    def test_empty_string(self):
        x = amf3.Context()

        self.assertRaises(pyamf.ReferenceError, x.addString, '')

    def test_get_reference(self):
        x = amf3.Context()
        y = [1, 2, 3]
        z = {'spam': 'eggs'}

        spam_alias = pyamf.register_class(Spam, 'spam.eggs')

        class Foo:
            pass

        foo_alias = pyamf.register_class(Foo, 'foo.bar')

        a = amf3.ClassDefinition(spam_alias)
        b = amf3.ClassDefinition(foo_alias)

        ref1 = x.addObject(y)
        ref2 = x.addObject(z)
        x.addString('abc')
        x.addString('def')
        x.addLegacyXML('<a></a>')
        x.addLegacyXML('<b></b>')
        x.addClass(a, Spam)
        x.addClass(b, Foo)

        self.assertEquals(x.getObjectReference(y), ref1)
        self.assertEquals(x.getObjectReference(z), ref2)
        self.assertRaises(pyamf.ReferenceError, x.getObjectReference, {})

        self.assertEquals(x.getStringReference('abc'), 0)
        self.assertEquals(x.getStringReference('def'), 1)
        self.assertRaises(pyamf.ReferenceError, x.getStringReference, 'asdfas')

        self.assertEquals(x.getLegacyXMLReference('<a></a>'), 0)
        self.assertEquals(x.getLegacyXMLReference('<b></b>'), 1)
        self.assertRaises(pyamf.ReferenceError, x.getLegacyXMLReference, '<c/>')

        self.assertEquals(x.getClass(Spam), a)
        self.assertEquals(x.getClass(Foo), b)
        self.assertRaises(pyamf.ReferenceError, x.getClass, object())

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

        self.assertEquals(new.classes, {})

        self.assertEquals(new.legacy_xml, [])
        self.assertEquals(len(new.legacy_xml), 0)


class ClassDefinitionTestCase(_util.ClassCacheClearingTestCase):

    def setUp(self):
        _util.ClassCacheClearingTestCase.setUp(self)

        self.alias = pyamf.ClassAlias(Spam, defer=True)

    def test_dynamic(self):
        self.assertFalse(self.alias.is_compiled())

        x = amf3.ClassDefinition(self.alias)

        self.assertTrue(x.alias is self.alias)
        self.assertEquals(x.encoding, 2)
        self.assertEquals(x.reference, None)
        self.assertEquals(x.attr_len, 0)

        self.assertTrue(self.alias.is_compiled())

    def test_static(self):
        self.alias.static_attrs = ['foo', 'bar']
        self.alias.dynamic = False

        x = amf3.ClassDefinition(self.alias)

        self.assertTrue(x.alias is self.alias)
        self.assertEquals(x.encoding, 0)
        self.assertEquals(x.reference, None)
        self.assertEquals(x.attr_len, 2)

    def test_mixed(self):
        self.alias.static_attrs = ['foo', 'bar']

        x = amf3.ClassDefinition(self.alias)

        self.assertTrue(x.alias is self.alias)
        self.assertEquals(x.encoding, 2)
        self.assertEquals(x.reference, None)
        self.assertEquals(x.attr_len, 2)

    def test_external(self):
        self.alias.external = True

        x = amf3.ClassDefinition(self.alias)

        self.assertTrue(x.alias is self.alias)
        self.assertEquals(x.encoding, 1)
        self.assertEquals(x.reference, None)
        self.assertEquals(x.attr_len, 0)


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

    def test_list_references(self):
        y = [0, 1, 2, 3]

        self._run([
            (y, '\x09\x09\x01\x04\x00\x04\x01\x04\x02\x04\x03'),
            (y, '\x09\x00'),
            (y, '\x09\x00')])

    def test_list_proxy_references(self):
        self.encoder.use_proxies = True
        y = [0, 1, 2, 3]
        self._run([
            (y, '\n\x07Cflex.messaging.io.ArrayCollection\t\t\x01\x04\x00'
                '\x04\x01\x04\x02\x04\x03'),
            (y, '\n\x00'),
            (y, '\n\x00')])

    def test_dict(self):
        self._run([
            ({'spam': 'eggs'}, '\n\x0b\x01\tspam\x06\teggs\x01')])

        self._run([
            ({'a': u'e', 'b': u'f', 'c': u'g', 'd': u'h'},  '\n\x0b\x01', (
                '\x03c\x06\x03g',
                '\x03b\x06\x03f',
                '\x03a\x06\x03e',
                '\x03d\x06\x03h',
            ), '\x01')
        ])

        x = amf3.Decoder('\n\x0b\x01\x03a\x06\x00\x03c\x06\x02\x03b\x06\x04'
            '\x03d\x06\x06\x01')
        self.assertEqual(x.readElement(),
            {'a': u'a', 'b': u'b', 'c': u'c', 'd': u'd'})

    def test_mixed_array(self):
        x = pyamf.MixedArray()
        x.update({0:u'hello', 'spam': u'eggs'})

        self._run([
            (x, '\t\x03\tspam\x06\teggs\x01\x06\x0bhello')])

        x = pyamf.MixedArray()
        x.update({0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 'a': 'a'})
        self._run([(x, '\x09\x0d\x03\x61\x06\x00\x01\x04\x00\x04\x01\x04\x02'
            '\x04\x03\x04\x04\x04\x05')])

        x = amf3.Decoder('\x09\x09\x03\x62\x06\x00\x03\x64\x06\x02\x03\x61'
            '\x06\x04\x03\x63\x06\x06\x01\x04\x00\x04\x01\x04\x02\x04\x03')

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

    def test_date(self):
        import datetime

        x = datetime.datetime(2005, 3, 18, 1, 58, 31)
        self.encoder.writeElement(x)

        self.assertEquals(self.buf.getvalue(), '\x08\x01Bp+6!\x15\x80\x00')
        self.buf.truncate()
        self.encoder.writeElement(x)

        self.assertEquals(self.buf.getvalue(), '\x08\x00')

        try:
            self._run([(datetime.time(22, 3), '')])
        except pyamf.EncodeError, e:
            self.assertEquals(str(e), 'A datetime.time instance was found but '
                'AMF3 has no way to encode time objects. Please use '
                'datetime.datetime instead (got:datetime.time(22, 3))')
        else:
            self.fail('pyamf.EncodeError not raised when encoding datetime.time')


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

    def test_anonymous(self):
        pyamf.register_class(Spam)

        x = Spam({'spam': 'eggs'})

        self._run([(x, '\n\x0b\x01\x09spam\x06\x09eggs\x01')])

    def test_custom_type(self):
        def write_as_list(list_interface_obj, encoder):
            list_interface_obj.ran = True
            self.assertEquals(id(self.encoder), id(encoder))

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

        assert_buffer(self, self.buf.getvalue(), (
            '\n\x0b!spam.eggs.Person', (
                '\x17family_name\x06\x07Doe',
                '\x15given_name\x06\tJane'
            ),
            '\x01'
        ))

    def test_slots(self):
        class Person(object):
            __slots__ = ('family_name', 'given_name')

        u = Person()
        u.family_name = 'Doe'
        u.given_name = 'Jane'

        self.encoder.writeElement(u)

        assert_buffer(self, self.buf.getvalue(), ('\n\x0b\x01', (
            '\x17family_name\x06\x07Doe',
            '\x15given_name\x06\tJane'
            ), '\x01'))

    def test_slots_registered(self):
        class Person(object):
            __slots__ = ('family_name', 'given_name')

        pyamf.register_class(Person, 'spam.eggs.Person')

        u = Person()
        u.family_name = 'Doe'
        u.given_name = 'Jane'

        self.encoder.writeElement(u)

        assert_buffer(self, self.buf.getvalue(), ('\n\x0b!spam.eggs.Person', (
            '\x17family_name\x06\x07Doe',
            '\x15given_name\x06\tJane'
        ), '\x01'))

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

        self.assertTrue(check_buffer(self.buf.getvalue(), ('\n\x0b\x01', (
            '\ttext\x06\x07bar',
            '\ttail\x01',
            '\x07tag\x06\x07foo'
        ), '\x01')))

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

    def test_29b_ints(self):
        """
        Tests for ints that don't fit into 29bits. Reference: #519
        """
        ints = [
            (amf3.MIN_29B_INT - 1, '\x05\xc1\xb0\x00\x00\x01\x00\x00\x00'),
            (amf3.MAX_29B_INT + 1, '\x05A\xb0\x00\x00\x00\x00\x00\x00')
        ]

        for i, val in ints:
            self.buf.truncate()

            self.encoder.writeElement(i)
            self.assertEquals(self.buf.getvalue(), val)

    def test_number(self):
        vals = [
            (0,        '\x04\x00'),
            (0.2,      '\x05\x3f\xc9\x99\x99\x99\x99\x99\x9a'),
            (1,        '\x04\x01'),
            (127,      '\x04\x7f'),
            (128,      '\x04\x81\x00'),
            (0x3fff,   '\x04\xff\x7f'),
            (0x4000,   '\x04\x81\x80\x00'),
            (0x1FFFFF, '\x04\xff\xff\x7f'),
            (0x200000, '\x04\x80\xc0\x80\x00'),
            (0x3FFFFF, '\x04\x80\xff\xff\xff'),
            (0x400000, '\x04\x81\x80\x80\x00'),
            (-1,       '\x04\xff\xff\xff\xff'),
            (42,       '\x04\x2a'),
            (-123,     '\x04\xff\xff\xff\x85'),
            (amf3.MIN_29B_INT, '\x04\xc0\x80\x80\x00'),
            (amf3.MAX_29B_INT, '\x04\xbf\xff\xff\xff'),
            (1.23456789, '\x05\x3f\xf3\xc0\xca\x42\x83\xde\x1b')
	]

        for i, val in vals:
            self.buf.truncate()

            self.encoder.writeElement(i)
            self.assertEquals(self.buf.getvalue(), val)

    def test_class(self):
        class New(object):
            pass

        class Classic:
            pass

        self.assertRaises(pyamf.EncodeError, self.encoder.writeElement, Classic)
        self.assertRaises(pyamf.EncodeError, self.encoder.writeElement, New)

    def test_proxy(self):
        """
        Test to ensure that only C{dict} objects will be proxied correctly
        """
        x = pyamf.ASObject()

        self.encoder.use_proxies = True
        self.encoder.writeElement(x)

        self.assertEquals(self.buf.getvalue(), '\n\x0b\x01\x01')

        self.buf.truncate()
        x = dict()

        self.encoder.writeElement(x)

        self.assertEquals(self.buf.getvalue(), '\n\x07;flex.messaging.io.'
            'ObjectProxy\n\x0b\x01\x01')

    def test_timezone(self):
        d = datetime.datetime(2009, 9, 24, 14, 23, 23)
        self.encoder.timezone_offset = datetime.timedelta(hours=-5)

        self.encoder.writeElement(d)

        self.assertEquals(self.buf.getvalue(), '\x08\x01Br>\xd8\x1f\xff\x80\x00')


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

    def test_undefined(self):
        self._run([(pyamf.Undefined, '\x00')])

    def test_number(self):
        self._run([
            (0,    '\x04\x00'),
            (0.2,  '\x05\x3f\xc9\x99\x99\x99\x99\x99\x9a'),
            (1,    '\x04\x01'),
            (-1,    '\x04\xff\xff\xff\xff'),
            (42,   '\x04\x2a'),
            (-123, '\x04\xff\xff\xff\x85'),
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
        self.assertEquals(self.context.getLegacyXMLReference(x), None)

        self.buf.truncate()
        self.buf.write('\x0b\x00')
        self.buf.seek(0, 0)
        y = self.decoder.readElement()

        self.assertEquals(x, y)

    def test_xmlstring_references(self):
        self.buf.write('\x0b\x33<a><b>hello world</b></a>\x0b\x00')
        self.buf.seek(0, 0)
        x = self.decoder.readElement()
        y = self.decoder.readElement()

        self.assertEquals(id(x), id(y))

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

        bytes = '\x0a\x0b\x01\x07\x62\x61\x7a\x06\x0b\x68\x65\x6c\x6c\x6f\x01'

        self.buf.write(bytes)
        self.buf.seek(0)
        d = self.decoder.readElement()

        self.assertEquals(type(d.keys()[0]), str)

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

        class_def, alias = self.decoder._getClassDefinition(0x01)

        self.assertTrue(isinstance(class_def, amf3.ClassDefinition))
        self.assertTrue(alias.klass, Spam)
        self.assertTrue(alias.alias, 'abc.xyz')
        self.assertEquals(class_def.encoding, amf3.ObjectEncoding.STATIC)

        self.assertTrue(class_def in self.context.class_ref.values())
        self.assertTrue(alias.klass in self.context.classes)

        self.context.class_ref = {}
        self.buf.write('\x0fabc.xyz')
        self.buf.seek(0, 0)

        class_def, alias = self.decoder._getClassDefinition(0x03)

        self.assertTrue(isinstance(class_def, amf3.ClassDefinition))
        self.assertTrue(alias.klass, Spam)
        self.assertTrue(alias.alias, 'abc.xyz')
        self.assertEquals(class_def.encoding, amf3.ObjectEncoding.EXTERNAL)

        self.assertTrue(class_def in self.context.class_ref.values())

        self.context.class_ref = {}
        self.buf.write('\x0fabc.xyz')
        self.buf.seek(0, 0)

        class_def, alias = self.decoder._getClassDefinition(0x05)

        self.assertTrue(isinstance(class_def, amf3.ClassDefinition))
        self.assertTrue(alias.klass, Spam)
        self.assertTrue(alias.alias, 'abc.xyz')
        self.assertEquals(class_def.encoding, amf3.ObjectEncoding.DYNAMIC)

        self.assertTrue(class_def in self.context.class_ref.values())

    def test_not_strict(self):
        self.assertFalse(self.decoder.strict)

        # write a typed object to the stream
        self.buf.write('\n\x0b\x13spam.eggs\x07foo\x06\x07bar\x01')
        self.buf.seek(0)

        self.assertFalse('spam.eggs' in pyamf.CLASS_CACHE)

        obj = self.decoder.readElement()

        self.assertTrue(isinstance(obj, pyamf.TypedObject))
        self.assertEquals(obj.alias, 'spam.eggs')
        self.assertEquals(obj, {'foo': 'bar'})

    def test_strict(self):
        self.decoder.strict = True

        self.assertTrue(self.decoder.strict)

        # write a typed object to the stream
        self.buf.write('\n\x0b\x13spam.eggs\x07foo\x06\x07bar\x01')
        self.buf.seek(0)

        self.assertFalse('spam.eggs' in pyamf.CLASS_CACHE)

        self.assertRaises(pyamf.UnknownClassAlias, self.decoder.readElement)

    def test_slots(self):
        class Person(object):
            __slots__ = ('family_name', 'given_name')

        pyamf.register_class(Person, 'spam.eggs.Person')

        self.buf.write('\n+!spam.eggs.Person\x17family_name\x15given_name\x06'
            '\x07Doe\x06\tJane\x02\x06\x06\x04\x06\x08\x01')
        self.buf.seek(0)

        foo = self.decoder.readElement()

        self.assertTrue(isinstance(foo, Person))
        self.assertEquals(foo.family_name, 'Doe')
        self.assertEquals(foo.given_name, 'Jane')
        self.assertEquals(self.buf.remaining(), 0)

    def test_default_proxy_flag(self):
        amf3.use_proxies_default = True
        decoder = amf3.Decoder(self.buf, context=self.context)
        self.assertTrue(decoder.use_proxies)
        amf3.use_proxies_default = False
        decoder = amf3.Decoder(self.buf, context=self.context)
        self.assertFalse(decoder.use_proxies)

    def test_ioerror_buffer_position(self):
        """
        Test to ensure that if an IOError is raised by `readElement` that
        the original position of the stream is restored.
        """
        bytes = pyamf.encode(u'foo', [1, 2, 3], encoding=pyamf.AMF3).getvalue()

        self.buf.write(bytes[:-1])
        self.buf.seek(0)

        self.decoder.readElement()
        self.assertEquals(self.buf.tell(), 5)

        self.assertRaises(IOError, self.decoder.readElement)
        self.assertEquals(self.buf.tell(), 5)

    def test_timezone(self):
        self.decoder.timezone_offset = datetime.timedelta(hours=-5)

        self.buf.write('\x08\x01Br>\xc6\xf5w\x80\x00')
        self.buf.seek(0)

        f = self.decoder.readElement()

        self.assertEquals(f, datetime.datetime(2009, 9, 24, 9, 23, 23))


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
        alias = pyamf.register_class(Spam, 'abc.xyz')
        class_defs = self.context.class_ref

        x = Spam({'spam': 'eggs'})
        y = Spam({'foo': 'bar'})

        self.encoder.writeElement(x)
        self.assertEquals(len(class_defs), 1)
        cd = class_defs[0]

        self.assertTrue(cd.alias is alias)

        self.assertEquals(self.stream.getvalue(), '\n\x0b\x0fabc.xyz\tspam\x06\teggs\x01')

        pos = self.stream.tell()
        self.encoder.writeElement(y)
        self.assertEquals(self.stream.getvalue()[pos:], '\n\x01\x07foo\x06\x07bar\x01')

    def test_static(self):
        alias = pyamf.register_class(Spam, 'abc.xyz')

        alias.dynamic = False

        x = Spam({'spam': 'eggs'})
        self.encoder.writeElement(x)
        self.assertEquals(self.stream.getvalue(), '\n\x03\x0fabc.xyz')
        pyamf.unregister_class(Spam)
        self.stream.truncate()
        self.encoder.context.clear()

        alias = pyamf.register_class(Spam, 'abc.xyz')
        alias.dynamic = False
        alias.static_attrs = ['spam']

        x = Spam({'spam': 'eggs', 'foo': 'bar'})
        self.encoder.writeElement(x)
        self.assertEquals(self.stream.getvalue(), '\n\x13\x0fabc.xyz\tspam\x06\teggs')

    def test_dynamic(self):
        pyamf.register_class(Spam, 'abc.xyz')

        x = Spam({'spam': 'eggs'})
        self.encoder.writeElement(x)

        self.assertEquals(self.stream.getvalue(), '\n\x0b\x0fabc.xyz\tspam\x06\teggs\x01')

    def test_combined(self):
        alias = pyamf.register_class(Spam, 'abc.xyz')

        alias.static_attrs = ['spam']

        x = Spam({'spam': 'foo', 'eggs': 'bar'})
        self.encoder.writeElement(x)

        buf = self.stream.getvalue()

        self.assertEquals(buf, '\n\x1b\x0fabc.xyz\tspam\x06\x07foo\teggs\x06\x07bar\x01')

    def test_external(self):
        alias = pyamf.register_class(Spam, 'abc.xyz')

        alias.external = True

        x = Spam({'spam': 'eggs'})
        self.encoder.writeElement(x)

        buf = self.stream.getvalue()

        # an inline object with and inline class-def, encoding = 0x01, 1 attr

        self.assertEquals(buf[:2], '\x0a\x07')
        # class alias name
        self.assertEquals(buf[2:10], '\x0fabc.xyz')

        self.assertEquals(len(buf), 10)

    def test_anonymous_class_references(self):
        """
        Test to ensure anonymous class references with static attributes
        are encoded propertly
        """
        class Foo:
            class __amf__:
                static = ('name', 'id', 'description')

        x = Foo()
        x.id = 1
        x.name = 'foo'
        x.description = None

        y = Foo()
        y.id = 2
        y.name = 'bar'
        y.description = None

        self.encoder.writeElement([x, y])

        self.assertEquals(self.stream.getvalue(), '\t\x05\x01\n;\x01\x17description\x05id\tname\x01\x04\x01\x06\x07foo\x01\n\x01\x01\x04\x02\x06\x07bar\x01')


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
        self.assertEquals(self.context.classes, {})
        self.assertEquals(self.context.class_ref, {})

        self.stream.write('\x0a\x13\x0fabc.xyz\x09spam\x06\x09eggs')
        self.stream.seek(0, 0)

        obj = self.decoder.readElement()

        class_def = self.context.class_ref[0]

        self.assertEquals(class_def.static_properties, ['spam'])

        self.assertTrue(isinstance(obj, Spam))
        self.assertEquals(obj.__dict__, {'spam': 'eggs'})

    def test_dynamic(self):
        pyamf.register_class(Spam, 'abc.xyz')

        self.assertEquals(self.context.objects, [])
        self.assertEquals(self.context.strings, [])
        self.assertEquals(self.context.classes, {})

        self.stream.write('\x0a\x0b\x0fabc.xyz\x09spam\x06\x09eggs\x01')
        self.stream.seek(0, 0)

        obj = self.decoder.readElement()

        class_def = self.context.class_ref[0]

        self.assertEquals(class_def.static_properties, [])

        self.assertTrue(isinstance(obj, Spam))
        self.assertEquals(obj.__dict__, {'spam': 'eggs'})

    def test_combined(self):
        """
        This tests an object encoding with static properties and dynamic
        properties
        """
        pyamf.register_class(Spam, 'abc.xyz')

        self.assertEquals(self.context.objects, [])
        self.assertEquals(self.context.strings, [])
        self.assertEquals(self.context.classes, {})

        self.stream.write('\x0a\x1b\x0fabc.xyz\x09spam\x06\x09eggs\x07baz\x06\x07'
            'nat\x01')
        self.stream.seek(0, 0)

        obj = self.decoder.readElement()

        class_def = self.context.class_ref[0]

        self.assertEquals(class_def.static_properties, ['spam'])

        self.assertTrue(isinstance(obj, Spam))
        self.assertEquals(obj.__dict__, {'spam': 'eggs', 'baz': 'nat'})

    def test_external(self):
        alias = pyamf.register_class(Spam, 'abc.xyz')
        alias.external = True

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
        self.assertEquals(self.stream.getvalue(), '\t\x01\tspam\x06\teggs\x01')
        self.stream.truncate()

        # check references
        x.writeObject(obj)
        self.assertEquals(self.stream.getvalue(), '\t\x00')
        self.stream.truncate()

        # check force no references, should include class def ref and refs to
        # string
        x.writeObject(obj, False)
        self.assertEquals(self.stream.getvalue(), '\t\x01\x00\x06\x02\x01')

    def test_object_proxy(self):
        self.encoder.use_proxies = True
        x = amf3.DataOutput(self.encoder)
        obj = {'spam': 'eggs'}

        x.writeObject(obj)
        self.assertEquals(self.stream.getvalue(),
            '\n\x07;flex.messaging.io.ObjectProxy\n\x0b\x01\tspam\x06\teggs\x01')
        self.stream.truncate()

        # check references
        x.writeObject(obj)
        self.assertEquals(self.stream.getvalue(), '\n\x00')
        self.stream.truncate()

    def test_object_proxy_mixed_array(self):
        self.encoder.use_proxies = True
        x = amf3.DataOutput(self.encoder)
        obj = pyamf.MixedArray(spam='eggs')

        x.writeObject(obj)
        self.assertEquals(self.stream.getvalue(),
            '\n\x07;flex.messaging.io.ObjectProxy\n\x0b\x01\tspam\x06\teggs\x01')
        self.stream.truncate()

        # check references
        x.writeObject(obj)
        self.assertEquals(self.stream.getvalue(), '\n\x00')
        self.stream.truncate()

    def test_object_proxy_inside_list(self):
        self.encoder.use_proxies = True
        x = amf3.DataOutput(self.encoder)
        obj = [{'spam': 'eggs'}]

        x.writeObject(obj)
        self.assertEquals(self.stream.getvalue(),
            '\n\x07Cflex.messaging.io.ArrayCollection\t\x03\x01\n\x07;'
            'flex.messaging.io.ObjectProxy\n\x0b\x01\tspam\x06\teggs\x01')

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

        self.assertRaises(OverflowError, x.writeUnsignedInt, -55)

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

        alias = pyamf.register_class(A, 'A')
        alias.static_attrs = ['a']

        class B(A):
            pass

        alias = pyamf.register_class(B, 'B')
        alias.static_attrs = ['b']

        x = B()
        x.a = 'spam'
        x.b = 'eggs'

        stream = util.BufferedByteStream()
        encoder = pyamf._get_encoder_class(pyamf.AMF3)(stream)

        encoder.writeElement(x)

        self.assertEquals(stream.getvalue(),
            '\n+\x03B\x03a\x03b\x06\tspam\x06\teggs\x01')

    def test_deep(self):
        class A(object):
            pass

        alias = pyamf.register_class(A, 'A')
        alias.static_attrs = ['a']

        class B(A):
            pass

        alias = pyamf.register_class(B, 'B')
        alias.static_attrs = ['b']

        class C(B):
            pass

        alias = pyamf.register_class(C, 'C')
        alias.static_attrs = ['c']

        x = C()
        x.a = 'spam'
        x.b = 'eggs'
        x.c = 'foo'

        stream = util.BufferedByteStream()
        encoder = pyamf._get_encoder_class(pyamf.AMF3)(stream)

        encoder.writeElement(x)

        self.assertEquals(stream.getvalue(),
            '\n;\x03C\x03a\x03b\x03c\x06\tspam\x06\teggs\x06\x07foo\x01')


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


class ComplexEncodingTestCase(unittest.TestCase, _util.BaseEncoderMixIn):
    amf_version = pyamf.AMF3

    class TestObject(object):
        def __init__(self):
            self.number = None
            self.test_list = ['test']
            self.sub_obj = None
            self.test_dict = {'test': 'ignore'}

        def __repr__(self):
            return '<TestObject %r @ 0x%x>' % (self.__dict__, id(self))

    class TestSubObject(object):
        def __init__(self):
            self.number = None

        def __repr__(self):
            return '<TestSubObject %r @ 0x%x>' % (self.__dict__, id(self))

    def setUp(self):
        _util.BaseEncoderMixIn.setUp(self)

        pyamf.register_class(self.TestObject, 'test_complex.test')
        pyamf.register_class(self.TestSubObject, 'test_complex.sub')

    def tearDown(self):
        pyamf.unregister_class(self.TestObject)
        pyamf.unregister_class(self.TestSubObject)

    def build_complex(self, max=5):
        test_objects = []

        for i in range(0, max):
            test_obj = self.TestObject()
            test_obj.number = i
            test_obj.sub_obj = self.TestSubObject()
            test_obj.sub_obj.number = i
            test_objects.append(test_obj)

        return test_objects

    def complex_test(self):
        class_defs = self.context.class_ref
        classes = self.context.classes

        self.assertEquals(len(classes), 3)
        self.assertTrue(self.TestObject in classes.keys())
        self.assertTrue(self.TestSubObject in classes.keys())

        self.assertEquals(len(class_defs), 3)
        self.assertEquals(self.TestObject, class_defs[1].alias.klass)
        self.assertEquals(self.TestSubObject, class_defs[2].alias.klass)

    def complex_encode_decode_test(self, decoded):
        for obj in decoded:
            self.assertEquals(self.TestObject, obj.__class__)
            self.assertEquals(self.TestSubObject, obj.sub_obj.__class__)

    def test_complex_dict(self):
        complex = {'element': 'ignore', 'objects': self.build_complex()}

        self.encoder.writeElement(complex)
        self.complex_test()

    def test_complex_encode_decode_dict(self):
        complex = {'element': 'ignore', 'objects': self.build_complex()}
        self.encoder.writeElement(complex)
        encoded = self.encoder.stream.getvalue()

        context = amf3.Context()
        decoded = amf3.Decoder(encoded, context).readElement()

        self.complex_encode_decode_test(decoded['objects'])

    def test_class_refs(self):
        class_defs = self.context.class_ref
        classes = self.context.classes

        self.assertEquals(class_defs, {})
        self.assertEquals(classes, {})

        a = self.TestSubObject()
        b = self.TestSubObject()

        self.encoder.writeInstance(a)

        cd = class_defs[0]

        self.assertEqual(cd.reference, '\x01')
        self.assertEquals(class_defs, {0: cd})
        self.assertEquals(classes, {self.TestSubObject: cd})

        self.encoder.writeElement({'foo': 'bar'})

        cd2 = class_defs[1]

        self.assertEquals(class_defs, {0: cd, 1: cd2})
        self.assertEquals(classes, {self.TestSubObject: cd, dict: cd2})
        self.assertEquals(cd2.reference, '\x05')

        self.encoder.writeElement({})

        self.assertEquals(class_defs, {0: cd, 1: cd2})
        self.assertEquals(classes, {self.TestSubObject: cd, dict: cd2})

        self.encoder.writeElement(b)

        self.assertEquals(class_defs, {0: cd, 1: cd2})
        self.assertEquals(classes, {self.TestSubObject: cd, dict: cd2})

        c = self.TestObject()

        self.encoder.writeElement(c)

        cd3 = class_defs[2]

        self.assertEquals(class_defs, {0: cd, 1: cd2, 2: cd3})
        self.assertEquals(classes,
            {self.TestSubObject: cd, dict: cd2, self.TestObject: cd3})

        self.assertEquals(cd3.reference, '\x09')


class ExceptionEncodingTestCase(_util.ClassCacheClearingTestCase):
    """
    Tests for encoding exceptions.
    """

    def setUp(self):
        _util.ClassCacheClearingTestCase.setUp(self)

        self.buffer = util.BufferedByteStream()
        self.encoder = amf3.Encoder(self.buffer)

    def test_exception(self):
        try:
            raise Exception('foo bar')
        except Exception, e:
            self.encoder.writeElement(e)

        self.assertEquals(self.buffer.getvalue(), '\n\x0b\x01\x0fmessage\x06'
            '\x0ffoo bar\tname\x06\x13Exception\x01')

    def test_user_defined(self):
        class FooBar(Exception):
            pass

        try:
            raise FooBar('foo bar')
        except Exception, e:
            self.encoder.writeElement(e)

        self.assertEquals(self.buffer.getvalue(), '\n\x0b\x01\x0fmessage\x06'
            '\x0ffoo bar\tname\x06\rFooBar\x01')

    def test_typed(self):
        class XYZ(Exception):
            pass

        pyamf.register_class(XYZ, 'foo.bar')

        try:
            raise XYZ('blarg')
        except Exception, e:
            self.encoder.writeElement(e)

        self.assertEquals(self.buffer.getvalue(), '\n\x0b\x0ffoo.bar\x0f'
            'message\x06\x0bblarg\tname\x06\x07XYZ\x01')


def suite():
    suite = unittest.TestSuite()

    test_cases = [
        TypesTestCase,
        ClassDefinitionTestCase,
        ContextTestCase,
        EncoderTestCase,
        DecoderTestCase,
        ObjectEncodingTestCase,
        ObjectDecodingTestCase,
        DataOutputTestCase,
        DataInputTestCase,
        ClassInheritanceTestCase,
        HelperTestCase,
        ComplexEncodingTestCase,
        ExceptionEncodingTestCase
    ]

    for tc in test_cases:
        suite.addTest(unittest.makeSuite(tc))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
