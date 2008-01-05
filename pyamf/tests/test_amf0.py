# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Tests for AMF0 Implementation.

@author: U{Arnar Birgisson<mailto:arnarbi@gmail.com>}
@author: U{Thijs Triemstra<mailto:info@collab.nl>}
@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import unittest, datetime

import pyamf
from pyamf import amf0, util
from pyamf.tests.util import EncoderTester, DecoderTester

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

        orig.addObject({'foo': 'bar'})
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
        z = {'foo': 'bar'}

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
        z = {'foo': 'bar'}

        ref1 = x.addObject(y)
        ref2 = x.addObject(z)

        self.assertEquals(x.getObjectReference(y), ref1)
        self.assertEquals(x.getObjectReference(z), ref2)
        self.assertRaises(pyamf.ReferenceError, x.getObjectReference, {})

class EncoderTestCase(unittest.TestCase):
    """
    Tests the output from the AMF0 L{Encoder<pyamf.amf0.Encoder>} class.
    """

    def setUp(self):
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
                '\x00\x3f<?xml version=\'1.0\' encoding=\'utf8\'?>\n<a><b>'
                'hello world</b></a>')])

    def test_xml_references(self):
        x = util.ET.fromstring('<a><b>hello world</b></a>')
        self._run([
            ([x, x], '\n\x00\x00\x00\x02'
                '\x0f\x00\x00\x00?<?xml version=\'1.0\' encoding=\'utf8\'?>\n'
                '<a><b>hello world</b></a>'
                '\x0f\x00\x00\x00?<?xml version=\'1.0\' encoding=\'utf8\'?>\n'
                '<a><b>hello world</b></a>')])

    def test_unsupported(self):
        self._run([(ord, '\x0d')])

    def test_object(self):
        self._run([
            ({'a': 'b'}, '\x03\x00\x01a\x02\x00\x01b\x00\x00\x09')])

    def test_force_amf3(self):
        class Foo(object):
            pass

        pyamf.register_class(Foo, 'foo.bar', metadata=['amf3'])

        x = Foo()
        x.x = 'y'

        self._run([
            (x, '\x11\n\x13\x0ffoo.bar\x03x\x06\x03y')])

        pyamf.unregister_class(Foo)

    def test_typed_object(self):
        class Foo(object):
            pass

        pyamf.register_class(Foo, alias='com.collab.dev.pyamf.foo')

        x = Foo()
        x.baz = 'hello'

        self.encoder.writeElement(x)

        self.assertEquals(self.buf.getvalue(),
            '\x10\x00\x18\x63\x6f\x6d\x2e\x63\x6f\x6c\x6c\x61\x62\x2e\x64\x65'
            '\x76\x2e\x70\x79\x61\x6d\x66\x2e\x66\x6f\x6f\x00\x03\x62\x61\x7a'
            '\x02\x00\x05\x68\x65\x6c\x6c\x6f\x00\x00\x09')

        pyamf.unregister_class(Foo)

    def test_complex_list(self):
        self._run([
            ([[1.0]], '\x0A\x00\x00\x00\x01\x0A\x00\x00\x00\x01\x00\x3F\xF0\x00'
                '\x00\x00\x00\x00\x00')])

        self._run([
            ([['test','test','test','test']], '\x0A\x00\x00\x00\x01\x0A\x00\x00'
                '\x00\x04\x02\x00\x04\x74\x65\x73\x74\x02\x00\x04\x74\x65\x73'
                '\x74\x02\x00\x04\x74\x65\x73\x74\x02\x00\x04\x74\x65\x73\x74')
        ])

        x = {'a': 'foo', 'b': 'bar'}
        self._run([
            ([[x, x]], '\n\x00\x00\x00\x01\n\x00\x00\x00\x02\x03\x00\x01a\x02'
                '\x00\x03foo\x00\x01b\x02\x00\x03bar\x00\x00\t\x07\x00\x02')])

    def test_amf3(self):
        x = 1

        self.context.addAMF3Object(x)
        self.encoder.writeElement(x)
        self.assertEquals(self.buf.getvalue(), '\x11\x04\x01')

    def test_anonymous(self):
        class Foo(object):
            pass

        pyamf.register_class(Foo)

        x = Foo()
        x.foo = 'bar'
        x.hello = 'world'

        self._run([
            (x, '\x03\x00\x03foo\x02\x00\x03bar\x00\x05hello\x02\x00\x05wo'
                'rld\x00\x00\t')])

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

        self.assertEquals(self.buf.getvalue(), '\n\x00\x00\x00\x03\x00?\xf0'
            '\x00\x00\x00\x00\x00\x00\x00@\x00\x00\x00\x00\x00\x00\x00\x00@'
            '\x08\x00\x00\x00\x00\x00\x00')

class DecoderTestCase(unittest.TestCase):
    """
    Tests the output from the AMF0 L{Decoder<pyamf.amf0.Decoder>} class.
    """
    def setUp(self):
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
        import datetime

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
        class Foo(object):
            pass

        try:
            del pyamf.CLASS_CACHE['com.collab.dev.pyamf.foo']
        except KeyError:
            pass

        pyamf.register_class(Foo, alias='com.collab.dev.pyamf.foo')

        self.buf.write('\x10\x00\x18\x63\x6f\x6d\x2e\x63\x6f\x6c\x6c\x61\x62'
            '\x2e\x64\x65\x76\x2e\x70\x79\x61\x6d\x66\x2e\x66\x6f\x6f\x00\x03'
            '\x62\x61\x7a\x02\x00\x05\x68\x65\x6c\x6c\x6f\x00\x00\x09')
        self.buf.seek(0)

        obj = self.decoder.readElement()

        self.assertEquals(type(obj), Foo)

        self.failUnless(hasattr(obj, 'baz'))
        self.assertEquals(obj.baz, 'hello')

        del pyamf.CLASS_CACHE['com.collab.dev.pyamf.foo']

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
            ([[{u'a': u'foo', u'b': u'bar'}, {u'a': u'foo', u'b': u'bar'}]],
                '\n\x00\x00\x00\x01\n\x00\x00\x00\x02\x08\x00\x00\x00\x00\x00'
                '\x01a\x02\x00\x03foo\x00\x01b\x02\x00\x03bar\x00\x00\t\x07'
                '\x00\x02')])
        self._run([
            ([[1.0]], '\x0A\x00\x00\x00\x01\x0A\x00\x00\x00\x01\x00\x3F\xF0\x00'
                '\x00\x00\x00\x00\x00')])

    def test_amf3(self):
        x = 1

        self.buf.write('\x11\x04\x01')
        self.buf.seek(0)

        self.assertEquals(self.decoder.readElement(), 1)
        self.assertTrue(x in self.context.amf3_objs)

class HelperTestCase(unittest.TestCase):
    def test_encode(self):
        pass

class RecordSetTestCase(unittest.TestCase):
    def test_create(self):
        x = amf0.RecordSet()

        self.assertEquals(x.columns, [])
        self.assertEquals(x.items, [])
        self.assertEquals(x.service, None)
        self.assertEquals(x.id, None)

        x = amf0.RecordSet(columns=['foo', 'bar'], items=[[1, 2]])

        self.assertEquals(x.columns, ['foo', 'bar'])
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

        x = amf0.RecordSet(columns=['foo'], items=[['bar']],
            service=service, id='asdfasdf')

        si = x.serverInfo

        self.assertTrue(isinstance(si, dict))
        self.assertEquals(si.cursor, 1)
        self.assertEquals(si.version, 1)
        self.assertEquals(si.columnNames, ['foo'])
        self.assertEquals(si.initialData, [['bar']])
        self.assertEquals(si.totalCount, 1)
        self.assertEquals(si.serviceName, 'baz')
        self.assertEquals(si.id, 'asdfasdf')

    def test_encode(self):
        stream = util.BufferedByteStream()
        encoder = pyamf._get_encoder_class(pyamf.AMF0)(stream)

        x = amf0.RecordSet(columns=['a', 'b', 'c'], items=[
            [1, 2, 3], [4, 5, 6], [7, 8, 9]])

        encoder.writeElement(x)

        self.assertEquals(stream.getvalue(), '\x10\x00\tRecordSet\x00\n'
            'serverInfo\x03\x00\x06cursor\x00?\xf0\x00\x00\x00\x00\x00\x00\x00'
            '\x0bcolumnNames\n\x00\x00\x00\x03\x02\x00\x01a\x02\x00\x01b\x02'
            '\x00\x01c\x00\ntotalCount\x00@\x08\x00\x00\x00\x00\x00\x00\x00'
            '\x07version\x00?\xf0\x00\x00\x00\x00\x00\x00\x00\x0binitialData\n'
            '\x00\x00\x00\x03\n\x00\x00\x00\x03\x00?\xf0\x00\x00\x00\x00\x00'
            '\x00\x00@\x00\x00\x00\x00\x00\x00\x00\x00@\x08\x00\x00\x00\x00'
            '\x00\x00\n\x00\x00\x00\x03\x00@\x10\x00\x00\x00\x00\x00\x00\x00@'
            '\x14\x00\x00\x00\x00\x00\x00\x00@\x18\x00\x00\x00\x00\x00\x00\n'
            '\x00\x00\x00\x03\x00@\x1c\x00\x00\x00\x00\x00\x00\x00@ \x00\x00'
            '\x00\x00\x00\x00\x00@"\x00\x00\x00\x00\x00\x00\x00\x00\t\x00\x00\t')

    def test_decode(self):
        stream = util.BufferedByteStream()
        decoder = pyamf._get_decoder_class(pyamf.AMF0)(stream)

        stream.write('\x10\x00\tRecordSet\x00\nserverI'
            'nfo\x03\x00\x06cursor\x00?\xf0\x00\x00\x00\x00\x00\x00\x00\x0bcol'
            'umnNames\n\x00\x00\x00\x03\x02\x00\x01a\x02\x00\x01b\x02\x00\x01c'
            '\x00\x0binitialData\n\x00\x00\x00\x03\n\x00\x00\x00\x03\x00?\xf0'
            '\x00\x00\x00\x00\x00\x00\x00@\x00\x00\x00\x00\x00\x00\x00\x00@'
            '\x08\x00\x00\x00\x00\x00\x00\n\x00\x00\x00\x03\x00@\x10\x00\x00'
            '\x00\x00\x00\x00\x00@\x14\x00\x00\x00\x00\x00\x00\x00@\x18\x00'
            '\x00\x00\x00\x00\x00\n\x00\x00\x00\x03\x00@\x1c\x00\x00\x00\x00'
            '\x00\x00\x00@ \x00\x00\x00\x00\x00\x00\x00@"\x00\x00\x00\x00\x00'
            '\x00\x00\x07version\x00?\xf0\x00\x00\x00\x00\x00\x00\x00\ntotalCo'
            'unt\x00@\x08\x00\x00\x00\x00\x00\x00\x00\x00\t\x00\x00\t')
        stream.seek(0, 0)

        x = decoder.readElement()

        self.assertTrue(isinstance(x, amf0.RecordSet))
        self.assertEquals(x.columns, ['a', 'b', 'c'])
        self.assertEquals(x.items, [[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        self.assertEquals(x.service, None)
        self.assertEquals(x.id, None)

def suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(TypesTestCase))
    suite.addTest(unittest.makeSuite(ContextTestCase))
    suite.addTest(unittest.makeSuite(EncoderTestCase))
    suite.addTest(unittest.makeSuite(DecoderTestCase))
    suite.addTest(unittest.makeSuite(RecordSetTestCase))
    suite.addTest(unittest.makeSuite(HelperTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
