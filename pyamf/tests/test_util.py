# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Tests for AMF utilities.

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import unittest

from datetime import datetime
from StringIO import StringIO

from pyamf import util

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

        sp = util.StringIOProxy('foo')

        self.assertEquals(sp._buffer.tell(), 0)
        self.assertEquals(sp._buffer.getvalue(), 'foo')
        self.assertEquals(len(sp), 3)
        self.assertEquals(sp.getvalue(), 'foo')

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
        sp = util.StringIOProxy('foobar')

        self.assertEquals(sp.getvalue(), 'foobar')
        self.assertEquals(len(sp), 6)
        self.assertEquals(sp.tell(), 0)

        sp.flush()

        self.assertEquals(sp.getvalue(), 'foobar')
        self.assertEquals(len(sp), 6)
        self.assertEquals(sp.tell(), 0)

    def test_getvalue(self):
        sp = util.StringIOProxy()

        sp.write('asdfasdf')
        self.assertEquals(sp.getvalue(), 'asdfasdf')
        sp.write('foo')
        self.assertEquals(sp.getvalue(), 'asdfasdffoo')

    def test_read(self):
        sp = util.StringIOProxy('this is a test')

        self.assertEquals(len(sp), 14)
        self.assertEquals(sp.read(1), 't')
        self.assertEquals(sp.getvalue(), 'this is a test')
        self.assertEquals(len(sp), 14)
        self.assertEquals(sp.read(10), 'his is a t')
        self.assertEquals(sp.read(), 'est')

    def test_readline(self):
        sp = util.StringIOProxy("this is a test\nfoo and bar")

        self.assertEquals(len(sp), 26)
        self.assertEquals(sp.getvalue(), "this is a test\nfoo and bar")
        self.assertEquals(sp.readline(), 'this is a test\n')

        self.assertEquals(len(sp), 26)
        self.assertEquals(sp.getvalue(), "this is a test\nfoo and bar")
        self.assertEquals(sp.readline(), 'foo and bar')

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

class NetworkStream(util.StringIOProxy, util.NetworkIOMixIn):
    pass

class NetworkIOMixInTestCase(unittest.TestCase):
    def test_create(self):
        x = NetworkStream()

    def test_read_uchar(self):
        x = NetworkStream('abc')

        self.assertEquals(x.getvalue(), 'abc')
        self.assertEquals(x.tell(), 0)
        self.assertEquals(x.read_uchar(), ord('a'))
        self.assertEquals(x.tell(), 1)

    def test_write_uchar(self):
        x = NetworkStream()

        self.assertEquals(x.getvalue(), '')
        self.assertEquals(x.tell(), 0)

        x.write_uchar(ord('a'))
        self.assertEquals(x.getvalue(), 'a')

        self.assertRaises(ValueError, x.write_uchar, 257)
        self.assertRaises(ValueError, x.write_uchar, -1)

    def test_read_uchar(self):
        x = NetworkStream('abc')

        self.assertEquals(x.read_uchar(), ord('a'))
        self.assertEquals(x.read_uchar(), ord('b'))
        self.assertEquals(x.read_uchar(), ord('c'))
        self.assertEquals(x.tell(), 3)

        self.assertRaises(EOFError, x.read_uchar)

    def test_write_char(self):
        x = NetworkStream()

        self.assertEquals(x.getvalue(), '')
        self.assertEquals(x.tell(), 0)

        x.write_char(ord('a'))
        self.assertEquals(x.getvalue(), 'a')

        self.assertRaises(ValueError, x.write_char, 128)
        self.assertRaises(ValueError, x.write_char, -129)

    def test_read_char(self):
        x = NetworkStream('abc')

        self.assertEquals(x.read_char(), ord('a'))
        self.assertEquals(x.read_char(), ord('b'))
        self.assertEquals(x.read_char(), ord('c'))
        self.assertEquals(x.tell(), 3)

        self.assertRaises(EOFError, x.read_char)

    def test_write_ushort(self):
        x = NetworkStream()

        self.assertEquals(x.getvalue(), '')
        self.assertEquals(x.tell(), 0)

        x.write_ushort(ord('a'))
        self.assertEquals(x.getvalue(), '\x00a')

        self.assertRaises(ValueError, x.write_ushort, 65537)
        self.assertRaises(ValueError, x.write_ushort, -1)

    def test_read_ushort(self):
        x = NetworkStream('abc')

        self.assertEquals(x.read_ushort(), ord('a') << 8 | ord('b'))
        self.assertEquals(x.tell(), 2)

        self.assertRaises(EOFError, x.read_ushort)
        self.assertEquals(x.tell(), 2)

    def test_write_short(self):
        x = NetworkStream()

        self.assertEquals(x.getvalue(), '')
        self.assertEquals(x.tell(), 0)

        x.write_short(ord('a'))
        self.assertEquals(x.getvalue(), '\x00a')

        self.assertRaises(ValueError, x.write_short, 32768)
        self.assertRaises(ValueError, x.write_short, -32769)

    def test_read_short(self):
        x = NetworkStream('abc')

        self.assertEquals(x.read_short(), ord('a') << 8 | ord('b'))

        self.assertRaises(EOFError, x.read_short)

    def test_write_ulong(self):
        x = NetworkStream()

        self.assertEquals(x.getvalue(), '')
        self.assertEquals(x.tell(), 0)

        x.write_ulong(ord('a'))
        self.assertEquals(x.getvalue(), '\x00\x00\x00a')

        self.assertRaises(ValueError, x.write_ulong, 4294967296L)
        self.assertRaises(ValueError, x.write_ulong, -1)

    def test_read_ulong(self):
        x = NetworkStream('\xff\xff\xff\xff')

        self.assertEquals(x.read_ulong(), 4294967295L)
        self.assertEquals(x.tell(), 4)

        self.assertRaises(EOFError, x.read_ulong)
        self.assertEquals(x.tell(), 4)

    def test_write_long(self):
        x = NetworkStream()

        self.assertEquals(x.getvalue(), '')
        self.assertEquals(x.tell(), 0)

        x.write_long(ord('a'))
        self.assertEquals(x.getvalue(), '\x00\x00\x00a')

        self.assertRaises(ValueError, x.write_long, 2147483648)
        self.assertRaises(ValueError, x.write_long, -2147483649)

    def test_read_long(self):
        x = NetworkStream('\xff\xff\xff\xff')

        self.assertEquals(x.read_long(), -1)
        self.assertEquals(x.tell(), 4)

        self.assertRaises(EOFError, x.read_long)

    def test_write_float(self):
        x = NetworkStream()

        self.assertEquals(x.getvalue(), '')
        self.assertEquals(x.tell(), 0)

        x.write_float(0.2)
        self.assertEquals(x.getvalue(), '>L\xcc\xcd')

    def test_read_float(self):
        x = NetworkStream('>L\xcc\xcd')

        self.assertEquals(str(x.read_float())[:3], str(0.2))
        self.assertEquals(x.tell(), 4)

        self.assertRaises(EOFError, x.read_float)

    def test_write_double(self):
        x = NetworkStream()

        self.assertEquals(x.getvalue(), '')
        self.assertEquals(x.tell(), 0)

        x.write_double(0.2)
        self.assertEquals(x.getvalue(), '?\xc9\x99\x99\x99\x99\x99\x9a')

    def test_read_double(self):
        x = NetworkStream('?\xc9\x99\x99\x99\x99\x99\x9a')

        self.assertEquals(x.read_double(), 0.2)
        self.assertEquals(x.tell(), 8)

        self.assertRaises(EOFError, x.read_double)

    def test_write_utf8_string(self):
        x = NetworkStream()

        self.assertEquals(x.getvalue(), '')
        self.assertEquals(x.tell(), 0)

        x.write_utf8_string(u'ᚠᛇᚻ')
        self.assertEquals(x.getvalue(), '\xe1\x9a\xa0\xe1\x9b\x87\xe1\x9a\xbb')
        self.assertEquals(x.tell(), 9)

    def test_read_utf8_string(self):
        x = NetworkStream('\xe1\x9a\xa0\xe1\x9b\x87\xe1\x9a\xbb')

        self.assertEquals(x.read_utf8_string(9), u'ᚠᛇᚻ')

    def test_nan(self):
        import fpconst

        x = NetworkStream('\xff\xf8\x00\x00\x00\x00\x00\x00')
        self.assertTrue(fpconst.isNaN(x.read_double())) 

        x = NetworkStream('\xff\xf0\x00\x00\x00\x00\x00\x00')
        self.assertTrue(fpconst.isNegInf(x.read_double()))
 
        x = NetworkStream('\x7f\xf0\x00\x00\x00\x00\x00\x00')
        self.assertTrue(fpconst.isPosInf(x.read_double())) 

class BufferedByteStreamTestCase(unittest.TestCase):
    """
    Tests for L{util.BufferedByteStream}
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
        x = util.BufferedByteStream('foobar')

        self.assertEqual(x.tell(), 0)
        self.assertEqual(x.remaining(), 6)

        x.seek(2)
        self.assertEqual(x.tell(), 2)
        self.assertEqual(x.remaining(), 4)

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

    suite.addTest(unittest.makeSuite(NetworkIOMixInTestCase))
    suite.addTest(unittest.makeSuite(BufferedByteStreamTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
