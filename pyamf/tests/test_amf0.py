# -*- coding: utf-8 -*-
#
# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Tests for AMF0 Implementation.

@since: 0.1.0
"""

import unittest
import datetime
import types

import pyamf
from pyamf import amf0, util
from pyamf.tests.util import (
    EncoderMixIn, DecoderMixIn, ClassCacheClearingTestCase, Spam, ClassicSpam)


class TypesTestCase(unittest.TestCase):
    """
    Tests the type mappings.
    """

    def test_types(self):
        self.assertEqual(amf0.TYPE_NUMBER, '\x00')
        self.assertEqual(amf0.TYPE_BOOL, '\x01')
        self.assertEqual(amf0.TYPE_STRING, '\x02')
        self.assertEqual(amf0.TYPE_OBJECT, '\x03')
        self.assertEqual(amf0.TYPE_MOVIECLIP, '\x04')
        self.assertEqual(amf0.TYPE_NULL, '\x05')
        self.assertEqual(amf0.TYPE_UNDEFINED, '\x06')
        self.assertEqual(amf0.TYPE_REFERENCE, '\x07')
        self.assertEqual(amf0.TYPE_MIXEDARRAY, '\x08')
        self.assertEqual(amf0.TYPE_OBJECTTERM, '\x09')
        self.assertEqual(amf0.TYPE_ARRAY, '\x0a')
        self.assertEqual(amf0.TYPE_DATE, '\x0b')
        self.assertEqual(amf0.TYPE_LONGSTRING, '\x0c')
        self.assertEqual(amf0.TYPE_UNSUPPORTED, '\x0d')
        self.assertEqual(amf0.TYPE_RECORDSET, '\x0e')
        self.assertEqual(amf0.TYPE_XML, '\x0f')
        self.assertEqual(amf0.TYPE_TYPEDOBJECT, '\x10')
        self.assertEqual(amf0.TYPE_AMF3, '\x11')


class ContextTestCase(unittest.TestCase):
    def test_create(self):
        c = amf0.Context()

        self.assertEqual(c.objects, [])
        self.assertEqual(len(c.objects), 0)

    def test_add(self):
        x = amf0.Context()
        y = [1, 2, 3]

        self.assertEqual(x.addObject(y), 0)
        self.assertTrue(y in x.objects)
        self.assertEqual(len(x.objects), 1)

    def test_clear(self):
        x = amf0.Context()
        x.clear()

        y = [1, 2, 3]

        x.addObject(y)
        x.addAMF3Object({})
        x.clear()

        self.assertEqual(x.objects, [])
        self.assertEqual(len(x.objects), 0)
        self.assertFalse(y in x.objects)

        self.assertFalse(x.hasAMF3ObjectReference({}))

    def test_get_by_reference(self):
        x = amf0.Context()
        y = [1, 2, 3]
        z = {'spam': 'eggs'}

        x.addObject(y)
        x.addObject(z)

        self.assertEqual(x.getObject(0), y)
        self.assertEqual(x.getObject(1), z)
        self.assertEqual(x.getObject(2), None)
        self.assertRaises(TypeError, x.getObject, '')
        self.assertRaises(TypeError, x.getObject, 2.2323)

    def test_get_reference(self):
        x = amf0.Context()
        y = [1, 2, 3]
        z = {'spam': 'eggs'}

        ref1 = x.addObject(y)
        ref2 = x.addObject(z)

        self.assertEqual(x.getObjectReference(y), ref1)
        self.assertEqual(x.getObjectReference(z), ref2)
        self.assertEqual(x.getObjectReference({}), -1)


class EncoderTestCase(ClassCacheClearingTestCase, EncoderMixIn):
    """
    Tests the output from the AMF0 L{Encoder<pyamf.amf0.Encoder>} class.
    """

    amf_type = pyamf.AMF0

    def setUp(self):
        ClassCacheClearingTestCase.setUp(self)
        EncoderMixIn.setUp(self)

    def test_number(self):
        self.assertEncoded(0, '\x00\x00\x00\x00\x00\x00\x00\x00\x00')
        self.assertEncoded(0.2, '\x00\x3f\xc9\x99\x99\x99\x99\x99\x9a')
        self.assertEncoded(1, '\x00\x3f\xf0\x00\x00\x00\x00\x00\x00')
        self.assertEncoded(42, '\x00\x40\x45\x00\x00\x00\x00\x00\x00')
        self.assertEncoded(-123, '\x00\xc0\x5e\xc0\x00\x00\x00\x00\x00')
        self.assertEncoded(1.23456789, '\x00\x3f\xf3\xc0\xca\x42\x83\xde\x1b')

    def test_boolean(self):
        self.assertEncoded(True, '\x01\x01')
        self.assertEncoded(False, '\x01\x00')

    def test_string(self):
        self.assertEncoded('', '\x02\x00\x00')
        self.assertEncoded('hello', '\x02\x00\x05hello')
        # unicode taken from http://www.columbia.edu/kermit/utf8.html
        self.assertEncoded(u'ᚠᛇᚻ', '\x02\x00\t\xe1\x9a\xa0\xe1\x9b\x87\xe1\x9a\xbb')

    def test_null(self):
        self.assertEncoded(None, '\x05')

    def test_undefined(self):
        self.assertEncoded(pyamf.Undefined, '\x06')

    def test_list(self):
        self.assertEncoded([], '\x0a\x00\x00\x00\x00')
        self.assertEncoded([1, 2, 3],
            '\x0a\x00\x00\x00\x03\x00\x3f\xf0\x00\x00\x00\x00\x00\x00\x00\x40'
            '\x00\x00\x00\x00\x00\x00\x00\x00\x40\x08\x00\x00\x00\x00\x00\x00')
        self.assertEncoded((1, 2, 3), '\x0a\x00\x00\x00\x03\x00\x3f\xf0\x00'
            '\x00\x00\x00\x00\x00\x00\x40\x00\x00\x00\x00\x00\x00\x00\x00'
            '\x40\x08\x00\x00\x00\x00\x00\x00')

    def test_longstring(self):
        s = 'a' * 65537

        self.assertEncoded(s, '\x0c\x00\x01\x00\x01' + s)

    def test_dict(self):
        self.assertEncoded({'a': 'a'}, '\x03\x00\x01a\x02\x00\x01a\x00\x00\t')

    def test_mixed_array(self):
        d = pyamf.MixedArray(a=1, b=2, c=3)

        self.assertEncoded(d, '\x08\x00\x00\x00\x00', (
            '\x00\x01a\x00?\xf0\x00\x00\x00\x00\x00\x00',
            '\x00\x01c\x00@\x08\x00\x00\x00\x00\x00\x00',
            '\x00\x01b\x00@\x00\x00\x00\x00\x00\x00\x00'
        ), '\x00\x00\t')

    def test_date(self):
        self.assertEncoded(datetime.datetime(2005, 3, 18, 1, 58, 31),
            '\x0bBp+6!\x15\x80\x00\x00\x00')
        self.assertEncoded(datetime.date(2003, 12, 1),
            '\x0bBo%\xe2\xb2\x80\x00\x00\x00\x00')
        self.assertEncoded(datetime.datetime(2009, 3, 8, 23, 30, 47, 770122),
            '\x0bBq\xfe\x86\xca5\xa1\xf4\x00\x00')

        self.assertRaises(pyamf.EncodeError, self.encode, datetime.time(22, 3))

    def test_xml(self):
        xml = '<a><b>hello world</b></a>'

        self.assertEncoded(util.ET.fromstring(xml),
            '\x0f\x00\x00\x00\x19' + xml)

    def test_xml_references(self):
        xml = '<a><b>hello world</b></a>'
        x = util.ET.fromstring(xml)

        self.assertEncoded([x, x], '\n\x00\x00\x00\x02'
                '\x0f\x00\x00\x00\x19<a><b>hello world</b></a>'
                '\x0f\x00\x00\x00\x19<a><b>hello world</b></a>')

    def test_object(self):
        self.assertEncoded({'a': 'b'}, '\x03\x00\x01a\x02\x00\x01b\x00\x00\x09')

    def test_force_amf3(self):
        alias = pyamf.register_class(Spam, 'spam.eggs')
        alias.amf3 = True

        x = Spam()
        x.x = 'y'

        self.assertEncoded(x, '\x11\n\x0b\x13spam.eggs\x03x\x06\x03y\x01')

    def test_typed_object(self):
        pyamf.register_class(Spam, alias='org.pyamf.spam')

        x = Spam()
        x.baz = 'hello'

        self.assertEncoded(x, '\x10\x00\x0eorg.pyamf.spam\x00\x03baz'
            '\x02\x00\x05hello\x00\x00\t')

    def test_complex_list(self):
        self.assertEncoded([[1.0]], '\x0a\x00\x00\x00\x01\x0a\x00\x00\x00\x01'
            '\x00\x3f\xf0\x00\x00\x00\x00\x00\x00')

        self.assertEncoded([['test', 'test', 'test', 'test']],
            '\x0a\x00\x00\x00\x01\x0a\x00\x00\x00\x04' + ('\x02\x00\x04test' * 4))

        x = {'a': 'spam', 'b': 'eggs'}

        self.assertEncoded([[x, x]], '\n\x00\x00\x00\x01\n\x00\x00\x00\x02'
            '\x03\x00\x01a\x02\x00\x04spam\x00\x01b\x02\x00\x04eggs\x00\x00'
            '\t\x07\x00\x02')

    def test_amf3(self):
        self.encoder.use_amf3 = True

        o = Spam()
        self.context.addAMF3Object(o)

        self.assertEncoded(o, '\x11\n\x0b\x01\x01')

    def test_anonymous(self):
        pyamf.register_class(Spam)

        x = Spam()
        x.spam = 'eggs'
        x.hello = 'world'

        self.assertEncoded(x, '\x03', ('\x00\x05hello\x02\x00\x05world',
            '\x00\x04spam\x02\x00\x04eggs'), '\x00\x00\t')

    def test_dynamic(self):
        x = Spam()

        x.foo = 'bar'
        x.hello = 'world'

        alias = pyamf.register_class(Spam)

        alias.exclude_attrs = ['foo']

        alias.compile()

        self.assertTrue(alias.dynamic)

        self.assertEncoded(x, '\x03\x00\x05hello\x02\x00\x05world\x00\x00\t')

    def test_dynamic_static(self):
        x = Spam()

        x.foo = 'bar'
        x.hello = 'world'

        alias = pyamf.register_class(Spam)

        alias.static_attrs = ['hello']
        alias.compile()

        self.assertTrue(alias.dynamic)

        self.assertEncoded(x, '\x03', ('\x00\x05hello\x02\x00\x05world',
            '\x00\x03foo\x02\x00\x03bar'), '\x00\x00\t')

    def test_dynamic_registered(self):
        x = Spam()

        x.foo = 'bar'
        x.hello = 'world'

        alias = pyamf.register_class(Spam, 'x')

        alias.exclude_attrs = ['foo']

        alias.compile()

        self.assertTrue(alias.dynamic)

        self.assertEncoded(x, '\x10\x00\x01x', '\x00\x05hello\x02\x00\x05world',
            '\x00\x00\t')

    def test_custom_type(self):
        def write_as_list(list_interface_obj, encoder):
            list_interface_obj.ran = True
            self.assertEqual(id(encoder), id(self.encoder))

            return list(list_interface_obj)

        class ListWrapper(object):
            ran = False

            def __iter__(self):
                return iter([1, 2, 3])

        pyamf.add_type(ListWrapper, write_as_list)
        x = ListWrapper()

        self.encoder.writeElement(x)
        self.assertEqual(x.ran, True)

        self.assertEqual(self.buf.getvalue(), '\n\x00\x00\x00\x03\x00?\xf0'
            '\x00\x00\x00\x00\x00\x00\x00@\x00\x00\x00\x00\x00\x00\x00\x00@'
            '\x08\x00\x00\x00\x00\x00\x00')

    def test_old_style_classes(self):
        class Person:
            pass

        pyamf.register_class(Person, 'spam.eggs.Person')

        u = Person()
        u.family_name = 'Doe'
        u.given_name = 'Jane'

        self.encoder.writeElement(u)

        self.assertEncoded(u, '\x10\x00\x10spam.eggs.Person', (
            '\x00\x0bfamily_name\x02\x00\x03Doe',
            '\x00\ngiven_name\x02\x00\x04Jane'
        ), '\x00\x00\t')

    def test_slots(self):
        class Person(object):
            __slots__ = ('family_name', 'given_name')

        u = Person()
        u.family_name = 'Doe'
        u.given_name = 'Jane'

        self.assertEncoded(u, '\x03', (
            '\x00\x0bfamily_name\x02\x00\x03Doe',
            '\x00\ngiven_name\x02\x00\x04Jane'
        ), '\x00\x00\t')

    def test_slots_registered(self):
        class Person(object):
            __slots__ = ('family_name', 'given_name')

        u = Person()
        u.family_name = 'Doe'
        u.given_name = 'Jane'

        pyamf.register_class(Person, 'spam.eggs.Person')

        self.assertEncoded(u, '\x10\x00\x10spam.eggs.Person', (
            '\x00\x0bfamily_name\x02\x00\x03Doe',
            '\x00\ngiven_name\x02\x00\x04Jane'
        ), '\x00\x00\t')

    def test_elementtree_tag(self):
        """
        Pretend to look like an ElementTree object to try to fool PyAMF into
        encoding an xml type.
        """
        class NotAnElement(object):
            items = lambda self: []

            def __iter__(self):
                return iter([])

        foo = NotAnElement()
        foo.tag = 'foo'
        foo.text = 'bar'
        foo.tail = None

        self.assertEncoded(foo, '\x03', (
            '\x00\x04text\x02\x00\x03bar',
            '\x00\x04tail\x05',
            '\x00\x03tag\x02\x00\x03foo',
        ), '\x00\x00\t')

    def test_funcs(self):
        def x():
            yield 2

        for i in (chr, self.assertRaises, lambda x: x, x(), pyamf):
            self.assertRaises(pyamf.EncodeError, self.encoder.writeElement, i)

    def test_external_subclassed_list(self):
        class L(list):
            class __amf__:
                external = True

            def __readamf__(self, o):
                pass

            def __writeamf__(self, o):
                pass

        pyamf.register_class(L, 'a')

        a = L()

        a.append('foo')
        a.append('bar')

        self.assertEncoded(a, '\x10\x00\x01a\x00\x00\t')

    def test_nonexternal_subclassed_list(self):
        class L(list):
            pass

        pyamf.register_class(L, 'a')

        a = L()

        a.append('foo')
        a.append('bar')

        self.assertEncoded(a, '\n\x00\x00\x00\x02\x02\x00\x03foo\x02\x00\x03bar')

    def test_amf3_xml(self):
        self.encoder.use_amf3 = True
        xml = '<root><sections><section /><section /></sections></root>'

        self.assertEncoded(util.ET.fromstring(xml), '\x11\x0bq' + xml)

    def test_use_amf3(self):
        self.encoder.use_amf3 = True

        x = {'foo': 'bar', 'baz': 'gak'}

        self.assertEncoded(x, '\x11\n\x0b', ('\x01\x07foo\x06\x07bar',
            '\x07baz\x06\x07gak\x01'))

    def test_static_attrs(self):
        class Foo(object):
            class __amf__:
                static = ('foo', 'bar')

        pyamf.register_class(Foo)

        x = Foo()
        x.foo = 'baz'
        x.bar = 'gak'

        self.assertEncoded(x, '\x03', ('\x00\x03bar\x02\x00\x03gak',
            '\x00\x03foo\x02\x00\x03baz'), '\x00\x00\t')

    def test_class(self):
        class Classic:
            pass

        class New(object):
            pass

        self.assertRaises(pyamf.EncodeError, self.encoder.writeElement, Classic)
        self.assertRaises(pyamf.EncodeError, self.encoder.writeElement, New)

    def test_timezone(self):
        d = datetime.datetime(2009, 9, 24, 14, 23, 23)
        self.encoder.timezone_offset = datetime.timedelta(hours=-5)

        self.assertEncoded(d, '\x0bBr>\xd8\x1f\xff\x80\x00\x00\x00')


class DecoderTestCase(ClassCacheClearingTestCase, DecoderMixIn):
    """
    Tests the output from the AMF0 L{Decoder<pyamf.amf0.Decoder>} class.
    """

    amf_type = pyamf.AMF0

    def setUp(self):
        ClassCacheClearingTestCase.setUp(self)
        DecoderMixIn.setUp(self)

    def test_undefined(self):
        self.assertDecoded(pyamf.Undefined, '\x06')

    def test_number(self):
        self.assertDecoded(0, '\x00\x00\x00\x00\x00\x00\x00\x00\x00')
        self.assertDecoded(0.2, '\x00\x3f\xc9\x99\x99\x99\x99\x99\x9a')
        self.assertDecoded(1, '\x00\x3f\xf0\x00\x00\x00\x00\x00\x00')
        self.assertDecoded(42, '\x00\x40\x45\x00\x00\x00\x00\x00\x00')
        self.assertDecoded(-123, '\x00\xc0\x5e\xc0\x00\x00\x00\x00\x00')
        self.assertDecoded(1.23456789, '\x00\x3f\xf3\xc0\xca\x42\x83\xde\x1b')

    def test_number_types(self):
        nr_types = [
            ('\x00\x00\x00\x00\x00\x00\x00\x00\x00', int),
            ('\x00\x3f\xc9\x99\x99\x99\x99\x99\x9a', float),
            ('\x00\x3f\xf0\x00\x00\x00\x00\x00\x00', int),
            ('\x00\x40\x45\x00\x00\x00\x00\x00\x00', int),
            ('\x00\xc0\x5e\xc0\x00\x00\x00\x00\x00', int),
            ('\x00\x3f\xf3\xc0\xca\x42\x83\xde\x1b', float),
            ('\x00\xff\xf8\x00\x00\x00\x00\x00\x00', float), # nan
            ('\x00\xff\xf0\x00\x00\x00\x00\x00\x00', float), # -inf
            ('\x00\x7f\xf0\x00\x00\x00\x00\x00\x00', float), # inf
        ]

        for t in nr_types:
            bytes, expected_type = t
            self.buf.truncate()
            self.buf.write(bytes)
            self.buf.seek(0)
            self.assertEqual(type(self.decoder.readElement()), expected_type)

    def test_infinites(self):
        self.buf.truncate()
        self.buf.write('\x00\xff\xf8\x00\x00\x00\x00\x00\x00')
        self.buf.seek(0)
        x = self.decoder.readElement()
        self.assertTrue(util.isNaN(x))

        self.buf.truncate()
        self.buf.write('\x00\xff\xf0\x00\x00\x00\x00\x00\x00')
        self.buf.seek(0)
        x = self.decoder.readElement()
        self.assertTrue(util.isNegInf(x))

        self.buf.truncate()
        self.buf.write('\x00\x7f\xf0\x00\x00\x00\x00\x00\x00')
        self.buf.seek(0)
        x = self.decoder.readElement()
        self.assertTrue(util.isPosInf(x))

    def test_boolean(self):
        self.assertDecoded(True, '\x01\x01')
        self.assertDecoded(False, '\x01\x00')

    def test_string(self):
        self.assertDecoded('', '\x02\x00\x00')
        self.assertDecoded('hello', '\x02\x00\x05hello')
        self.assertDecoded(u'ᚠᛇᚻ',
            '\x02\x00\t\xe1\x9a\xa0\xe1\x9b\x87\xe1\x9a\xbb')

    def test_longstring(self):
        a = 'a' * 65537

        self.assertDecoded(a, '\x0c\x00\x01\x00\x01' + a)

    def test_null(self):
        self.assertDecoded(None, '\x05')

    def test_list(self):
        self.assertDecoded([], '\x0a\x00\x00\x00\x00')
        self.assertDecoded([1, 2, 3], '\x0a\x00\x00\x00\x03\x00\x3f\xf0\x00'
            '\x00\x00\x00\x00\x00\x00\x40\x00\x00\x00\x00\x00\x00\x00\x00\x40'
            '\x08\x00\x00\x00\x00\x00\x00')

    def test_dict(self):
        bytes = '\x08\x00\x00\x00\x00\x00\x01\x61\x02\x00\x01\x61\x00\x00\x09'

        self.assertDecoded({'a': 'a'}, bytes)

        self.buf.write(bytes)
        self.buf.seek(0)
        d = self.decoder.readElement()

        self.assertEqual(type(d.keys()[0]), str)

    def test_mixed_array(self):
        bytes = ('\x08\x00\x00\x00\x00\x00\x01a\x00?\xf0\x00\x00\x00\x00\x00'
            '\x00\x00\x01c\x00@\x08\x00\x00\x00\x00\x00\x00\x00\x01b\x00@\x00'
            '\x00\x00\x00\x00\x00\x00\x00\x00\t')

        self.assertDecoded(pyamf.MixedArray(a=1, b=2, c=3), bytes)

        self.buf.write(bytes)
        self.buf.seek(0)
        d = self.decoder.readElement()

        self.assertEqual(type(d.keys()[0]), str)

    def test_date(self):
        self.assertDecoded(datetime.datetime(2005, 3, 18, 1, 58, 31),
            '\x0bBp+6!\x15\x80\x00\x00\x00')
        self.assertDecoded(datetime.datetime(2009, 3, 8, 23, 30, 47, 770122),
            '\x0bBq\xfe\x86\xca5\xa1\xf4\x00\x00')

    def test_xml(self):
        e = '<a><b>hello world</b></a>'
        ret = self.decode('\x0f\x00\x00\x00\x19' + e)

        self.assertEqual(util.ET.tostring(ret), e)

    def test_xml_references(self):
        self.buf.truncate(0)
        self.buf.write('\x0f\x00\x00\x00\x19<a><b>hello world</b></a>'
            '\x07\x00\x00')
        self.buf.seek(0)

        self.assertEqual(
            util.ET.tostring(util.ET.fromstring('<a><b>hello world</b></a>')),
            util.ET.tostring(self.decoder.readElement()))

        self.assertEqual(
            util.ET.tostring(util.ET.fromstring('<a><b>hello world</b></a>')),
            util.ET.tostring(self.decoder.readElement()))

    def test_object(self):
        bytes = '\x03\x00\x01a\x02\x00\x01b\x00\x00\x09'

        self.assertDecoded({'a': 'b'}, bytes)

        self.buf.write(bytes)
        self.buf.seek(0)
        d = self.decoder.readElement()

        self.assertEqual(type(d.keys()[0]), str)

    def test_registered_class(self):
        pyamf.register_class(Spam, alias='org.pyamf.spam')

        bytes = ('\x10\x00\x0eorg.pyamf.spam\x00\x03baz'
            '\x02\x00\x05hello\x00\x00\x09')

        obj = self.decode(bytes)

        self.assertEqual(type(obj), Spam)

        self.assertTrue(hasattr(obj, 'baz'))
        self.assertEqual(obj.baz, 'hello')

    def test_complex_list(self):
        x = datetime.datetime(2007, 11, 3, 8, 7, 37, 437000)

        self.assertDecoded([['test','test','test','test']],
            '\x0A\x00\x00\x00\x01\x0A\x00\x00\x00\x04\x02\x00\x04\x74\x65\x73'
            '\x74\x02\x00\x04\x74\x65\x73\x74\x02\x00\x04\x74\x65\x73\x74\x02'
            '\x00\x04\x74\x65\x73\x74')
        self.assertDecoded([x], '\x0a\x00\x00\x00\x01\x0b\x42\x71\x60\x48\xcf'
            '\xed\xd0\x00\x00\x00')
        self.assertDecoded(
            [[{u'a': u'spam', u'b': u'eggs'}, {u'a': u'spam', u'b': u'eggs'}]],
            '\n\x00\x00\x00\x01\n\x00\x00\x00\x02\x08\x00\x00\x00\x00\x00\x01'
            'a\x02\x00\x04spam\x00\x01b\x02\x00\x04eggs\x00\x00\t\x07\x00\x02')
        self.assertDecoded([[1.0]], '\x0A\x00\x00\x00\x01\x0A\x00\x00\x00\x01'
            '\x00\x3F\xF0\x00\x00\x00\x00\x00\x00')

    def test_amf3(self):
        # this is horrible, it needs refactoring
        x = 1

        self.buf.write('\x11\x04\x01')
        self.buf.seek(0)

        self.assertEqual(self.decoder.readElement(), 1)

    def test_dynamic(self):
        class Foo(pyamf.ASObject):
            pass

        x = Foo()

        x.foo = 'bar'

        alias = pyamf.register_class(Foo, 'x')
        alias.exclude_attrs = ['hello']

        self.assertDecoded(x, '\x10\x00\x01x\x00\x03foo\x02\x00\x03bar\x00'
            '\x05hello\x02\x00\x05world\x00\x00\t')

    def test_classic_class(self):
        pyamf.register_class(ClassicSpam, 'spam.eggs')

        self.buf.write('\x10\x00\tspam.eggs\x00\x03foo\x02\x00\x03bar\x00\x00\t')
        self.buf.seek(0)

        foo = self.decoder.readElement()

        self.assertEqual(foo.foo, 'bar')

    def test_not_strict(self):
        self.assertFalse(self.decoder.strict)

        # write a typed object to the stream
        self.buf.write('\x10\x00\tspam.eggs\x00\x03foo\x02\x00\x03bar\x00\x00\t')
        self.buf.seek(0)

        self.assertFalse('spam.eggs' in pyamf.CLASS_CACHE)

        obj = self.decoder.readElement()

        self.assertTrue(isinstance(obj, pyamf.TypedObject))
        self.assertEqual(obj.alias, 'spam.eggs')
        self.assertEqual(obj, {'foo': 'bar'})

    def test_strict(self):
        self.decoder.strict = True

        self.assertTrue(self.decoder.strict)

        # write a typed object to the stream
        self.buf.write('\x10\x00\tspam.eggs\x00\x03foo\x02\x00\x03bar\x00\x00\t')
        self.buf.seek(0)

        self.assertFalse('spam.eggs' in pyamf.CLASS_CACHE)

        self.assertRaises(pyamf.UnknownClassAlias, self.decoder.readElement)

    def test_slots(self):
        class Person(object):
            __slots__ = ('family_name', 'given_name')

        self.buf.write('\x03\x00\x0bfamily_name\x02\x00\x03Doe\x00\n'
            'given_name\x02\x00\x04Jane\x00\x00\t')
        self.buf.seek(0)

        foo = self.decoder.readElement()

        self.assertEqual(foo.family_name, 'Doe')
        self.assertEqual(foo.given_name, 'Jane')

    def test_slots_registered(self):
        class Person(object):
            __slots__ = ('family_name', 'given_name')

        pyamf.register_class(Person, 'spam.eggs.Person')

        self.buf.write('\x10\x00\x10spam.eggs.Person\x00\x0bfamily_name\x02'
            '\x00\x03Doe\x00\ngiven_name\x02\x00\x04Jane\x00\x00\t')
        self.buf.seek(0)

        foo = self.decoder.readElement()

        self.assertTrue(isinstance(foo, Person))
        self.assertEqual(foo.family_name, 'Doe')
        self.assertEqual(foo.given_name, 'Jane')

    def test_ioerror_buffer_position(self):
        """
        Test to ensure that if an IOError is raised by `readElement` that
        the original position of the stream is restored.
        """
        bytes = pyamf.encode(u'foo', [1, 2, 3], encoding=pyamf.AMF0).getvalue()

        self.buf.write(bytes[:-1])
        self.buf.seek(0)

        self.decoder.readElement()
        self.assertEqual(self.buf.tell(), 6)

        self.assertRaises(IOError, self.decoder.readElement)
        self.assertEqual(self.buf.tell(), 6)

    def test_timezone(self):
        self.decoder.timezone_offset = datetime.timedelta(hours=-5)

        self.buf.write('\x0bBr>\xc6\xf5w\x80\x00\x00\x00')
        self.buf.seek(0)

        f = self.decoder.readElement()

        self.assertEqual(f, datetime.datetime(2009, 9, 24, 9, 23, 23))


class HelperTestCase(unittest.TestCase):
    def test_encode(self):
        buf = amf0.encode(1)

        self.assertTrue(isinstance(buf, util.BufferedByteStream))

        self.assertEqual(amf0.encode(1).getvalue(), '\x00?\xf0\x00\x00\x00\x00\x00\x00')
        self.assertEqual(amf0.encode('foo', 'bar').getvalue(), '\x02\x00\x03foo\x02\x00\x03bar')

    def test_encode_with_context(self):
        context = amf0.Context()

        obj = object()
        context.addObject(obj)
        self.assertEqual(amf0.encode(obj, context=context).getvalue(), '\x07\x00\x00')

    def test_decode(self):
        gen = amf0.decode('\x00?\xf0\x00\x00\x00\x00\x00\x00')
        self.assertTrue(isinstance(gen, types.GeneratorType))

        self.assertEqual(gen.next(), 1)
        self.assertRaises(StopIteration, gen.next)

        self.assertEqual([x for x in amf0.decode('\x02\x00\x03foo\x02\x00\x03bar')], ['foo', 'bar'])

    def test_decode_with_context(self):
        context = amf0.Context()

        obj = object()
        context.addObject(obj)
        self.assertEqual([x for x in amf0.decode('\x07\x00\x00', context=context)], [obj])


class RecordSetTestCase(unittest.TestCase):
    def test_create(self):
        x = amf0.RecordSet()

        self.assertEqual(x.columns, [])
        self.assertEqual(x.items, [])
        self.assertEqual(x.service, None)
        self.assertEqual(x.id, None)

        x = amf0.RecordSet(columns=['spam', 'eggs'], items=[[1, 2]])

        self.assertEqual(x.columns, ['spam', 'eggs'])
        self.assertEqual(x.items, [[1, 2]])
        self.assertEqual(x.service, None)
        self.assertEqual(x.id, None)

        x = amf0.RecordSet(service={}, id=54)

        self.assertEqual(x.columns, [])
        self.assertEqual(x.items, [])
        self.assertEqual(x.service, {})
        self.assertEqual(x.id, 54)

    def test_server_info(self):
        # empty recordset
        x = amf0.RecordSet()

        si = x.serverInfo

        self.assertTrue(isinstance(si, dict))
        self.assertEqual(si.cursor, 1)
        self.assertEqual(si.version, 1)
        self.assertEqual(si.columnNames, [])
        self.assertEqual(si.initialData, [])
        self.assertEqual(si.totalCount, 0)

        try:
            si.serviceName
        except AttributeError:
            pass

        try:
            si.id
        except AttributeError:
            pass

        # basic create
        x = amf0.RecordSet(columns=['a', 'b', 'c'], items=[
            [1, 2, 3], [4, 5, 6], [7, 8, 9]])

        si = x.serverInfo

        self.assertTrue(isinstance(si, dict))
        self.assertEqual(si.cursor, 1)
        self.assertEqual(si.version, 1)
        self.assertEqual(si.columnNames, ['a', 'b', 'c'])
        self.assertEqual(si.initialData, [[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        self.assertEqual(si.totalCount, 3)

        try:
            si.serviceName
        except AttributeError:
            pass

        try:
            si.id
        except AttributeError:
            pass

        # with service & id
        service = {'name': 'baz'}

        x = amf0.RecordSet(columns=['spam'], items=[['eggs']],
            service=service, id='asdfasdf')

        si = x.serverInfo

        self.assertTrue(isinstance(si, dict))
        self.assertEqual(si.cursor, 1)
        self.assertEqual(si.version, 1)
        self.assertEqual(si.columnNames, ['spam'])
        self.assertEqual(si.initialData, [['eggs']])
        self.assertEqual(si.totalCount, 1)
        self.assertEqual(si.serviceName, 'baz')
        self.assertEqual(si.id, 'asdfasdf')

    def test_encode(self):
        stream = util.BufferedByteStream()
        encoder = pyamf._get_encoder_class(pyamf.AMF0)(stream)

        x = amf0.RecordSet(columns=['a', 'b', 'c'], items=[
            [1, 2, 3], [4, 5, 6], [7, 8, 9]])

        encoder.writeElement(x)

        stream.write('\x10\x00\tRecordSet\x00\nserverInfo\x03\x00\x06cursor'
            '\x00?\xf0\x00\x00\x00\x00\x00\x00\x00\x0bcolumnNames\n\x00\x00'
            '\x00\x03\x02\x00\x01a\x02\x00\x01b\x02\x00\x01c\x00\x0binitial'
            'Data\n\x00\x00\x00\x03\n\x00\x00\x00\x03\x00?\xf0\x00\x00\x00'
            '\x00\x00\x00\x00@\x00\x00\x00\x00\x00\x00\x00\x00@\x08\x00\x00'
            '\x00\x00\x00\x00\n\x00\x00\x00\x03\x00@\x10\x00\x00\x00\x00\x00'
            '\x00\x00@\x14\x00\x00\x00\x00\x00\x00\x00@\x18\x00\x00\x00\x00'
            '\x00\x00\n\x00\x00\x00\x03\x00@\x1c\x00\x00\x00\x00\x00\x00\x00'
            '@ \x00\x00\x00\x00\x00\x00\x00@"\x00\x00\x00\x00\x00\x00\x00\x07'
            'version\x00?\xf0\x00\x00\x00\x00\x00\x00\x00\ntotalCount\x00@'
            '\x08\x00\x00\x00\x00\x00\x00\x00\x00\t\x00\x00\t')

    def test_decode(self):
        stream = util.BufferedByteStream()
        decoder = pyamf._get_decoder_class(pyamf.AMF0)(stream)

        stream.write('\x10\x00\tRecordSet\x00\n'
            'serverInfo\x08\x00\x00\x00\x00\x00\x06cursor\x00?\xf0\x00\x00\x00'
            '\x00\x00\x00\x00\x0bcolumnNames\n\x00\x00\x00\x03\x02\x00\x01a'
            '\x02\x00\x01b\x02\x00\x01c\x00\x0binitialData\n\x00\x00\x00\x03'
            '\n\x00\x00\x00\x03\x00?\xf0\x00\x00\x00\x00\x00\x00\x00@\x00\x00'
            '\x00\x00\x00\x00\x00\x00@\x08\x00\x00\x00\x00\x00\x00\n\x00\x00'
            '\x00\x03\x00@\x10\x00\x00\x00\x00\x00\x00\x00@\x14\x00\x00\x00'
            '\x00\x00\x00\x00@\x18\x00\x00\x00\x00\x00\x00\n\x00\x00\x00\x03'
            '\x00@\x1c\x00\x00\x00\x00\x00\x00\x00@ \x00\x00\x00\x00\x00\x00'
            '\x00@"\x00\x00\x00\x00\x00\x00\x00\x07version\x00?\xf0\x00\x00'
            '\x00\x00\x00\x00\x00\ntotalCount\x00@\x08\x00\x00\x00\x00\x00\x00'
            '\x00\x00\t\x00\x00\t')

        stream.seek(0, 0)
        x = decoder.readElement()

        self.assertTrue(isinstance(x, amf0.RecordSet))
        self.assertEqual(x.columns, ['a', 'b', 'c'])
        self.assertEqual(x.items, [[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        self.assertEqual(x.service, None)
        self.assertEqual(x.id, None)


class ClassInheritanceTestCase(ClassCacheClearingTestCase, EncoderMixIn):

    amf_type = pyamf.AMF0

    def setUp(self):
        # wtf
        ClassCacheClearingTestCase.setUp(self)
        EncoderMixIn.setUp(self)

    def test_simple(self):
        class A(object):
            class __amf__:
                static = ('a')


        class B(A):
            class __amf__:
                static = ('b')

        pyamf.register_class(A, 'A')
        pyamf.register_class(B, 'B')

        x = B()
        x.a = 'spam'
        x.b = 'eggs'

        self.assertEncoded(x, '\x10\x00\x01B', ('\x00\x01a\x02\x00\x04spam',
            '\x00\x01b\x02\x00\x04eggs'), '\x00\x00\t')

    def test_deep(self):
        class A(object):
            class __amf__:
                static = ('a')

        class B(A):
            class __amf__:
                static = ('b')

        class C(B):
            class __amf__:
                static = ('c')

        pyamf.register_class(A, 'A')
        pyamf.register_class(B, 'B')
        pyamf.register_class(C, 'C')

        x = C()
        x.a = 'spam'
        x.b = 'eggs'
        x.c = 'foo'

        self.assertEncoded(x, '\x10\x00\x01C', ('\x00\x01a\x02\x00\x04spam',
            '\x00\x01c\x02\x00\x03foo', '\x00\x01b\x02\x00\x04eggs'),
            '\x00\x00\t')


class ExceptionEncodingTestCase(ClassCacheClearingTestCase):
    """
    Tests for encoding exceptions.
    """

    def setUp(self):
        ClassCacheClearingTestCase.setUp(self)

        self.buffer = util.BufferedByteStream()
        self.encoder = amf0.Encoder(self.buffer)

    def test_exception(self):
        try:
            raise Exception('foo bar')
        except Exception, e:
            self.encoder.writeElement(e)

        self.assertEqual(self.buffer.getvalue(), '\x03\x00\x07message\x02'
            '\x00\x07foo bar\x00\x04name\x02\x00\tException\x00\x00\t')

    def test_user_defined(self):
        class FooBar(Exception):
            pass

        try:
            raise FooBar('foo bar')
        except Exception, e:
            self.encoder.writeElement(e)

        self.assertEqual(self.buffer.getvalue(), '\x03\x00\x07message\x02'
            '\x00\x07foo bar\x00\x04name\x02\x00\x06FooBar\x00\x00\t')

    def test_typed(self):
        class XYZ(Exception):
            pass

        pyamf.register_class(XYZ, 'foo.bar')

        try:
            raise XYZ('blarg')
        except Exception, e:
            self.encoder.writeElement(e)

        self.assertEqual(self.buffer.getvalue(), '\x10\x00\x07foo.bar\x00'
            '\x07message\x02\x00\x05blarg\x00\x04name\x02\x00\x03XYZ\x00\x00\t')
