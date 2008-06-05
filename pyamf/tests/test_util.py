# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Tests for AMF utilities.

@since: 0.1.0
"""

import unittest

from datetime import datetime
from StringIO import StringIO

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

        self.assertRaises(ValueError, x.write_uchar, 256)
        self.assertRaises(ValueError, x.write_uchar, -1)

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

        self.assertRaises(ValueError, x.write_char, 128)
        self.assertRaises(ValueError, x.write_char, -129)

    def test_write_ushort(self):
        x = ByteStream()

        self._write_endian(x, x.write_ushort, (0,), ('\x00\x00', '\x00\x00'))
        self._write_endian(x, x.write_ushort, (12345,), ('09', '90'))
        self._write_endian(x, x.write_ushort, (65535,), ('\xff\xff', '\xff\xff'))

        self.assertRaises(ValueError, x.write_ushort, 65536)
        self.assertRaises(ValueError, x.write_ushort, -1)

    def test_read_ushort(self):
        self._read_endian(['\x00\x00', '\x00\x00'], 'read_ushort', (), 0)
        self._read_endian(['09', '90'], 'read_ushort', (), 12345)
        self._read_endian(['\xff\xff', '\xff\xff'], 'read_ushort', (), 65535)

    def test_write_short(self):
        x = ByteStream()

        self._write_endian(x, x.write_short, (-5673,), ('\xe9\xd7', '\xd7\xe9'))
        self._write_endian(x, x.write_short, (32767,), ('\x7f\xff', '\xff\x7f'))

        self.assertRaises(ValueError, x.write_ushort, 65537)
        self.assertRaises(ValueError, x.write_ushort, -1)

    def test_read_short(self):
        self._read_endian(['\xe9\xd7', '\xd7\xe9'], 'read_short', (), -5673)
        self._read_endian(['\x7f\xff', '\xff\x7f'], 'read_short', (), 32767)

    def test_write_ulong(self):
        x = ByteStream()

        self._write_endian(x, x.write_ulong, (0,), ('\x00\x00\x00\x00', '\x00\x00\x00\x00'))
        self._write_endian(x, x.write_ulong, (16810049,), ('\x01\x00\x80A', 'A\x80\x00\x01'))
        self._write_endian(x, x.write_ulong, (4294967295L,), ('\xff\xff\xff\xff', '\xff\xff\xff\xff'))

        self.assertRaises(ValueError, x.write_ulong, 4294967296L)
        self.assertRaises(ValueError, x.write_ulong, -1)

    def test_read_ulong(self):
        self._read_endian(['\x00\x00\x00\x00', '\x00\x00\x00\x00'], 'read_ulong', (), 0)
        self._read_endian(['\x01\x00\x80A', 'A\x80\x00\x01'], 'read_ulong', (), 16810049)
        self._read_endian(['\xff\xff\xff\xff', '\xff\xff\xff\xff'], 'read_ulong', (), 4294967295L)

    def test_write_long(self):
        x = ByteStream()

        self._write_endian(x, x.write_long, (0,), ('\x00\x00\x00\x00', '\x00\x00\x00\x00'))
        self._write_endian(x, x.write_long, (16810049,), ('\x01\x00\x80A', 'A\x80\x00\x01'))
        self._write_endian(x, x.write_long, (2147483647L,), ('\x7f\xff\xff\xff', '\xff\xff\xff\x7f'))

        self.assertRaises(ValueError, x.write_long, 2147483648)
        self.assertRaises(ValueError, x.write_long, -2147483649)

    def test_read_long(self):
        self._read_endian(['\x00\x00\x00\x00', '\x00\x00\x00\x00'], 'read_long', (), 0)
        self._read_endian(['\x01\x00\x80A', 'A\x80\x00\x01'], 'read_long', (), 16810049)
        self._read_endian(['\x7f\xff\xff\xff', '\xff\xff\xff\x7f'], 'read_long', (), 2147483647L)

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

def suite():
    """
    Unit tests for AMF utilities.
    """
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(TimestampTestCase))
    suite.addTest(unittest.makeSuite(StringIOProxyTestCase))

    try:
        suite.addTest(unittest.makeSuite(cStringIOProxyTestCase))
    except ImportError:
        pass

    suite.addTest(unittest.makeSuite(DataTypeMixInTestCase))
    suite.addTest(unittest.makeSuite(BufferedByteStreamTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
