# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE for details.

"""
Tests for AMF utilities.

@since: 0.1.0
"""

import unittest

from datetime import datetime
from StringIO import StringIO

import pyamf
from pyamf import util

from pyamf.tests import util as _util

class TimestampTestCase(unittest.TestCase):
    """
    Test UTC timestamps.
    """

    def test_get_timestamp(self):
        self.assertEqual(util.get_timestamp(datetime(2007, 11, 12)), 1194825600)

    def test_get_datetime(self):
        self.assertEqual(util.get_datetime(1194825600), datetime(2007, 11, 12))

    def test_get_negative_datetime(self):
        self.assertEqual(util.get_datetime(-31536000), datetime(1969, 1, 1))

class StringIOProxyTestCase(unittest.TestCase):
    """
    """

    def setUp(self):
        from StringIO import StringIO

        self.previous = util.StringIOProxy._wrapped_class
        util.StringIOProxy._wrapped_class = StringIO

    def tearDown(self):
        util.StringIOProxy._wrapped_class = self.previous

    def test_create(self):
        sp = util.StringIOProxy()

        self.assertEquals(sp._buffer.tell(), 0)
        self.assertEquals(sp._buffer.getvalue(), '')
        self.assertEquals(len(sp), 0)
        self.assertEquals(sp.getvalue(), '')

        sp = util.StringIOProxy(None)

        self.assertEquals(sp._buffer.tell(), 0)
        self.assertEquals(sp._buffer.getvalue(), '')
        self.assertEquals(len(sp), 0)
        self.assertEquals(sp.getvalue(), '')

        sp = util.StringIOProxy('')

        self.assertEquals(sp._buffer.tell(), 0)
        self.assertEquals(sp._buffer.getvalue(), '')
        self.assertEquals(len(sp), 0)
        self.assertEquals(sp.getvalue(), '')

        sp = util.StringIOProxy('spam')

        self.assertEquals(sp._buffer.tell(), 0)
        self.assertEquals(sp._buffer.getvalue(), 'spam')
        self.assertEquals(len(sp), 4)
        self.assertEquals(sp.getvalue(), 'spam')

        sp = util.StringIOProxy(StringIO('this is a test'))
        self.assertEquals(sp._buffer.tell(), 0)
        self.assertEquals(sp._buffer.getvalue(), 'this is a test')
        self.assertEquals(len(sp), 14)
        self.assertEquals(sp.getvalue(), 'this is a test')

        self.assertRaises(TypeError, util.StringIOProxy, self)

    def test_close(self):
        sp = util.StringIOProxy()

        sp.close()

        self.assertEquals(len(sp), 0)
        self.assertRaises(ValueError, sp.write, 'asdfasdf')

    def test_flush(self):
        sp = util.StringIOProxy('spameggs')

        self.assertEquals(sp.getvalue(), 'spameggs')
        self.assertEquals(len(sp), 8)
        self.assertEquals(sp.tell(), 0)

        sp.flush()

        self.assertEquals(sp.getvalue(), 'spameggs')
        self.assertEquals(len(sp), 8)
        self.assertEquals(sp.tell(), 0)

    def test_getvalue(self):
        sp = util.StringIOProxy()

        sp.write('asdfasdf')
        self.assertEquals(sp.getvalue(), 'asdfasdf')
        sp.write('spam')
        self.assertEquals(sp.getvalue(), 'asdfasdfspam')

    def test_read(self):
        sp = util.StringIOProxy('this is a test')

        self.assertEquals(len(sp), 14)
        self.assertEquals(sp.read(1), 't')
        self.assertEquals(sp.getvalue(), 'this is a test')
        self.assertEquals(len(sp), 14)
        self.assertEquals(sp.read(10), 'his is a t')
        self.assertEquals(sp.read(), 'est')

    def test_readline(self):
        sp = util.StringIOProxy("this is a test\nspam and eggs")

        self.assertEquals(len(sp), 28)
        self.assertEquals(sp.getvalue(), "this is a test\nspam and eggs")
        self.assertEquals(sp.readline(), 'this is a test\n')

        self.assertEquals(len(sp), 28)
        self.assertEquals(sp.getvalue(), "this is a test\nspam and eggs")
        self.assertEquals(sp.readline(), 'spam and eggs')

    def test_readlines(self):
        sp = util.StringIOProxy("\n".join([
            "line 1",
            "line 2",
            "line 3",
            "line 4",
        ]))

        self.assertEquals(len(sp), 27)
        self.assertEquals(sp.readlines(), [
            "line 1\n",
            "line 2\n",
            "line 3\n",
            "line 4",
        ])

        self.assertEquals(len(sp), 27)
        self.assertEquals(sp.getvalue(), "\n".join([
            "line 1",
            "line 2",
            "line 3",
            "line 4",
        ]))

    def test_seek(self):
        sp = util.StringIOProxy('abcdefghijklmnopqrstuvwxyz')

        self.assertEquals(sp.getvalue(), 'abcdefghijklmnopqrstuvwxyz')
        self.assertEquals(sp.tell(), 0)

        # Relative to the beginning of the stream
        sp.seek(0, 0)
        self.assertEquals(sp.tell(), 0)
        self.assertEquals(sp.getvalue(), 'abcdefghijklmnopqrstuvwxyz')
        self.assertEquals(sp.read(1), 'a')
        self.assertEquals(len(sp), 26)

        sp.seek(10, 0)
        self.assertEquals(sp.tell(), 10)
        self.assertEquals(sp.getvalue(), 'abcdefghijklmnopqrstuvwxyz')
        self.assertEquals(sp.read(1), 'k')
        self.assertEquals(len(sp), 26)

        sp.seek(-5, 1)
        self.assertEquals(sp.tell(), 6)
        self.assertEquals(sp.getvalue(), 'abcdefghijklmnopqrstuvwxyz')
        self.assertEquals(sp.read(1), 'g')
        self.assertEquals(len(sp), 26)

        sp.seek(-3, 2)
        self.assertEquals(sp.tell(), 23)
        self.assertEquals(sp.getvalue(), 'abcdefghijklmnopqrstuvwxyz')
        self.assertEquals(sp.read(1), 'x')
        self.assertEquals(len(sp), 26)

    def test_tell(self):
        sp = util.StringIOProxy('abcdefghijklmnopqrstuvwxyz')

        self.assertEquals(sp.getvalue(), 'abcdefghijklmnopqrstuvwxyz')
        self.assertEquals(len(sp), 26)

        self.assertEquals(sp.tell(), 0)
        sp.read(1)
        self.assertEquals(sp.tell(), 1)

        self.assertEquals(sp.getvalue(), 'abcdefghijklmnopqrstuvwxyz')
        self.assertEquals(len(sp), 26)

        sp.read(5)
        self.assertEquals(sp.tell(), 6)

    def test_truncate(self):
        sp = util.StringIOProxy('abcdef')

        self.assertEquals(sp.getvalue(), 'abcdef')
        self.assertEquals(len(sp), 6)

        sp.truncate()
        self.assertEquals(sp.getvalue(), '')
        self.assertEquals(len(sp), 0)

        sp = util.StringIOProxy('hello')

        self.assertEquals(sp.getvalue(), 'hello')
        self.assertEquals(len(sp), 5)

        sp.truncate(3)

        self.assertEquals(sp.getvalue(), 'hel')
        self.assertEquals(len(sp), 3)

    def test_write(self):
        sp = util.StringIOProxy()

        self.assertEquals(sp.getvalue(), '')
        self.assertEquals(len(sp), 0)
        self.assertEquals(sp.tell(), 0)

        sp.write('hello')
        self.assertEquals(sp.getvalue(), 'hello')
        self.assertEquals(len(sp), 5)
        self.assertEquals(sp.tell(), 5)

        sp = util.StringIOProxy('xyz')

        self.assertEquals(sp.getvalue(), 'xyz')
        self.assertEquals(len(sp), 3)
        self.assertEquals(sp.tell(), 0)

        sp.write('abc')
        self.assertEquals(sp.getvalue(), 'abc')
        self.assertEquals(len(sp), 3)
        self.assertEquals(sp.tell(), 3)

    def test_writelines(self):
        lines = ["line 1", "line 2", "line 3", "line 4"]
        sp = util.StringIOProxy()

        self.assertEquals(sp.getvalue(), '')
        self.assertEquals(len(sp), 0)
        self.assertEquals(sp.tell(), 0)

        sp.writelines(lines)

        self.assertEquals(sp.getvalue(), "".join(lines))
        self.assertEquals(len(sp), 24)
        self.assertEquals(sp.tell(), 24)

    def test_len(self):
        sp = util.StringIOProxy()

        self.assertEquals(sp.getvalue(), '')
        self.assertEquals(len(sp), 0)
        self.assertEquals(sp.tell(), 0)

        sp.write('xyz')

        self.assertEquals(len(sp), 3)

        sp = util.StringIOProxy('foo')

        self.assertEquals(len(sp), 3)

        sp.seek(0, 2)
        sp.write('xyz')

        self.assertEquals(len(sp), 6)

    def test_consume(self):
        sp = util.StringIOProxy()

        self.assertEquals(sp.getvalue(), '')
        self.assertEquals(sp.tell(), 0)

        sp.consume()

        self.assertEquals(sp.getvalue(), '')
        self.assertEquals(sp.tell(), 0)

        sp = util.StringIOProxy('foobar')

        self.assertEquals(sp.getvalue(), 'foobar')
        self.assertEquals(sp.tell(), 0)

        sp.seek(3)

        self.assertEquals(sp.tell(), 3)
        sp.consume()

        self.assertEquals(sp.getvalue(), 'bar')
        self.assertEquals(sp.tell(), 0)

        # from ticket 451 - http://pyamf.org/ticket/451
        sp = util.StringIOProxy('abcdef')
        # move the stream pos to the end
        sp.read()

        self.assertEquals(len(sp), 6)
        sp.consume()
        self.assertEquals(len(sp), 0)

class cStringIOProxyTestCase(StringIOProxyTestCase):
    def setUp(self):
        from cStringIO import StringIO

        self.previous = util.StringIOProxy._wrapped_class
        util.StringIOProxy._wrapped_class = StringIO

class ByteStream(util.StringIOProxy, util.DataTypeMixIn):
    pass

class DataTypeMixInTestCase(unittest.TestCase):
    endians = (util.DataTypeMixIn.ENDIAN_BIG, util.DataTypeMixIn.ENDIAN_LITTLE)

    def _write_endian(self, obj, func, args, expected):
        old_endian = obj.endian

        for x in range(2):
            obj.truncate()
            obj.endian = self.endians[x]

            func(*args)

            self.assertEquals(obj.getvalue(), expected[x])

        obj.endian = old_endian

    def _read_endian(self, data, func, args, expected):
        for x in range(2):
            obj = ByteStream(data[x])
            obj.endian = self.endians[x]

            result = getattr(obj, func)(*args)

            self.assertEquals(result, expected)

    def test_read_uchar(self):
        x = ByteStream('\x00\xff')

        self.assertEquals(x.read_uchar(), 0)
        self.assertEquals(x.read_uchar(), 255)

    def test_write_uchar(self):
        x = ByteStream()

        x.write_uchar(0)
        self.assertEquals(x.getvalue(), '\x00')
        x.write_uchar(255)
        self.assertEquals(x.getvalue(), '\x00\xff')

        self.assertRaises(OverflowError, x.write_uchar, 256)
        self.assertRaises(OverflowError, x.write_uchar, -1)

    def test_read_char(self):
        x = ByteStream('\x00\x7f\xff\x80')

        self.assertEquals(x.read_char(), 0)
        self.assertEquals(x.read_char(), 127)
        self.assertEquals(x.read_char(), -1)
        self.assertEquals(x.read_char(), -128)

    def test_write_char(self):
        x = ByteStream()

        x.write_char(0)
        x.write_char(-128)
        x.write_char(127)

        self.assertEquals(x.getvalue(), '\x00\x80\x7f')

        self.assertRaises(OverflowError, x.write_char, 128)
        self.assertRaises(OverflowError, x.write_char, -129)

    def test_write_ushort(self):
        x = ByteStream()

        self._write_endian(x, x.write_ushort, (0,), ('\x00\x00', '\x00\x00'))
        self._write_endian(x, x.write_ushort, (12345,), ('09', '90'))
        self._write_endian(x, x.write_ushort, (65535,), ('\xff\xff', '\xff\xff'))

        self.assertRaises(OverflowError, x.write_ushort, 65536)
        self.assertRaises(OverflowError, x.write_ushort, -1)

    def test_read_ushort(self):
        self._read_endian(['\x00\x00', '\x00\x00'], 'read_ushort', (), 0)
        self._read_endian(['09', '90'], 'read_ushort', (), 12345)
        self._read_endian(['\xff\xff', '\xff\xff'], 'read_ushort', (), 65535)

    def test_write_short(self):
        x = ByteStream()

        self._write_endian(x, x.write_short, (-5673,), ('\xe9\xd7', '\xd7\xe9'))
        self._write_endian(x, x.write_short, (32767,), ('\x7f\xff', '\xff\x7f'))

        self.assertRaises(OverflowError, x.write_ushort, 65537)
        self.assertRaises(OverflowError, x.write_ushort, -1)

    def test_read_short(self):
        self._read_endian(['\xe9\xd7', '\xd7\xe9'], 'read_short', (), -5673)
        self._read_endian(['\x7f\xff', '\xff\x7f'], 'read_short', (), 32767)

    def test_write_ulong(self):
        x = ByteStream()

        self._write_endian(x, x.write_ulong, (0,), ('\x00\x00\x00\x00', '\x00\x00\x00\x00'))
        self._write_endian(x, x.write_ulong, (16810049,), ('\x01\x00\x80A', 'A\x80\x00\x01'))
        self._write_endian(x, x.write_ulong, (4294967295L,), ('\xff\xff\xff\xff', '\xff\xff\xff\xff'))

        self.assertRaises(OverflowError, x.write_ulong, 4294967296L)
        self.assertRaises(OverflowError, x.write_ulong, -1)

    def test_read_ulong(self):
        self._read_endian(['\x00\x00\x00\x00', '\x00\x00\x00\x00'], 'read_ulong', (), 0)
        self._read_endian(['\x01\x00\x80A', 'A\x80\x00\x01'], 'read_ulong', (), 16810049)
        self._read_endian(['\xff\xff\xff\xff', '\xff\xff\xff\xff'], 'read_ulong', (), 4294967295L)

    def test_write_long(self):
        x = ByteStream()

        self._write_endian(x, x.write_long, (0,), ('\x00\x00\x00\x00', '\x00\x00\x00\x00'))
        self._write_endian(x, x.write_long, (16810049,), ('\x01\x00\x80A', 'A\x80\x00\x01'))
        self._write_endian(x, x.write_long, (2147483647L,), ('\x7f\xff\xff\xff', '\xff\xff\xff\x7f'))
        self._write_endian(x, x.write_long, (-2147483648,), ('\x80\x00\x00\x00', '\x00\x00\x00\x80'))

        self.assertRaises(OverflowError, x.write_long, 2147483648)
        self.assertRaises(OverflowError, x.write_long, -2147483649)

    def test_read_long(self):
        self._read_endian(['\x00\x00\x00\x00', '\x00\x00\x00\x00'], 'read_long', (), 0)
        self._read_endian(['\x01\x00\x80A', 'A\x80\x00\x01'], 'read_long', (), 16810049)
        self._read_endian(['\x7f\xff\xff\xff', '\xff\xff\xff\x7f'], 'read_long', (), 2147483647L)

    def test_write_u24bit(self):
        x = ByteStream()

        self._write_endian(x, x.write_24bit_uint, (0,), ('\x00\x00\x00', '\x00\x00\x00'))
        self._write_endian(x, x.write_24bit_uint, (4292609,), ('A\x80\x01', '\x01\x80A'))
        self._write_endian(x, x.write_24bit_uint, (16777215,), ('\xff\xff\xff', '\xff\xff\xff'))

        self.assertRaises(OverflowError, x.write_24bit_uint, 16777216)
        self.assertRaises(OverflowError, x.write_24bit_uint, -1)

    def test_read_u24bit(self):
        self._read_endian(['\x00\x00\x00', '\x00\x00\x00'], 'read_24bit_uint', (), 0)
        self._read_endian(['\x00\x00\x80', '\x80\x00\x00'], 'read_24bit_uint', (), 128)
        self._read_endian(['\x80\x00\x00', '\x00\x00\x80'], 'read_24bit_uint', (), 8388608)
        self._read_endian(['\xff\xff\x7f', '\x7f\xff\xff'], 'read_24bit_uint', (), 16777087)
        self._read_endian(['\x7f\xff\xff', '\xff\xff\x7f'], 'read_24bit_uint', (), 8388607)

    def test_write_24bit(self):
        x = ByteStream()

        self._write_endian(x, x.write_24bit_int, (0,), ('\x00\x00\x00', '\x00\x00\x00'))
        self._write_endian(x, x.write_24bit_int, (128,), ('\x00\x00\x80', '\x80\x00\x00'))
        self._write_endian(x, x.write_24bit_int, (8388607,), ('\x7f\xff\xff', '\xff\xff\x7f'))
        self._write_endian(x, x.write_24bit_int, (-1,), ('\xff\xff\xff', '\xff\xff\xff'))
        self._write_endian(x, x.write_24bit_int, (-8388608,), ('\x80\x00\x00', '\x00\x00\x80'))

        self.assertRaises(OverflowError, x.write_24bit_int, 8388608)
        self.assertRaises(OverflowError, x.write_24bit_int, -8388609)

    def test_read_24bit(self):
        self._read_endian(['\x00\x00\x00', '\x00\x00\x00'], 'read_24bit_int', (), 0)
        self._read_endian(['\x00\x00\x80', '\x80\x00\x00'], 'read_24bit_int', (), 128)
        self._read_endian(['\x80\x00\x00', '\x00\x00\x80'], 'read_24bit_int', (), -8388608)
        self._read_endian(['\xff\xff\x7f', '\x7f\xff\xff'], 'read_24bit_int', (), -129)
        self._read_endian(['\x7f\xff\xff', '\xff\xff\x7f'], 'read_24bit_int', (), 8388607)

    def test_write_float(self):
        x = ByteStream()

        self._write_endian(x, x.write_float, (0.2,), ('>L\xcc\xcd', '\xcd\xccL>'))

    def test_read_float(self):
        self._read_endian(['?\x00\x00\x00', '\x00\x00\x00?'], 'read_float', (), 0.5)

    def test_write_double(self):
        x = ByteStream()

        self._write_endian(x, x.write_double, (0.2,), ('?\xc9\x99\x99\x99\x99\x99\x9a', '\x9a\x99\x99\x99\x99\x99\xc9?'))

    def test_read_double(self):
        self._read_endian(['?\xc9\x99\x99\x99\x99\x99\x9a', '\x9a\x99\x99\x99\x99\x99\xc9?'], 'read_double', (), 0.2)

    def test_write_utf8_string(self):
        x = ByteStream()

        self._write_endian(x, x.write_utf8_string, (u'ᚠᛇᚻ',), ['\xe1\x9a\xa0\xe1\x9b\x87\xe1\x9a\xbb'] * 2)

    def test_read_utf8_string(self):
        self._read_endian(['\xe1\x9a\xa0\xe1\x9b\x87\xe1\x9a\xbb'] * 2, 'read_utf8_string', (9,), u'ᚠᛇᚻ')

    def test_nan(self):
        x = ByteStream('\xff\xf8\x00\x00\x00\x00\x00\x00')
        self.assertTrue(_util.isNaN(x.read_double()))

        x = ByteStream('\xff\xf0\x00\x00\x00\x00\x00\x00')
        self.assertTrue(_util.isNegInf(x.read_double()))

        x = ByteStream('\x7f\xf0\x00\x00\x00\x00\x00\x00')
        self.assertTrue(_util.isPosInf(x.read_double()))

        # now test little endian
        x = ByteStream('\x00\x00\x00\x00\x00\x00\xf8\xff')
        x.endian = ByteStream.ENDIAN_LITTLE
        self.assertTrue(_util.isNaN(x.read_double()))

        x = ByteStream('\x00\x00\x00\x00\x00\x00\xf0\xff')
        x.endian = ByteStream.ENDIAN_LITTLE
        self.assertTrue(_util.isNegInf(x.read_double()))

        x = ByteStream('\x00\x00\x00\x00\x00\x00\xf0\x7f')
        x.endian = ByteStream.ENDIAN_LITTLE
        self.assertTrue(_util.isPosInf(x.read_double()))

    def test_write_infinites(self):
        nan = 1e3000000 / 1e3000000
        pos_inf = 1e3000000
        neg_inf = -1e3000000

        x = ByteStream()

        self._write_endian(x, x.write_double, (nan,), (
            '\xff\xf8\x00\x00\x00\x00\x00\x00',
            '\x00\x00\x00\x00\x00\x00\xf8\xff'
        ))

        self._write_endian(x, x.write_double, (pos_inf,), (
            '\x7f\xf0\x00\x00\x00\x00\x00\x00',
            '\x00\x00\x00\x00\x00\x00\xf0\x7f'
        ))

        self._write_endian(x, x.write_double, (neg_inf,), (
            '\xff\xf0\x00\x00\x00\x00\x00\x00',
            '\x00\x00\x00\x00\x00\x00\xf0\xff'
        ))

class BufferedByteStreamTestCase(unittest.TestCase):
    """
    Tests for L{BufferedByteStream<util.BufferedByteStream>}
    """

    def test_create(self):
        x = util.BufferedByteStream()

        self.assertEquals(x.getvalue(), '')
        self.assertEquals(x.tell(), 0)

        x = util.BufferedByteStream('abc')

        self.assertEquals(x.getvalue(), 'abc')
        self.assertEquals(x.tell(), 0)

    def test_read(self):
        x = util.BufferedByteStream()

        x.read()
        self.assertRaises(EOFError, x.read, 10)

        x.write('hello')
        x.seek(0)
        self.assertRaises(IOError, x.read, 10)

    def test_peek(self):
        x = util.BufferedByteStream('abcdefghijklmnopqrstuvwxyz')

        self.assertEquals(x.tell(), 0)

        self.assertEquals(x.peek(), 'a')
        self.assertEquals(x.peek(5), 'abcde')
        self.assertEquals(x.peek(-1), 'abcdefghijklmnopqrstuvwxyz')

    def test_eof(self):
        x = util.BufferedByteStream()

        self.assertTrue(x.at_eof())
        x.write('hello')
        x.seek(0)
        self.assertFalse(x.at_eof())
        x.seek(0, 2)
        self.assertTrue(x.at_eof())

    def test_remaining(self):
        x = util.BufferedByteStream('spameggs')

        self.assertEqual(x.tell(), 0)
        self.assertEqual(x.remaining(), 8)

        x.seek(2)
        self.assertEqual(x.tell(), 2)
        self.assertEqual(x.remaining(), 6)

    def test_add(self):
        a = util.BufferedByteStream('a')
        b = util.BufferedByteStream('b')

        c = a + b

        self.assertTrue(isinstance(c, util.BufferedByteStream))
        self.assertEquals(c.getvalue(), 'ab')
        self.assertEquals(c.tell(), 0)

    def test_add_pos(self):
        a = util.BufferedByteStream('abc')
        b = util.BufferedByteStream('def')

        a.seek(1)
        b.seek(0, 2)

        self.assertEquals(a.tell(), 1)
        self.assertEquals(b.tell(), 3)

        c = a + b

        self.assertEquals(a.tell(), 1)
        self.assertEquals(b.tell(), 3)

class DummyAlias(pyamf.ClassAlias):
    pass

class AnotherDummyAlias(pyamf.ClassAlias):
    pass

class YADummyAlias(pyamf.ClassAlias):
    pass

class ClassAliasTestCase(unittest.TestCase):
    def setUp(self):
        self.old_aliases = pyamf.ALIAS_TYPES.copy()

    def tearDown(self):
        _util.replace_dict(self.old_aliases, pyamf.ALIAS_TYPES)

    def test_simple(self):
        class A(object):
            pass

        pyamf.register_alias_type(DummyAlias, A)

        self.assertEquals(util.get_class_alias(A), DummyAlias)

    def test_nested(self):
        class A(object):
            pass

        class B(object):
            pass

        class C(object):
            pass

        pyamf.register_alias_type(DummyAlias, A, B, C)

        self.assertEquals(util.get_class_alias(B), DummyAlias)

    def test_multiple(self):
        class A(object):
            pass

        class B(object):
            pass

        class C(object):
            pass

        pyamf.register_alias_type(DummyAlias, A)
        pyamf.register_alias_type(AnotherDummyAlias, B)
        pyamf.register_alias_type(YADummyAlias, C)

        self.assertEquals(util.get_class_alias(B), AnotherDummyAlias)
        self.assertEquals(util.get_class_alias(C), YADummyAlias)
        self.assertEquals(util.get_class_alias(A), DummyAlias)

    def test_none_existant(self):
        self.assertEquals(None, util.get_class_alias(self.__class__))

    def test_subclass(self):
        class A(object):
            pass

        class B(A):
            pass

        pyamf.register_alias_type(DummyAlias, A)

        self.assertEquals(util.get_class_alias(B), DummyAlias)

class TestObject(object):
    def __init__(self):
        self.name = 'test'

class IndexedCollectionTestCase(unittest.TestCase):
    def setUp(self):
        self.collection = util.IndexedCollection()

    def test_append(self):
        max = 5
        for i in range(0, max):
            test_obj = TestObject()
            test_obj.name = i
            self.collection.append(test_obj)

        self.assertEquals(max, len(self.collection.list))
        for i in range(0, max):
            self.assertEquals(i, self.collection.list[i].name)

    def test_get_reference_to(self):
        test_obj = TestObject
        self.collection.append(test_obj)
        idx = self.collection.getReferenceTo(test_obj)
        self.assertEquals(0, idx)
        self.assertRaises(pyamf.ReferenceError, self.collection.getReferenceTo, TestObject())

    def test_get_by_reference(self):
        test_obj = TestObject
        idx = self.collection.append(test_obj)
        self.assertEquals(id(test_obj), id(self.collection.getByReference(idx)))
        idx = self.collection.getReferenceTo(test_obj)
        self.assertEquals(id(test_obj), id(self.collection.getByReference(idx)))
        self.assertRaises(TypeError, self.collection.getByReference, 'bad ref')

    def test_remove(self):
        test_obj = TestObject()
        ref = self.collection.append(test_obj)
        self.collection.remove(test_obj)
        self.assertEquals(0, len(self.collection.list))
        self.assertFalse(self.collection.dict.has_key(ref))
        self.assertRaises(pyamf.ReferenceError, self.collection.getReferenceTo, test_obj)

    def test_array(self):
        test_obj = []
        idx = self.collection.append(test_obj)
        self.assertEquals(id(test_obj), id(self.collection.getByReference(idx)))

class IndexedMapTestCase(unittest.TestCase):
    class TestObject(object):
        def __init__(self):
            self.name = 'test'

    def setUp(self):
        self.collection = util.IndexedMap()

    def test_map(self):
        test_obj = TestObject()
        test_map = TestObject()
        ref = self.collection.map(test_obj, test_map)
        self.assertEquals(test_obj, self.collection.getByReference(ref))
        self.assertEquals(test_map, self.collection.getMappedByReference(ref))
        ref = self.collection.getReferenceTo(test_obj)
        self.assertEquals(test_obj, self.collection.getByReference(ref))
        self.assertEquals(test_map, self.collection.getMappedByReference(ref))

    def test_remove(self):
        test_obj = TestObject()
        test_map = TestObject()
        self.collection.map(test_obj, test_map)
        self.collection.remove(test_obj)
        self.assertEquals(0, len(self.collection.list))
        self.assertEquals(0, len(self.collection.mapped))

class GetAttrsTestCase(unittest.TestCase):
    def test_duplicate_keys(self):
        self.assertRaises(AttributeError, util.get_attrs, {0:0, '0':1})

def suite():
    """
    Unit tests for AMF utilities.
    """
    suite = unittest.TestSuite()

    test_cases = [
        TimestampTestCase,
        StringIOProxyTestCase,
        DataTypeMixInTestCase,
        BufferedByteStreamTestCase,
        ClassAliasTestCase,
        IndexedCollectionTestCase,
        IndexedMapTestCase,
        GetAttrsTestCase
    ]

    try:
        import cStringIO
        test_cases.append(cStringIOProxyTestCase)
    except ImportError:
        pass

    for tc in test_cases:
        suite.addTest(unittest.makeSuite(tc))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
