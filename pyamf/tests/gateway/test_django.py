# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.

"""
Django gateway tests.

@since: 0.1.0
"""

import unittest
import sys
import os

from django import http

import pyamf
from pyamf import remoting, util
from pyamf.remoting.gateway import django as _django


class HttpRequest(http.HttpRequest):
    """
    Custom C{HttpRequest} to support raw_post_data provided by
    C{django.core.handlers.*}
    """

    def __init__(self, *args, **kwargs):
        http.HttpRequest.__init__(self, *args, **kwargs)

        self.raw_post_data = ''


class DjangoGatewayTestCase(unittest.TestCase):
    def setUp(self):
        import new

        self.mod_name = '%s.%s' % (__name__, 'settings')
        sys.modules[self.mod_name] = new.module(self.mod_name)

        self.old_env = os.environ.get('DJANGO_SETTINGS_MODULE', None)

        os.environ['DJANGO_SETTINGS_MODULE'] = self.mod_name

    def tearDown(self):
        if self.old_env is not None:
            os.environ['DJANGO_SETTINGS_MODULE'] = self.old_env

        del sys.modules[self.mod_name]

    def test_settings(self):
        from django import conf

        settings_mod = sys.modules[self.mod_name]

        settings_mod.DEBUG = True
        settings_mod.AMF_TIME_OFFSET = 1000

        conf.settings = conf.Settings(self.mod_name)

        gw = _django.DjangoGateway()

        self.assertTrue(gw.debug)
        self.assertEquals(gw.timezone_offset, 1000)

    def test_request_method(self):
        gw = _django.DjangoGateway()

        http_request = HttpRequest()
        http_request.method = 'GET'

        http_response = gw(http_request)
        self.assertEquals(http_response.status_code, 405)

    def test_bad_request(self):
        gw = _django.DjangoGateway()

        request = util.BufferedByteStream()
        request.write('Bad request')
        request.seek(0, 0)

        http_request = HttpRequest()
        http_request.method = 'POST'
        http_request.raw_post_data = request.getvalue()

        http_response = gw(http_request)
        self.assertEquals(http_response.status_code, 400)

    def test_unknown_request(self):
        gw = _django.DjangoGateway()

        request = util.BufferedByteStream()
        request.write('\x00\x00\x00\x00\x00\x01\x00\x09test.test\x00'
            '\x02/1\x00\x00\x00\x14\x0a\x00\x00\x00\x01\x08\x00\x00\x00\x00'
            '\x00\x01\x61\x02\x00\x01\x61\x00\x00\x09')
        request.seek(0, 0)

        http_request = HttpRequest()
        http_request.method = 'POST'
        http_request.raw_post_data = request.getvalue()

        http_response = gw(http_request)
        envelope = remoting.decode(http_response.content)

        message = envelope['/1']

        self.assertEquals(message.status, remoting.STATUS_ERROR)
        body = message.body

        self.assertTrue(isinstance(body, remoting.ErrorFault))
        self.assertEquals(body.code, 'Service.ResourceNotFound')

    def test_expose_request(self):
        http_request = HttpRequest()
        self.executed = False

        def test(request):
            self.assertEquals(http_request, request)
            self.assertTrue(hasattr(request, 'amf_request'))
            self.executed = True

        gw = _django.DjangoGateway({'test.test': test}, expose_request=True)

        request = util.BufferedByteStream()
        request.write('\x00\x00\x00\x00\x00\x01\x00\x09test.test\x00'
            '\x02/1\x00\x00\x00\x05\x0a\x00\x00\x00\x00')
        request.seek(0, 0)

        http_request.method = 'POST'
        http_request.raw_post_data = request.getvalue()

        gw(http_request)

        self.assertTrue(self.executed)

    def _raiseException(self, e, *args, **kwargs):
        raise e()

    def test_really_bad_decode(self):
        self.old_method = remoting.decode
        remoting.decode = lambda *args, **kwargs: self._raiseException(Exception, *args, **kwargs)

        http_request = HttpRequest()
        http_request.method = 'POST'
        http_request.raw_post_data = ''

        gw = _django.DjangoGateway()

        try:
            http_response = gw(http_request)
        except:
            remoting.decode = self.old_method

            raise

        remoting.decode = self.old_method

        self.assertTrue(isinstance(http_response, http.HttpResponseServerError))
        self.assertEquals(http_response.status_code, 500)
        self.assertEquals(http_response.content, '500 Internal Server Error\n\nAn unexpected error occurred.')

    def test_expected_exceptions_decode(self):
        self.old_method = remoting.decode

        gw = _django.DjangoGateway()

        http_request = HttpRequest()
        http_request.method = 'POST'
        http_request.raw_post_data = ''

        try:
            for x in (KeyboardInterrupt, SystemExit):
                remoting.decode = lambda *args, **kwargs: self._raiseException(x, *args, **kwargs)
                self.assertRaises(x, gw, http_request)
        except:
            remoting.decode = self.old_method

            raise

        remoting.decode = self.old_method

    def test_timezone(self):
        import datetime

        http_request = HttpRequest()
        self.executed = False

        td = datetime.timedelta(hours=-5)
        now = datetime.datetime.utcnow()

        def echo(d):
            self.assertEquals(d, now + td)
            self.executed = True

            return d

        gw = _django.DjangoGateway({'test.test': echo}, timezone_offset=-18000,
            expose_request=False)

        msg = remoting.Envelope(amfVersion=pyamf.AMF0, clientType=0)
        msg['/1'] = remoting.Request(target='test.test', body=[now])

        http_request.method = 'POST'
        http_request.raw_post_data = remoting.encode(msg).getvalue()

        res = remoting.decode(gw(http_request).content)
        self.assertTrue(self.executed)

        self.assertEquals(res['/1'].body, now)


def suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(DjangoGatewayTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
