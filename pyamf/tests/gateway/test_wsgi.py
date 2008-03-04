# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
WSGI gateway tests.

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import unittest

from pyamf import remoting, util
from pyamf.remoting.gateway.wsgi import WSGIGateway

class WSGIServerTestCase(unittest.TestCase):
    def test_request_method(self):
        gw = WSGIGateway()

        def bad_response(status, headers):
            self.assertEquals(status, '400 Bad Request')

        gw({'REQUEST_METHOD': 'GET'}, bad_response)

        def start_response(status, headers):
            self.assertEquals(status, '400 Bad Request')

        self.assertRaises(KeyError, gw, {'REQUEST_METHOD': 'POST'},
            start_response)

    def test_bad_request(self):
        gw = WSGIGateway()

        request = util.BufferedByteStream()
        request.write('Bad request')
        request.seek(0, 0)

        env = {
            'REQUEST_METHOD': 'POST',
            'CONTENT_LENGTH': str(len(request)),
            'wsgi.input': request
        }

        def start_response(status, headers):
            self.assertEquals(status, '400 Bad Request')

        gw(env, start_response)

    def test_unknown_request(self):
        gw = WSGIGateway()

        request = util.BufferedByteStream()
        request.write('\x00\x00\x00\x00\x00\x01\x00\x09test.test\x00'
            '\x02/1\x00\x00\x00\x14\x0a\x00\x00\x00\x01\x08\x00\x00\x00\x00'
            '\x00\x01\x61\x02\x00\x01\x61\x00\x00\x09')
        request.seek(0, 0)

        env = {
            'REQUEST_METHOD': 'POST',
            'CONTENT_LENGTH': str(len(request)),
            'wsgi.input': request
        }

        def start_response(status, headers):
            self.assertEquals(status, '200 OK')
            self.assertTrue(('Content-Type', 'application/x-amf') in headers)

        response = gw(env, start_response)
        envelope = remoting.decode(''.join(response))

        message = envelope['/1']

        self.assertEquals(message.status, remoting.STATUS_ERROR)
        body = message.body

        self.assertTrue(isinstance(body, remoting.ErrorFault))
        self.assertEquals(body.code, 'Service.ResourceNotFound')

def suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(WSGIServerTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
