# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Tests for AMF0 Implementation.

@since: 0.1.0
"""

import unittest, datetime, types

import pyamf
from pyamf import amf0, util
from pyamf.tests.util import EncoderTester, DecoderTester, \
    ClassCacheClearingTestCase, Spam, ClassicSpam, isNaN, isPosInf, isNegInf

class TypesTestCase(unittest.TestCase):
    """
    Tests the type mappings.
    """
    def test_types(self):
        self.assertEquals(amf0.ASTypes.NUMBER, 0x00)
        self.assertEquals(amf0.ASTypes.BOOL, 0x01)
        self.assertEquals(amf0.ASTypes.STRING, 0x02)
        self.assertEquals(amf0.ASTypes.OBJECT, 0x03)
        self.assertEquals(amf0.ASTypes.MOVIECLIP, 0x04)
        self.assertEquals(amf0.ASTypes.NULL, 0x05)
        self.assertEquals(amf0.ASTypes.UNDEFINED, 0x06)
        self.assertEquals(amf0.ASTypes.REFERENCE, 0x07)
        self.assertEquals(amf0.ASTypes.MIXEDARRAY, 0x08)
        self.assertEquals(amf0.ASTypes.OBJECTTERM, 0x09)
        self.assertEquals(amf0.ASTypes.ARRAY, 0x0a)
        self.assertEquals(amf0.ASTypes.DATE, 0x0b)
        self.assertEquals(amf0.ASTypes.LONGSTRING, 0x0c)
        self.assertEquals(amf0.ASTypes.UNSUPPORTED, 0x0d)
        self.assertEquals(amf0.ASTypes.RECORDSET, 0x0e)
        self.assertEquals(amf0.ASTypes.XML, 0x0f)
        self.assertEquals(amf0.ASTypes.TYPEDOBJECT, 0x10)
        self.assertEquals(amf0.ASTypes.AMF3, 0x11)

class ContextTestCase(unittest.TestCase):
    def test_create(self):
        c = amf0.Context()

        self.assertEquals(c.objects, [])
        self.assertEquals(len(c.objects), 0)
        self.assertEquals(c.amf3_objs, [])
        self.assertEquals(len(c.amf3_objs), 0)

    def test_copy(self):
        import copy

        orig = amf0.Context()

        orig.addObject({'spam': 'eggs'})
        orig.amf3_objs.append([1, 2, 3])

        new = copy.copy(orig)

        self.assertEquals(new.objects, [])
        self.assertEquals(len(new.objects), 0)
        self.assertEquals(new.amf3_objs, [[1, 2, 3]])
        self.assertEquals(len(new.amf3_objs), 1)

    def test_add(self):
        x = amf0.Context()
        y = [1, 2, 3]

        self.assertEquals(x.addObject(y), 0)
        self.assertTrue(y in x.objects)
        self.assertEquals(len(x.objects), 1)

    def test_clear(self):
        x = amf0.Context()
        y = [1, 2, 3]

        x.addObject(y)
        x.amf3_objs.append({})
        x.clear()

        self.assertEquals(x.objects, [])
        self.assertEquals(len(x.objects), 0)
        self.assertFalse(y in x.objects)

        self.assertEquals(x.amf3_objs, [])
        self.assertEquals(len(x.amf3_objs), 0)
        self.assertFalse({} in x.amf3_objs)

    def test_get_by_reference(self):
        x = amf0.Context()
        y = [1, 2, 3]
        z = {'spam': 'eggs'}

        x.addObject(y)
        x.addObject(z)

        self.assertEquals(x.getObject(0), y)
        self.assertEquals(x.getObject(1), z)
        self.assertRaises(pyamf.ReferenceError, x.getObject, 2)
        self.assertRaises(TypeError, x.getObject, '')
        self.assertRaises(TypeError, x.getObject, 2.2323)

    def test_get_reference(self):
        x = amf0.Context()
        y = [1, 2, 3]
        z = {'spam': 'eggs'}

        ref1 = x.addObject(y)
        ref2 = x.addObject(z)

        self.assertEquals(x.getObjectReference(y), ref1)
        self.assertEquals(x.getObjectReference(z), ref2)
        self.assertRaises(pyamf.ReferenceError, x.getObjectReference, {})

class EncoderTestCase(ClassCacheClearingTestCase):
    """
    Tests the output from the AMF0 L{Encoder<pyamf.amf0.Encoder>} class.
    """

    def setUp(self):
        ClassCacheClearingTestCase.setUp(self)

        self.buf = util.BufferedByteStream()
        self.encoder = amf0.Encoder(self.buf)
        self.context = self.encoder.context

    def _run(self, data):
        self.encoder.context.clear()

        e = EncoderTester(self.encoder, data)
        e.run(self)

    def test_number(self):
        data = [
            (0,    '\x00\x00\x00\x00\x00\x00\x00\x00\x00'),
            (0.2,  '\x00\x3f\xc9\x99\x99\x99\x99\x99\x9a'),
            (1,    '\x00\x3f\xf0\x00\x00\x00\x00\x00\x00'),
            (42,   '\x00\x40\x45\x00\x00\x00\x00\x00\x00'),
            (-123, '\x00\xc0\x5e\xc0\x00\x00\x00\x00\x00'),
            (1.23456789, '\x00\x3f\xf3\xc0\xca\x42\x83\xde\x1b')]

        # XXX nick: Should we be testing python longs here?

        self._run(data)

    def test_boolean(self):
        data = [
            (True, '\x01\x01'),
            (False, '\x01\x00')]

        self._run(data)

    def test_string(self):
        data = [
            ('', '\x02\x00\x00'),
            ('hello', '\x02\x00\x05hello'),
            # unicode taken from http://www.columbia.edu/kermit/utf8.html
            (u'ᚠᛇᚻ', '\x02\x00\t\xe1\x9a\xa0\xe1\x9b\x87\xe1\x9a\xbb')]

        self._run(data)

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
        self.assertEquals(self.buf.getvalue(), '\x02\x00\x15M\xc3\x83\xc3\x82'
            '\xc2\xb6tley Cr\xc3\x83\xc3\x82\xc2\xbce')
        self.buf.truncate()

        self.encoder.writeString(StrObject())
        self.assertEquals(self.buf.getvalue(), '\x02\x00\x15M\xc3\x83\xc3\x82'
            '\xc2\xb6tley Cr\xc3\x83\xc3\x82\xc2\xbce')
        self.buf.truncate()

        self.encoder.writeString(ReprObject())
        self.assertEquals(self.buf.getvalue(), '\x02\x00\x15M\xc3\x83\xc3\x82'
            '\xc2\xb6tley Cr\xc3\x83\xc3\x82\xc2\xbce')
        self.buf.truncate()

        self.encoder.writeString('M\xc3\x83\xc3\x82\xc2\xb6tley Cr\xc3\x83\xc3\x82\xc2\xbce')
        self.assertEquals(self.buf.getvalue(), '\x02\x00\x15M\xc3\x83\xc3\x82'
            '\xc2\xb6tley Cr\xc3\x83\xc3\x82\xc2\xbce')

    def test_null(self):
        self._run([(None, '\x05')])

    def test_undefined(self):
        self._run([(pyamf.Undefined, '\x06')])

    def test_list(self):
        data = [
            ([], '\x0a\x00\x00\x00\x00'),
            ([1, 2, 3], '\x0a\x00\x00\x00\x03\x00\x3f\xf0\x00\x00\x00\x00\x00'
                '\x00\x00\x40\x00\x00\x00\x00\x00\x00\x00\x00\x40\x08\x00\x00'
                '\x00\x00\x00\x00'),
            ((1, 2, 3), '\x0a\x00\x00\x00\x03\x00\x3f\xf0\x00\x00\x00\x00\x00'
                '\x00\x00\x40\x00\x00\x00\x00\x00\x00\x00\x00\x40\x08\x00\x00'
                '\x00\x00\x00\x00')]

        self._run(data)

    def test_longstring(self):
        self._run([('a' * 65537, '\x0c\x00\x01\x00\x01' + 'a' * 65537)])

    def test_dict(self):
        self._run([
            ({'a': 'a'}, '\x03\x00\x01a\x02\x00\x01a\x00\x00\t')])

    def test_mixed_array(self):
        self._run([
            (pyamf.MixedArray(a=1, b=2, c=3), '\x08\x00\x00\x00\x00\x00\x01a'
                '\x00?\xf0\x00\x00\x00\x00\x00\x00\x00\x01c\x00@\x08\x00\x00'
                '\x00\x00\x00\x00\x00\x01b\x00@\x00\x00\x00\x00\x00\x00\x00'
                '\x00\x00\t')])

    def test_date(self):
        import datetime

        self._run([
            (datetime.datetime(2005, 3, 18, 1, 58, 31), '\x0bBp+6!\x15\x80\x00\x00\x00'),
            (datetime.date(2003, 12, 1), '\x0bBo%\xe2\xb2\x80\x00\x00\x00\x00')])

    def test_xml(self):
        self._run([
            (util.ET.fromstring('<a><b>hello world</b></a>'), '\x0f\x00\x00'
                '\x00\x19<a><b>hello world</b></a>')])

    def test_xml_references(self):
        x = util.ET.fromstring('<a><b>hello world</b></a>')
        self._run([
            ([x, x], '\n\x00\x00\x00\x02'
                '\x0f\x00\x00\x00\x19<a><b>hello world</b></a>'
                '\x0f\x00\x00\x00\x19<a><b>hello world</b></a>')])

    def test_object(self):
        self._run([
            ({'a': 'b'}, '\x03\x00\x01a\x02\x00\x01b\x00\x00\x09')])

    def test_force_amf3(self):
        pyamf.register_class(Spam, 'spam.eggs', metadata=['amf3'])

        x = Spam()
        x.x = 'y'

        self._run([
            (x, '\x11\n\x0b\x13spam.eggs\x03x\x06\x03y\x01')])

        pyamf.unregister_class(Spam)

    def test_typed_object(self):
        pyamf.register_class(Spam, alias='org.pyamf.spam')

        x = Spam()
        x.baz = 'hello'

        self.encoder.writeElement(x)

        self.assertEquals(self.buf.getvalue(),
            '\x10\x00\x0eorg.pyamf.spam\x00\x03baz\x02\x00\x05hello\x00\x00\t')

        pyamf.unregister_class(Spam)

    def test_complex_list(self):
        self._run([
            ([[1.0]], '\x0A\x00\x00\x00\x01\x0A\x00\x00\x00\x01\x00\x3F\xF0\x00'
                '\x00\x00\x00\x00\x00')])

        self._run([
            ([['test','test','test','test']], '\x0A\x00\x00\x00\x01\x0A\x00\x00'
                '\x00\x04\x02\x00\x04\x74\x65\x73\x74\x02\x00\x04\x74\x65\x73'
                '\x74\x02\x00\x04\x74\x65\x73\x74\x02\x00\x04\x74\x65\x73\x74')
        ])

        x = {'a': 'spam', 'b': 'eggs'}
        self._run([
            ([[x, x]], '\n\x00\x00\x00\x01\n\x00\x00\x00\x02\x03\x00\x01a\x02'
                '\x00\x04spam\x00\x01b\x02\x00\x04eggs\x00\x00\t\x07\x00\x02')])

    def test_amf3(self):
        self.assertFalse(hasattr(self.context, 'amf3_context'))

        self.context.addAMF3Object(1)
        self.encoder.writeElement(1)
        self.assertEquals(self.buf.getvalue(), '\x11\x04\x01')

        self.assertTrue(hasattr(self.context, 'amf3_context'))

        self.buf.seek(0)
        self.buf.truncate()
        obj = object()
        self.context.addAMF3Object(obj)
        self.context.amf3_context.addObject(obj)

        self.encoder.writeElement(obj)

        self.assertEquals(self.buf.getvalue(), '\x11\n\x00')

    def test_anonymous(self):
        pyamf.register_class(Spam)

        x = Spam()
        x.spam = 'eggs'
        x.hello = 'world'

        self._run([
            (x, '\x03\x00\x05hello\x02\x00\x05world\x00\x04spam\x02\x00\x04eggs\x00\x00\t')])

    def test_dynamic(self):
        def attr_func(obj):
            self.assertTrue(isinstance(obj, Spam))

            return ['hello']

        x = Spam()

        x.foo = 'bar'
        x.hello = 'world'

        pyamf.register_class(Spam, attr_func=attr_func, metadata=['dynamic'])
        self._run([(x, '\x03\x00\x05hello\x02\x00\x05world\x00\x00\t')])
        pyamf.unregister_class(Spam)

        # try duplicate attributes
        pyamf.register_class(Spam, attrs=['hello'], attr_func=attr_func,
            metadata=['dynamic'])
        self._run([(x, '\x03\x00\x05hello\x02\x00\x05world\x00\x00\t')])
        pyamf.unregister_class(Spam)

        pyamf.register_class(Spam, attrs=['foo'], attr_func=attr_func,
            metadata=['dynamic'])
        self._run([(x, '\x03\x00\x03foo\x02\x00\x03bar\x00\x05hello\x02\x00'
            '\x05world\x00\x00\t')])
        pyamf.unregister_class(Spam)

        # and now typedobject
        pyamf.register_class(Spam, 'x', attr_func=attr_func,
            metadata=['dynamic'])
        self._run([(x,
            '\x10\x00\x01x\x00\x05hello\x02\x00\x05world\x00\x00\t')])
        pyamf.unregister_class(Spam)

        pyamf.register_class(Spam, 'x', attrs=['hello'], attr_func=attr_func,
            metadata=['dynamic'])
        self._run([(x,
            '\x10\x00\x01x\x00\x05hello\x02\x00\x05world\x00\x00\t')])
        pyamf.unregister_class(Spam)

        pyamf.register_class(Spam, 'x', attrs=['foo'], attr_func=attr_func,
            metadata=['dynamic'])
        self._run([(x, '\x10\x00\x01x\x00\x03foo\x02\x00\x03bar\x00\x05hello'
            '\x02\x00\x05world\x00\x00\t')])

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

        self.assertEquals(self.buf.getvalue(), '\n\x00\x00\x00\x03\x00?\xf0'
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

        self.assertEquals(self.buf.getvalue(), '\x10\x00\x10spam.eggs.Person'
            '\x00\x0bfamily_name\x02\x00\x03Doe\x00\ngiven_name\x02\x00\x04'
            'Jane\x00\x00\t')

    def test_getstate(self):
        tc = self
        tc.executed = False

        class Foo(object):
            def __getstate__(self):
                tc.executed = True
                return {'spam': 'hello', 'eggs': True}

        pyamf.register_class(Foo, 'foo')

        foo = Foo()
        self.encoder.writeElement(foo)

        self.assertEquals(self.buf.getvalue(), '\x10\x00\x03\x66\x6f\x6f\x00'
            '\x04\x65\x67\x67\x73\x01\x01\x00\x04\x73\x70\x61\x6d\x02\x00\x05'
            '\x68\x65\x6c\x6c\x6f\x00\x00\x09')
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
            '\x03\x00\x04text\x02\x00\x03bar\x00\x04tail\x05\x00\x03tag\x02\x00\x03foo\x00\x00\t')

    def test_funcs(self):
        def x():
            yield 2

        self.assertRaises(pyamf.EncodeError, self.encoder.writeElement, chr)
        self.assertRaises(pyamf.EncodeError, self.encoder.writeElement, self.assertRaises)
        self.assertRaises(pyamf.EncodeError, self.encoder.writeElement, lambda x: x)
        self.assertRaises(pyamf.EncodeError, self.encoder.writeElement, x())
        self.assertRaises(pyamf.EncodeError, self.encoder.writeElement, pyamf)
        self.assertRaises(pyamf.EncodeError, self.encoder.writeElement, ''.startswith)

class DecoderTestCase(ClassCacheClearingTestCase):
    """
    Tests the output from the AMF0 L{Decoder<pyamf.amf0.Decoder>} class.
    """
    def setUp(self):
        ClassCacheClearingTestCase.setUp(self)

        self.buf = util.BufferedByteStream()
        self.decoder = amf0.Decoder(self.buf)
        self.context = self.decoder.context

    def _run(self, data):
        self.context.clear()

        e = DecoderTester(self.decoder, data)
        e.run(self)

    def test_types(self):
        for x in amf0.ACTIONSCRIPT_TYPES:
            self.buf.write(chr(x))
            self.buf.seek(0)
            self.decoder.readType()
            self.buf.truncate()

        self.buf.write('x')
        self.buf.seek(0)
        self.assertRaises(pyamf.DecodeError, self.decoder.readType)

    def test_undefined(self):
        self._run([(pyamf.Undefined, '\x06')])

    def test_number(self):
        self._run([
            (0,    '\x00\x00\x00\x00\x00\x00\x00\x00\x00'),
            (0.2,  '\x00\x3f\xc9\x99\x99\x99\x99\x99\x9a'),
            (1,    '\x00\x3f\xf0\x00\x00\x00\x00\x00\x00'),
            (42,   '\x00\x40\x45\x00\x00\x00\x00\x00\x00'),
            (-123, '\x00\xc0\x5e\xc0\x00\x00\x00\x00\x00'),
            (1.23456789, '\x00\x3f\xf3\xc0\xca\x42\x83\xde\x1b')])

    def test_number_types(self):
        types = [
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

        for t in types:
            bytes, expected_type = t
            self.buf.truncate()
            self.buf.write(bytes)
            self.buf.seek(0)
            self.assertEquals(type(self.decoder.readElement()), expected_type)

    def test_infinites(self):
        self.buf.truncate()
        self.buf.write('\x00\xff\xf8\x00\x00\x00\x00\x00\x00')
        self.buf.seek(0)
        x = self.decoder.readElement()
        self.assertTrue(isNaN(x))

        self.buf.truncate()
        self.buf.write('\x00\xff\xf0\x00\x00\x00\x00\x00\x00')
        self.buf.seek(0)
        x = self.decoder.readElement()
        self.assertTrue(isNegInf(x))

        self.buf.truncate()
        self.buf.write('\x00\x7f\xf0\x00\x00\x00\x00\x00\x00')
        self.buf.seek(0)
        x = self.decoder.readElement()
        self.assertTrue(isPosInf(x))

    def test_boolean(self):
        self._run([
            (True, '\x01\x01'),
            (False, '\x01\x00')])

    def test_string(self):
        self._run([
            ('', '\x02\x00\x00'),
            ('hello', '\x02\x00\x05hello'),
            (u'ᚠᛇᚻ', '\x02\x00\t\xe1\x9a\xa0\xe1\x9b\x87\xe1\x9a\xbb')])

    def test_longstring(self):
        self._run([('a' * 65537, '\x0c\x00\x01\x00\x01' + 'a' * 65537)])

    def test_null(self):
        self._run([(None, '\x05')])

    def test_list(self):
        self._run([
            ([], '\x0a\x00\x00\x00\x00'),
            ([1, 2, 3], '\x0a\x00\x00\x00\x03\x00\x3f\xf0\x00\x00\x00\x00\x00'
                '\x00\x00\x40\x00\x00\x00\x00\x00\x00\x00\x00\x40\x08\x00\x00'
                '\x00\x00\x00\x00')])

    def test_dict(self):
        self._run([
            ({'a': 'a'}, '\x08\x00\x00\x00\x00\x00\x01\x61\x02\x00\x01\x61\x00'
                '\x00\x09')])

    def test_mixed_array(self):
        self._run([
            (pyamf.MixedArray(a=1, b=2, c=3), '\x08\x00\x00\x00\x00\x00\x01a'
                '\x00?\xf0\x00\x00\x00\x00\x00\x00\x00\x01c\x00@\x08\x00\x00'
                '\x00\x00\x00\x00\x00\x01b\x00@\x00\x00\x00\x00\x00\x00\x00'
                '\x00\x00\t')])

    def test_date(self):
        self._run([
            (datetime.datetime(2005, 3, 18, 1, 58, 31),
                '\x0bBp+6!\x15\x80\x00\x00\x00')])

    def test_xml(self):
        self.buf.truncate(0)
        self.buf.write('\x0f\x00\x00\x00\x19<a><b>hello world</b></a>')
        self.buf.seek(0)

        self.assertEquals(
            util.ET.tostring(util.ET.fromstring('<a><b>hello world</b></a>')),
            util.ET.tostring(self.decoder.readElement()))

    def test_xml_references(self):
        self.buf.truncate(0)
        self.buf.write('\x0f\x00\x00\x00\x19<a><b>hello world</b></a>'
            '\x07\x00\x00')
        self.buf.seek(0)

        self.assertEquals(
            util.ET.tostring(util.ET.fromstring('<a><b>hello world</b></a>')),
            util.ET.tostring(self.decoder.readElement()))

        self.assertEquals(
            util.ET.tostring(util.ET.fromstring('<a><b>hello world</b></a>')),
            util.ET.tostring(self.decoder.readElement()))

    def test_object(self):
        self._run([
            ({'a': 'b'}, '\x03\x00\x01a\x02\x00\x01b\x00\x00\x09')])

    def test_registered_class(self):
        pyamf.register_class(Spam, alias='org.pyamf.spam')

        self.buf.write('\x10\x00\x0eorg.pyamf.spam\x00\x03'
            'baz\x02\x00\x05hello\x00\x00\x09')
        self.buf.seek(0)

        obj = self.decoder.readElement()

        self.assertEquals(type(obj), Spam)

        self.assertTrue(hasattr(obj, 'baz'))
        self.assertEquals(obj.baz, 'hello')

    def test_complex_list(self):
        x = datetime.datetime(2007, 11, 3, 8, 7, 37, 437000)

        self._run([
            ([['test','test','test','test']], '\x0A\x00\x00\x00\x01\x0A\x00\x00'
                '\x00\x04\x02\x00\x04\x74\x65\x73\x74\x02\x00\x04\x74\x65\x73'
                '\x74\x02\x00\x04\x74\x65\x73\x74\x02\x00\x04\x74\x65\x73\x74')
        ])
        self._run([
            ([x], '\x0a\x00\x00\x00\x01\x0b\x42\x71\x60\x48\xcf\xed\xd0\x00'
                '\x00\x00')])
        self._run([
            ([[{u'a': u'spam', u'b': u'eggs'}, {u'a': u'spam', u'b': u'eggs'}]],
                '\n\x00\x00\x00\x01\n\x00\x00\x00\x02\x08\x00\x00\x00\x00\x00'
                '\x01a\x02\x00\x04spam\x00\x01b\x02\x00\x04eggs\x00\x00\t\x07'
                '\x00\x02')])
        self._run([
            ([[1.0]], '\x0A\x00\x00\x00\x01\x0A\x00\x00\x00\x01\x00\x3F\xF0\x00'
                '\x00\x00\x00\x00\x00')])

    def test_amf3(self):
        x = 1

        self.buf.write('\x11\x04\x01')
        self.buf.seek(0)

        self.assertFalse(hasattr(self.decoder, '_amf3_context'))
        self.assertEquals(self.decoder.readElement(), 1)
        self.assertTrue(x in self.context.amf3_objs)
        self.assertTrue(hasattr(self.context, 'amf3_context'))

    def test_dynamic(self):
        class Foo(pyamf.ASObject):
            pass

        def attr_func(obj):
            self.assertTrue(isinstance(obj, Foo))

            return ['hello']

        x = Foo()

        x.foo = 'bar'
        x.hello = 'world'

        y = Foo()
        y.hello = x.hello

        pyamf.register_class(Foo, 'x', attr_func=attr_func,
            metadata=['dynamic'])
        self._run([(y, '\x10\x00\x01x\x00\x03foo\x02\x00\x03bar\x00\x05hello'
            '\x02\x00\x05world\x00\x00\t')])
        pyamf.unregister_class(Foo)

        pyamf.register_class(Foo, 'x', attrs=['hello'], attr_func=attr_func,
            metadata=['dynamic'])
        self._run([(y, '\x10\x00\x01x\x00\x03foo\x02\x00\x03bar\x00\x05hello'
            '\x02\x00\x05world\x00\x00\t')])
        pyamf.unregister_class(Foo)

        pyamf.register_class(Foo, 'x', attrs=['foo'], attr_func=attr_func,
            metadata=['dynamic'])
        self._run([(x, '\x10\x00\x01x\x00\x03foo\x02\x00\x03bar\x00\x05hello'
            '\x02\x00\x05world\x00\x00\t')])

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

        self.buf.write('\x10\x00\x03\x66\x6f\x6f\x00\x04\x65\x67\x67\x73\x01\x01\x00\x04')
        self.buf.write('\x73\x70\x61\x6d\x02\x00\x05\x68\x65\x6c\x6c\x6f\x00\x00\x09')
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

        self.buf.write('\x10\x00\x03\x66\x6f\x6f\x00\x04\x65\x67\x67\x73\x01\x01\x00\x04')
        self.buf.write('\x73\x70\x61\x6d\x02\x00\x05\x68\x65\x6c\x6c\x6f\x00\x00\x09')
        self.buf.seek(0)

        foo = self.decoder.readElement()

        self.assertTrue(self.executed)
        self.assertTrue(isinstance(foo, Foo))
        self.assertEquals(foo.spam, 'hello')
        self.assertEquals(foo.eggs, True)

        pyamf.unregister_class(Foo)

    def test_classic_class(self):
        pyamf.register_class(ClassicSpam, 'spam.eggs')

        self.buf.write('\x10\x00\tspam.eggs\x00\x03foo\x02\x00\x03bar\x00\x00\t')
        self.buf.seek(0)

        foo = self.decoder.readElement()

        self.assertEquals(foo.foo, 'bar')

class HelperTestCase(unittest.TestCase):
    def test_encode(self):
        buf = amf0.encode(1)

        self.assertTrue(isinstance(buf, util.BufferedByteStream))

        self.assertEquals(amf0.encode(1).getvalue(), '\x00?\xf0\x00\x00\x00\x00\x00\x00')
        self.assertEquals(amf0.encode('foo', 'bar').getvalue(), '\x02\x00\x03foo\x02\x00\x03bar')

    def test_encode_with_context(self):
        context = amf0.Context()

        obj = object()
        context.addObject(obj)
        self.assertEquals(amf0.encode(obj, context=context).getvalue(), '\x07\x00\x00')

    def test_decode(self):
        gen = amf0.decode('\x00?\xf0\x00\x00\x00\x00\x00\x00')
        self.assertTrue(isinstance(gen, types.GeneratorType))

        self.assertEquals(gen.next(), 1)
        self.assertRaises(StopIteration, gen.next)

        self.assertEquals([x for x in amf0.decode('\x02\x00\x03foo\x02\x00\x03bar')], ['foo', 'bar'])

    def test_decode_with_context(self):
        context = amf0.Context()

        obj = object()
        context.addObject(obj)
        self.assertEquals([x for x in amf0.decode('\x07\x00\x00', context=context)], [obj])

class RecordSetTestCase(unittest.TestCase):
    def test_create(self):
        x = amf0.RecordSet()

        self.assertEquals(x.columns, [])
        self.assertEquals(x.items, [])
        self.assertEquals(x.service, None)
        self.assertEquals(x.id, None)

        x = amf0.RecordSet(columns=['spam', 'eggs'], items=[[1, 2]])

        self.assertEquals(x.columns, ['spam', 'eggs'])
        self.assertEquals(x.items, [[1, 2]])
        self.assertEquals(x.service, None)
        self.assertEquals(x.id, None)

        x = amf0.RecordSet(service={}, id=54)

        self.assertEquals(x.columns, [])
        self.assertEquals(x.items, [])
        self.assertEquals(x.service, {})
        self.assertEquals(x.id, 54)

    def test_server_info(self):
        # empty recordset
        x = amf0.RecordSet()

        si = x.serverInfo

        self.assertTrue(isinstance(si, dict))
        self.assertEquals(si.cursor, 1)
        self.assertEquals(si.version, 1)
        self.assertEquals(si.columnNames, [])
        self.assertEquals(si.initialData, [])
        self.assertEquals(si.totalCount, 0)

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
        self.assertEquals(si.cursor, 1)
        self.assertEquals(si.version, 1)
        self.assertEquals(si.columnNames, ['a', 'b', 'c'])
        self.assertEquals(si.initialData, [[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        self.assertEquals(si.totalCount, 3)

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
        self.assertEquals(si.cursor, 1)
        self.assertEquals(si.version, 1)
        self.assertEquals(si.columnNames, ['spam'])
        self.assertEquals(si.initialData, [['eggs']])
        self.assertEquals(si.totalCount, 1)
        self.assertEquals(si.serviceName, 'baz')
        self.assertEquals(si.id, 'asdfasdf')

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
        self.assertEquals(x.columns, ['a', 'b', 'c'])
        self.assertEquals(x.items, [[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        self.assertEquals(x.service, None)
        self.assertEquals(x.id, None)

class ClassInheritanceTestCase(ClassCacheClearingTestCase):
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
        encoder = pyamf._get_encoder_class(pyamf.AMF0)(stream)

        encoder.writeElement(x)

        self.assertEquals(stream.getvalue(), '\x10\x00\x01B\x00\x01a\x02\x00'
            '\x04spam\x00\x01b\x02\x00\x04eggs\x00\x00\t')

        pyamf.unregister_class(A)
        pyamf.unregister_class(B)

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
        encoder = pyamf._get_encoder_class(pyamf.AMF0)(stream)

        encoder.writeElement(x)

        self.assertEquals(stream.getvalue(), '\x10\x00\x01C\x00\x01a\x02\x00'
            '\x04spam\x00\x01c\x02\x00\x03foo\x00\x01b\x02\x00\x04eggs\x00'
            '\x00\t')

        pyamf.unregister_class(A)
        pyamf.unregister_class(B)
        pyamf.unregister_class(C)

def suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(TypesTestCase))
    suite.addTest(unittest.makeSuite(ContextTestCase))
    suite.addTest(unittest.makeSuite(EncoderTestCase))
    suite.addTest(unittest.makeSuite(DecoderTestCase))
    suite.addTest(unittest.makeSuite(RecordSetTestCase))
    suite.addTest(unittest.makeSuite(HelperTestCase))
    suite.addTest(unittest.makeSuite(ClassInheritanceTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
