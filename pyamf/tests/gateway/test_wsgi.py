# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.

"""
WSGI gateway tests.

@since: 0.1.0
"""

import unittest

import pyamf
from pyamf import remoting, util
from pyamf.remoting.gateway.wsgi import WSGIGateway


class WSGIServerTestCase(unittest.TestCase):
    def setUp(self):
        self.gw = WSGIGateway()
        self.executed = False

    def test_request_method(self):
        def bad_response(status, headers):
            self.executed = True
            self.assertEquals(status, '400 Bad Request')

        self.gw({'REQUEST_METHOD': 'GET'}, bad_response)
        self.assertTrue(self.executed)

        self.assertRaises(KeyError, self.gw, {'REQUEST_METHOD': 'POST'},
            lambda *args: None)

    def test_bad_request(self):
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
            self.executed = True

        self.gw(env, start_response)
        self.assertTrue(self.executed)

    def test_unknown_request(self):
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
            self.executed = True
            self.assertEquals(status, '200 OK')
            self.assertTrue(('Content-Type', 'application/x-amf') in headers)

        response = self.gw(env, start_response)
        envelope = remoting.decode(''.join(response))

        message = envelope['/1']

        self.assertEquals(message.status, remoting.STATUS_ERROR)
        body = message.body

        self.assertTrue(isinstance(body, remoting.ErrorFault))
        self.assertEquals(body.code, 'Service.ResourceNotFound')
        self.assertTrue(self.executed)

    def test_eof_decode(self):
        request = util.BufferedByteStream()

        env = {
            'REQUEST_METHOD': 'POST',
            'CONTENT_LENGTH': str(len(request)),
            'wsgi.input': request
        }

        def start_response(status, headers):
            self.executed = True
            self.assertEquals(status, '400 Bad Request')
            self.assertTrue(('Content-Type', 'text/plain') in headers)

        response = self.gw(env, start_response)

        self.assertEquals(response, ['400 Bad Request\n\nThe request body was unable to be successfully decoded.'])
        self.assertTrue(self.executed)

    def _raiseException(self, e, *args, **kwargs):
        raise e()

    def test_really_bad_decode(self):
        self.old_method = remoting.decode
        remoting.decode = lambda *args, **kwargs: self._raiseException(Exception, *args, **kwargs)

        request = util.BufferedByteStream()

        env = {
            'REQUEST_METHOD': 'POST',
            'CONTENT_LENGTH': str(len(request)),
            'wsgi.input': request
        }

        def start_response(status, headers):
            self.executed = True
            self.assertEquals(status, '500 Internal Server Error')
            self.assertTrue(('Content-Type', 'text/plain') in headers)

        try:
            response = self.gw(env, start_response)
        except:
            remoting.decode = self.old_method

            raise

        remoting.decode = self.old_method

        self.assertEquals(response, ['500 Internal Server Error\n\nAn unexpec'
            'ted error occurred whilst decoding.'])
        self.assertTrue(self.executed)

    def test_expected_exceptions_decode(self):
        self.old_method = remoting.decode

        env = {
            'REQUEST_METHOD': 'POST',
            'CONTENT_LENGTH': '0',
            'wsgi.input': util.BufferedByteStream()
        }

        try:
            for x in (KeyboardInterrupt, SystemExit):
                remoting.decode = lambda *args, **kwargs: self._raiseException(x, *args, **kwargs)
                self.assertRaises(x, self.gw, env, lambda *args: args)
        except:
            remoting.decode = self.old_method

            raise

        remoting.decode = self.old_method

    def test_expose_request(self):
        self.gw.expose_request = True
        self.executed = False

        env = remoting.Envelope(pyamf.AMF0, pyamf.ClientTypes.Flash9)
        request = remoting.Request('echo', body=['hello'])
        env['/1'] = request

        request = remoting.encode(env)

        env = {
            'REQUEST_METHOD': 'POST',
            'CONTENT_LENGTH': str(len(request)),
            'wsgi.input': request
        }

        def echo(http_request, data):
            self.assertTrue('pyamf.request' in http_request)
            request = http_request['pyamf.request']

            self.assertTrue(isinstance(request, remoting.Request))

            self.assertEquals(request.target, 'echo')
            self.assertEquals(request.body, ['hello'])
            self.executed = True

            return data

        self.gw.addService(echo)

        response = self.gw(env, lambda *args: None)

        self.assertTrue(self.executed)

    def test_timezone(self):
        import datetime

        self.executed = False

        td = datetime.timedelta(hours=-5)
        now = datetime.datetime.utcnow()

        def echo(d):
            self.assertEquals(d, now + td)
            self.executed = True

            return d

        self.gw.addService(echo)
        self.gw.timezone_offset = -18000

        msg = remoting.Envelope(amfVersion=pyamf.AMF0, clientType=0)
        msg['/1'] = remoting.Request(target='echo', body=[now])

        stream = remoting.encode(msg)

        env = {
            'REQUEST_METHOD': 'POST',
            'CONTENT_LENGTH': str(len(stream)),
            'wsgi.input': stream
        }

        response = self.gw(env, lambda *args: None)
        envelope = remoting.decode(''.join(response))
        message = envelope['/1']

        self.assertEquals(message.body, now)


def suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(WSGIServerTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
