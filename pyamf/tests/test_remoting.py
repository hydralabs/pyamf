# -*- encoding: utf-8 -*-
#
# Copyright (c) 2007 The PyAMF Project. All rights reserved.
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

"""
Tests for AMF Remoting.

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import unittest

import pyamf
from pyamf import remoting, util

class DecoderTestCase(unittest.TestCase):
    """
    Tests the decoders.
    """

    def test_amf_version(self):
        for x in ('\x00', '\x03'):
            try:
                remoting.decode(x)
            except EOFError:
                pass

        self.failUnlessRaises(pyamf.DecodeError, remoting.decode, '\x10')

    def test_client_version(self):
        """
        Tests the AMF client version.
        """
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
        """
        Test header decoder.
        """
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
        remoting.decode('\x00\x00\x00\x01\x00\x04name\x00\x00\x00\x00\x06\x0a'
            '\x00\x00\x00\x00\x00\x00')

        self.failUnlessRaises(pyamf.DecodeError, remoting.decode,
            '\x00\x00\x00\x01\x00\x04name\x00\x00\x00\x00\x06\x0a\x00\x00\x00'
            '\x00\x00\x00', strict=True)

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
            '\x02/1\x00\x00\x00\x14\x0a\x00\x00\x00\x01\x08\x00\x00\x00\x00'
            '\x00\x01\x61\x02\x00\x01\x61\x00\x00\x09')

        self.assertEquals(msg.amfVersion, 0)
        self.assertEquals(msg.clientType, 0)
        self.assertEquals(len(msg.headers), 0)
        self.assertEquals(len(msg), 1)
        self.assertEquals('/1' in msg, True)

        m = msg['/1']

        self.assertEquals(m.target, 'test.test')
        self.assertEquals(m.body, [{'a': 'a'}])

        y = [x for x in msg]

        self.assertEquals(len(y), 1)

        x = y[0]
        self.assertEquals(('/1', m), x)

    def test_invalid_body_data_length(self):
        remoting.decode('\x00\x00\x00\x00\x00\x01\x00\x09test.test\x00\x02/1'
            '\x00\x00\x00\x13\x0a\x00\x00\x00\x01\x08\x00\x00\x00\x00\x00\x01'
            '\x61\x02\x00\x01\x61\x00\x00\x09')

        self.failUnlessRaises(pyamf.DecodeError, remoting.decode,
            '\x00\x00\x00\x00\x00\x01\x00\x09test.test\x00\x02/1\x00\x00\x00'
            '\x13\x0a\x00\x00\x00\x01\x08\x00\x00\x00\x00\x00\x01\x61\x02\x00'
            '\x01\x61\x00\x00\x09', strict=True)

class EncoderTestCase(unittest.TestCase):
    """
    Test the encoders.
    """
    def test_basic(self):
        """
        """
        msg = remoting.Envelope(pyamf.AMF0, pyamf.ClientTypes.Flash6)
        self.assertEquals(remoting.encode(msg).getvalue(), '\x00' * 6)

        msg = remoting.Envelope(pyamf.AMF3, pyamf.ClientTypes.FlashCom)
        self.assertEquals(remoting.encode(msg).getvalue(),
            '\x03\x01' + '\x00' * 4)

    def test_header(self):
        """
        Test encoding of header.
        """
        msg = remoting.Envelope(pyamf.AMF0, pyamf.ClientTypes.Flash6)

        msg.headers['foo'] = (False, 'bar')
        self.assertEquals(remoting.encode(msg).getvalue(),
            '\x00\x00\x00\x01\x00\x03foo\x00\x00\x00\x00\x00\n\x00\x00\x00\x02'
            '\x01\x00\x02\x00\x03bar\x00\x00')

        msg = remoting.Envelope(pyamf.AMF0, pyamf.ClientTypes.Flash6)

        msg.headers['foo'] = (True, ['a', 'b', 'c'])
        self.assertEquals(remoting.encode(msg).getvalue(),
            '\x00\x00\x00\x01\x00\x03foo\x00\x00\x00\x00\x00\n\x00\x00\x00\x02'
            '\x01\x01\n\x00\x00\x00\x03\x02\x00\x01a\x02\x00\x01b\x02\x00\x01c'
            '\x00\x00')

    def test_body(self):
        """
        Test encoding of body.
        """
        msg = remoting.Envelope(pyamf.AMF0, pyamf.ClientTypes.Flash6)

        msg['/1'] = ('test.test', 0, 'hello')

        self.assertEquals(len(msg), 1)

        x = msg['/1']

        self.assertTrue(isinstance(x, remoting.Message))
        self.assertEquals(x.envelope, msg)
        self.assertEquals(x.target, 'test.test')
        self.assertEquals(x.body, 'hello')
        self.assertEquals(x.status, 0)
        self.assertEquals(x.headers, msg.headers)

        self.assertEquals(remoting.encode(msg).getvalue(),
            '\x00\x00\x00\x00\x00\x01\x00\x0b/1/onResult\x00\x04null\x00\x00'
            '\x00\x00\x02\x00\x05hello')

    def test_strict(self):
        msg = remoting.Envelope(pyamf.AMF0, pyamf.ClientTypes.Flash6)

        msg['/1'] = ('test.test', 0, 'hello')

        self.assertEquals(remoting.encode(msg, strict=True).getvalue(),
            '\x00\x00\x00\x00\x00\x01\x00\x0b/1/onResult\x00\x04null\x00\x00'
            '\x00\x08\x02\x00\x05hello')

class RecordSetTestCase(unittest.TestCase):
    def test_create(self):
        x = remoting.RecordSet()

        self.assertEquals(x.columns, [])
        self.assertEquals(x.items, [])
        self.assertEquals(x.service, None)
        self.assertEquals(x.id, None)

        x = remoting.RecordSet(columns=['foo', 'bar'], items=[[1, 2]])

        self.assertEquals(x.columns, ['foo', 'bar'])
        self.assertEquals(x.items, [[1, 2]])
        self.assertEquals(x.service, None)
        self.assertEquals(x.id, None)

        x = remoting.RecordSet(service={}, id=54)

        self.assertEquals(x.columns, [])
        self.assertEquals(x.items, [])
        self.assertEquals(x.service, {})
        self.assertEquals(x.id, 54)

    def test_server_info(self):
        # empty recordset
        x = remoting.RecordSet()

        si = x.serverInfo

        self.assertTrue(isinstance(si, dict))
        self.assertEquals(si['cursor'], 1)
        self.assertEquals(si['version'], 1)
        self.assertEquals(si['columnNames'], [])
        self.assertEquals(si['initialData'], [])
        self.assertEquals(si['totalCount'], 0)

        try:
            si['serviceName']
        except KeyError:
            pass

        try:
            si['id']
        except KeyError:
            pass

        # basic create
        x = remoting.RecordSet(columns=['a', 'b', 'c'], items=[
            [1, 2, 3], [4, 5, 6], [7, 8, 9]])

        si = x.serverInfo

        self.assertTrue(isinstance(si, dict))
        self.assertEquals(si['cursor'], 1)
        self.assertEquals(si['version'], 1)
        self.assertEquals(si['columnNames'], ['a', 'b', 'c'])
        self.assertEquals(si['initialData'], [[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        self.assertEquals(si['totalCount'], 3)

        try:
            si['serviceName']
        except KeyError:
            pass

        try:
            si['id']
        except KeyError:
            pass

        # with service & id
        service = pyamf.Bag({'name': 'baz'})

        service.__dict__.update(name='baz')
        x = remoting.RecordSet(columns=['foo'], items=[['bar']],
            service=service, id='asdfasdf')

        si = x.serverInfo

        self.assertTrue(isinstance(si, dict))
        self.assertEquals(si['cursor'], 1)
        self.assertEquals(si['version'], 1)
        self.assertEquals(si['columnNames'], ['foo'])
        self.assertEquals(si['initialData'], [['bar']])
        self.assertEquals(si['totalCount'], 1)
        self.assertEquals(si['serviceName'], 'baz')
        self.assertEquals(si['id'], 'asdfasdf')

    def test_encode(self):
        stream = util.BufferedByteStream()
        encoder = pyamf._get_encoder_class(pyamf.AMF0)(stream)

        x = remoting.RecordSet(columns=['a', 'b', 'c'], items=[
            [1, 2, 3], [4, 5, 6], [7, 8, 9]])

        encoder.writeElement(x)

        self.assertEquals(stream.getvalue(), '\x11\x0a\x13\x13RecordSet\x15serv'
            'erInfo\t\x01\rcursor\x04\x01\x17columnNames\t\x07\x01\x06\x03a\x06'
            '\x03b\x06\x03c\x17initialData\t\x07\x01\t\x07\x01\x04\x01\x04\x02'
            '\x04\x03\t\x07\x01\x04\x04\x04\x05\x04\x06\t\x07\x01\x04\x07\x04'
            '\x08\x04\t\x0fversion\x04\x01\x15totalCount\x04\x03\x01')

        stream.truncate()

        encoder = pyamf._get_encoder_class(pyamf.AMF3)(stream)

        x = remoting.RecordSet(columns=['a', 'b', 'c'], items=[
            [1, 2, 3], [4, 5, 6], [7, 8, 9]])

        encoder.writeElement(x)

        self.assertEquals(stream.getvalue(), '\x0a\x13\x13RecordSet\x15serv'
            'erInfo\t\x01\rcursor\x04\x01\x17columnNames\t\x07\x01\x06\x03a\x06'
            '\x03b\x06\x03c\x17initialData\t\x07\x01\t\x07\x01\x04\x01\x04\x02'
            '\x04\x03\t\x07\x01\x04\x04\x04\x05\x04\x06\t\x07\x01\x04\x07\x04'
            '\x08\x04\t\x0fversion\x04\x01\x15totalCount\x04\x03\x01')

    def test_decode(self):
        stream = util.BufferedByteStream()
        decoder = pyamf._get_decoder_class(pyamf.AMF0)(stream)

        stream.write('\x11\x0a\x13\x13RecordSet\x15serverInfo\t\x01\rcursor\x04'
            '\x01\x17columnNames\t\x07\x01\x06\x03a\x06\x03b\x06\x03c\x17initia'
            'lData\t\x07\x01\t\x07\x01\x04\x01\x04\x02\x04\x03\t\x07\x01\x04'
            '\x04\x04\x05\x04\x06\t\x07\x01\x04\x07\x04\x08\x04\t\x0fversion'
            '\x04\x01\x15totalCount\x04\x03\x01')
        stream.seek(0, 0)

        x = decoder.readElement()

        self.assertTrue(isinstance(x, remoting.RecordSet))
        self.assertEquals(x.columns, ['a', 'b', 'c'])
        self.assertEquals(x.items, [[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        self.assertEquals(x.service, None)
        self.assertEquals(x.id, None)

def suite():
    """
    Add tests.
    """
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(DecoderTestCase))
    suite.addTest(unittest.makeSuite(EncoderTestCase))
    suite.addTest(unittest.makeSuite(RecordSetTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
