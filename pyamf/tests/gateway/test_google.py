# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.

"""
Google Web App gateway tests.

@since: 0.3.1
"""

import unittest

from StringIO import StringIO

from google.appengine.ext import webapp

import pyamf
from pyamf import remoting
from pyamf.remoting.gateway import google as _google


class WebAppGatewayTestCase(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)

        self.gw = _google.WebAppGateway()

        self.environ = {
            'wsgi.input': StringIO(),
            'wsgi.output': StringIO()
        }

        self.request = webapp.Request(self.environ)
        self.response = webapp.Response()

        self.gw.initialize(self.request, self.response)

    def test_get(self):
        self.gw.get()

        self.assertEquals(self.response.__dict__['_Response__status'][0], 405)

    def test_bad_request(self):
        self.environ['wsgi.input'].write('Bad request')
        self.environ['wsgi.input'].seek(0, 0)

        self.gw.post()
        self.assertEquals(self.response.__dict__['_Response__status'][0], 400)

    def test_unknown_request(self):
        self.environ['wsgi.input'].write(
            '\x00\x00\x00\x00\x00\x01\x00\x09test.test\x00\x02/1\x00\x00\x00'
            '\x14\x0a\x00\x00\x00\x01\x08\x00\x00\x00\x00\x00\x01\x61\x02\x00'
            '\x01\x61\x00\x00\x09')
        self.environ['wsgi.input'].seek(0, 0)

        self.gw.post()

        self.assertEquals(self.response.__dict__['_Response__status'][0], 200)

        envelope = remoting.decode(self.response.out.getvalue())
        message = envelope['/1']

        self.assertEquals(message.status, remoting.STATUS_ERROR)
        body = message.body

        self.assertTrue(isinstance(body, remoting.ErrorFault))
        self.assertEquals(body.code, 'Service.ResourceNotFound')

    def test_expose_request(self):
        self.executed = False

        def test(request):
            self.assertEquals(self.request, request)
            self.assertTrue(hasattr(self.request, 'amf_request'))

            self.executed = True

        self.gw.expose_request = True
        self.gw.addService(test, 'test.test')

        self.environ['wsgi.input'].write('\x00\x00\x00\x00\x00\x01\x00\x09'
            'test.test\x00\x02/1\x00\x00\x00\x05\x0a\x00\x00\x00\x00')
        self.environ['wsgi.input'].seek(0, 0)

        self.gw.post()

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
        self.environ['wsgi.input'] = stream
        self.gw.post()

        envelope = remoting.decode(self.response.out.getvalue())
        message = envelope['/1']

        self.assertEquals(message.body, now)
        self.assertTrue(self.executed)


def suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(WebAppGatewayTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
