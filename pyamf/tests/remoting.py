# -*- encoding: utf-8 -*-
#
# Copyright (c) 2007 The PyAMF Project. All rights reserved.
# 
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

"""
Test for AMF Remoting.
"""

import unittest

import pyamf
from pyamf import remoting, util

class DecoderTestCase(unittest.TestCase):
    def test_amf_version(self):
        for x in ('\x00', '\x03'):
            try:
                remoting.decode(x)
            except EOFError:
                pass

        self.failUnlessRaises(ValueError, remoting.decode, '\x01')

    def test_client_version(self):
        for x in ('\x00', '\x01', '\x03'):
            try:
                remoting.decode('\x00' + x)
            except EOFError:
                pass

    def test_null_msg(self):
        msg = remoting.decode('\x00\x00\x00\x00\x00\x00')

        self.assertEquals(msg.amfVersion, 0)
        self.assertEquals(msg.clientType, 0)
        self.assertEquals(msg.headers, {})
        self.assertEquals(msg, {})

        y = [x for x in msg]

        self.assertEquals(y, [])

    def test_simple_header(self):
        msg = remoting.decode('\x00\x00\x00\x01\x00\x04name\x00\x00\x00\x00'
            '\x05\x0a\x00\x00\x00\x00\x00\x00')

        self.assertEquals(msg.amfVersion, 0)
        self.assertEquals(msg.clientType, 0)
        self.assertEquals(len(msg.headers), 1)
        self.assertEquals('name' in msg.headers, True)
        self.assertEquals(msg.headers['name'], [])
        self.assertFalse(msg.headers.is_required('name'))
        self.assertEquals(msg, {})

        y = [x for x in msg]

        self.assertEquals(y, [])

    def test_required_header(self):
        msg = remoting.decode('\x00\x00\x00\x01\x00\x04name\x01\x00\x00\x00'
            '\x05\x0a\x00\x00\x00\x00\x00\x00')

        self.assertTrue(msg.headers.is_required('name'))

    def test_invalid_header_data_length(self):
        self.failUnlessRaises(pyamf.ParseError, remoting.decode,
            '\x00\x00\x00\x01\x00\x04name\x00\x00\x00\x00\x06\x0a\x00\x00\x00'
            '\x00\x00\x00')

    def test_multiple_headers(self):
        msg = remoting.decode('\x00\x00\x00\x02\x00\x04name\x00\x00\x00\x00'
            '\x05\x0a\x00\x00\x00\x00\x00\x03foo\x01\x00\x00\x00\x01\x05\x00'
            '\x00')

        self.assertEquals(msg.amfVersion, 0)
        self.assertEquals(msg.clientType, 0)
        self.assertEquals(len(msg.headers), 2)
        self.assertEquals('name' in msg.headers, True)
        self.assertEquals('foo' in msg.headers, True)
        self.assertEquals(msg.headers['name'], [])
        self.assertFalse(msg.headers.is_required('name'))
        self.assertEquals(msg.headers['foo'], None)
        self.assertTrue(msg.headers.is_required('foo'))
        self.assertEquals(msg, {})

        y = [x for x in msg]

        self.assertEquals(y, [])

    def test_simple_body(self):
        self.failUnlessRaises(EOFError, remoting.decode, 
            '\x00\x00\x00\x00\x00\x01')

        msg = remoting.decode('\x00\x00\x00\x00\x00\x01\x00\x09test.test\x00'
            '\x02/1\x00\x00\x00\x0f\x08\x00\x00\x00\x00\x00\x01\x61\x02\x00'
            '\x01\x61\x00\x00\x09')

        self.assertEquals(msg.amfVersion, 0)
        self.assertEquals(msg.clientType, 0)
        self.assertEquals(len(msg.headers), 0)
        self.assertEquals(len(msg), 1)
        self.assertEquals('/1' in msg, True)
        
        m = msg['/1']

        self.assertEquals(m.target, 'test.test')
        self.assertEquals(m.body, {'a': 'a'})

        y = [x for x in msg]

        self.assertEquals(len(y), 1)

        x = y[0]
        self.assertEquals(m, x)

    def test_invalid_body_data_length(self):
        self.failUnlessRaises(pyamf.ParseError, remoting.decode,
            '\x00\x00\x00\x00\x00\x01\x00\x09test.test\x00\x02/1\x00\x00\x00'
            '\x0d\x08\x00\x00\x00\x00\x00\x01\x61\x02\x00\x01\x61\x00\x00\x09')

class EncoderTestCase(unittest.TestCase):
    def test_basic(self):
        msg = remoting.Envelope(pyamf.AMF0, pyamf.ClientTypes.Flash)
        self.assertEquals(remoting.encode(msg).getvalue(), '\x00' * 6)

        msg = remoting.Envelope(pyamf.AMF3, pyamf.ClientTypes.FlashCom)
        self.assertEquals(remoting.encode(msg).getvalue(),
            '\x03\x01' + '\x00' * 4)

    def test_header(self):
        msg = remoting.Envelope(pyamf.AMF0, pyamf.ClientTypes.Flash)

        msg.headers['foo'] = (False, 'bar')
        self.assertEquals(remoting.encode(msg).getvalue(), '\x00\x00\x00\x01'
            '\x00\x03foo\x00\x00\x00\x00\x06\x02\x00\x03bar\x00\x00')

        msg = remoting.Envelope(pyamf.AMF0, pyamf.ClientTypes.Flash)

        msg.headers['foo'] = (True, ['a', 'b', 'c'])
        self.assertEquals(remoting.encode(msg).getvalue(), '\x00\x00\x00\x01'
            '\x00\x03foo\x01\x00\x00\x00\x11\n\x00\x00\x00\x03\x02\x00\x01a'
            '\x02\x00\x01b\x02\x00\x01c\x00\x00')

    def test_body(self):
        msg = remoting.Envelope(pyamf.AMF0, pyamf.ClientTypes.Flash)

        msg['/1'] = ('test.test', 0, 'hello')

        self.assertEquals(len(msg), 1)

        x = msg['/1']

        self.assertTrue(isinstance(x, remoting.Message))
        self.assertEquals(x.envelope, msg)
        self.assertEquals(x.target, 'test.test')
        self.assertEquals(x.body, 'hello')
        self.assertEquals(x.status, 0)
        self.assertEquals(x.headers, msg.headers)

        self.assertEquals(remoting.encode(msg).getvalue(), '\x00\x00\x00\x00'
            '\x00\x01\x00\x0b/1/onResult\x00\x04null\x00\x00\x00\x08\x02\x00'
            '\x05hello')

def suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(DecoderTestCase))
    suite.addTest(unittest.makeSuite(EncoderTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
