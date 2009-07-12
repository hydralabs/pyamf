# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.

"""
Tests for Remoting client.

@since: 0.1.0
"""

import unittest

import pyamf
from pyamf import remoting
from pyamf.remoting import client


class ServiceMethodProxyTestCase(unittest.TestCase):
    def test_create(self):
        x = client.ServiceMethodProxy('a', 'b')

        self.assertEquals(x.service, 'a')
        self.assertEquals(x.name, 'b')

    def test_call(self):
        tc = self

        class TestService(object):
            def __init__(self, s, args):
                self.service = s
                self.args = args

            def _call(self, service, *args):
                tc.assertTrue(self.service, service)
                tc.assertTrue(self.args, args)

        x = client.ServiceMethodProxy(None, None)
        ts = TestService(x, [1, 2, 3])
        x.service = ts

        x(1, 2, 3)

    def test_str(self):
        x = client.ServiceMethodProxy('spam', 'eggs')
        self.assertEquals(str(x), 'spam.eggs')

        x = client.ServiceMethodProxy('spam', None)
        self.assertEquals(str(x), 'spam')


class ServiceProxyTestCase(unittest.TestCase):
    def test_create(self):
        x = client.ServiceProxy('spam', 'eggs')

        self.assertEquals(x._gw, 'spam')
        self.assertEquals(x._name, 'eggs')
        self.assertEquals(x._auto_execute, True)

        x = client.ServiceProxy('hello', 'world', True)

        self.assertEquals(x._gw, 'hello')
        self.assertEquals(x._name, 'world')
        self.assertEquals(x._auto_execute, True)

        x = client.ServiceProxy(ord, chr, False)

        self.assertEquals(x._gw, ord)
        self.assertEquals(x._name, chr)
        self.assertEquals(x._auto_execute, False)

    def test_getattr(self):
        x = client.ServiceProxy(None, None)
        y = x.spam

        self.assertTrue(isinstance(y, client.ServiceMethodProxy))
        self.assertEquals(y.name, 'spam')

    def test_call(self):
        class DummyGateway(object):
            def __init__(self, tc):
                self.tc = tc

            def addRequest(self, method_proxy, *args):
                self.tc.assertEquals(method_proxy, self.method_proxy)
                self.tc.assertEquals(args, self.args)

                self.request = {'method_proxy': method_proxy, 'args': args}
                return self.request

            def execute_single(self, request):
                self.tc.assertEquals(request, self.request)

                return pyamf.ASObject(body=None)

        gw = DummyGateway(self)
        x = client.ServiceProxy(gw, 'test')
        y = x.spam

        gw.method_proxy = y
        gw.args = ()

        y()
        gw.args = (1, 2, 3)

        y(1, 2, 3)

    def test_service_call(self):
        class DummyGateway(object):
            def __init__(self, tc):
                self.tc = tc

            def addRequest(self, method_proxy, *args):
                self.tc.assertEquals(method_proxy.service, self.x)
                self.tc.assertEquals(method_proxy.name, None)

                return pyamf.ASObject(method_proxy=method_proxy, args=args)

            def execute_single(self, request):
                return pyamf.ASObject(body=None)

        gw = DummyGateway(self)
        x = client.ServiceProxy(gw, 'test')
        gw.x = x

        x()

    def test_pending_call(self):
        class DummyGateway(object):
            def __init__(self, tc):
                self.tc = tc

            def addRequest(self, method_proxy, *args):
                self.tc.assertEquals(method_proxy, self.method_proxy)
                self.tc.assertEquals(args, self.args)

                self.request = pyamf.ASObject(method_proxy=method_proxy, args=args)

                return self.request

        gw = DummyGateway(self)
        x = client.ServiceProxy(gw, 'test', False)
        y = x.eggs

        gw.method_proxy = y
        gw.args = ()

        res = y()

        self.assertEquals(id(gw.request), id(res))

    def test_str(self):
        x = client.ServiceProxy(None, 'test')

        self.assertEquals(str(x), 'test')


class RequestWrapperTestCase(unittest.TestCase):
    def test_create(self):
        x = client.RequestWrapper(1, 2, 3, 4)

        self.assertEquals(x.gw, 1)
        self.assertEquals(x.id, 2)
        self.assertEquals(x.service, 3)
        self.assertEquals(x.args, (4,))

    def test_str(self):
        x = client.RequestWrapper(None, '/1', None, None)

        self.assertEquals(str(x), '/1')

    def test_null_response(self):
        x = client.RequestWrapper(None, None, None, None)

        self.assertRaises(AttributeError, getattr, x, 'result')

    def test_set_response(self):
        x = client.RequestWrapper(None, None, None, None)

        y = pyamf.ASObject(body='spam.eggs')

        x.setResponse(y)

        self.assertEquals(x.response, y)
        self.assertEquals(x.result, 'spam.eggs')


class DummyResponse(object):
    tc = None
    closed = False

    def __init__(self, status, body, headers=()):
        self.status = status
        self.body = body
        self.headers = headers

    def getheader(self, header):
        if header in self.headers:
            return self.headers[header]

        return None

    def read(self, x=None):
        if x is None:
            return self.body

        return self.body[:x]

    def close(self):
        self.closed = True


class DummyConnection(object):
    tc = None
    expected_value = None
    expected_url = None
    expected_headers = None
    response = None

    def request(self, method, url, value, headers=None):
        self.tc.assertEquals(method, 'POST')
        self.tc.assertEquals(url, self.expected_url)
        self.tc.assertEquals(value, self.expected_value)
        self.tc.assertEquals(headers, self.expected_headers)

    def getresponse(self):
        return self.response


class RemotingServiceTestCase(unittest.TestCase):
    def test_create(self):
        self.assertRaises(TypeError, client.RemotingService)
        x = client.RemotingService('http://example.org')

        self.assertEquals(x.url, ('http', 'example.org', '', '', '', ''))

        self.assertEquals(x.connection.host, 'example.org')
        self.assertEquals(x.connection.port, 80)

        # amf version
        x = client.RemotingService('http://example.org', pyamf.AMF3)
        self.assertEquals(x.amf_version, pyamf.AMF3)

        # client type
        x = client.RemotingService('http://example.org', pyamf.AMF3,
            pyamf.ClientTypes.FlashCom)

        self.assertEquals(x.client_type, pyamf.ClientTypes.FlashCom)

    def test_schemes(self):
        x = client.RemotingService('http://example.org')
        self.assertEquals(x.connection.port, 80)

        x = client.RemotingService('https://example.org')
        self.assertEquals(x.connection.port, 443)

        self.assertRaises(ValueError, client.RemotingService,
            'ftp://example.org')

    def test_port(self):
        x = client.RemotingService('http://example.org:8080')
        self.assertEquals(x.connection.host, 'example.org')
        self.assertEquals(x.connection.port, 8080)

    def test_get_service(self):
        x = client.RemotingService('http://example.org')

        y = x.getService('spam')

        self.assertTrue(isinstance(y, client.ServiceProxy))
        self.assertEquals(y._name, 'spam')
        self.assertEquals(y._gw, x)

        self.assertRaises(TypeError, x.getService, 1)

    def test_add_request(self):
        gw = client.RemotingService('http://spameggs.net')

        self.assertEquals(gw.request_number, 1)
        self.assertEquals(gw.requests, [])
        service = gw.getService('baz')
        wrapper = gw.addRequest(service, 1, 2, 3)

        self.assertEquals(gw.requests, [wrapper])
        self.assertEquals(wrapper.gw, gw)
        self.assertEquals(gw.request_number, 2)
        self.assertEquals(wrapper.id, '/1')
        self.assertEquals(wrapper.service, service)
        self.assertEquals(wrapper.args, (1, 2, 3))

        # add 1 arg
        wrapper2 = gw.addRequest(service, None)

        self.assertEquals(gw.requests, [wrapper, wrapper2])
        self.assertEquals(wrapper2.gw, gw)
        self.assertEquals(gw.request_number, 3)
        self.assertEquals(wrapper2.id, '/2')
        self.assertEquals(wrapper2.service, service)
        self.assertEquals(wrapper2.args, (None,))

        # add no args
        wrapper3 = gw.addRequest(service)

        self.assertEquals(gw.requests, [wrapper, wrapper2, wrapper3])
        self.assertEquals(wrapper3.gw, gw)
        self.assertEquals(gw.request_number, 4)
        self.assertEquals(wrapper3.id, '/3')
        self.assertEquals(wrapper3.service, service)
        self.assertEquals(wrapper3.args, tuple())

    def test_remove_request(self):
        gw = client.RemotingService('http://spameggs.net')
        self.assertEquals(gw.requests, [])

        service = gw.getService('baz')
        wrapper = gw.addRequest(service, 1, 2, 3)
        self.assertEquals(gw.requests, [wrapper])

        gw.removeRequest(wrapper)
        self.assertEquals(gw.requests, [])

        wrapper = gw.addRequest(service, 1, 2, 3)
        self.assertEquals(gw.requests, [wrapper])

        gw.removeRequest(service, 1, 2, 3)
        self.assertEquals(gw.requests, [])

        self.assertRaises(LookupError, gw.removeRequest, service, 1, 2, 3)

    def test_get_request(self):
        gw = client.RemotingService('http://spameggs.net')

        service = gw.getService('baz')
        wrapper = gw.addRequest(service, 1, 2, 3)

        wrapper2 = gw.getRequest(str(wrapper))
        self.assertEquals(wrapper, wrapper2)

        wrapper2 = gw.getRequest('/1')
        self.assertEquals(wrapper, wrapper2)

        wrapper2 = gw.getRequest(wrapper.id)
        self.assertEquals(wrapper, wrapper2)

    def test_get_amf_request(self):
        gw = client.RemotingService('http://example.org', pyamf.AMF3,
            pyamf.ClientTypes.FlashCom)

        service = gw.getService('baz')
        method_proxy = service.gak
        wrapper = gw.addRequest(method_proxy, 1, 2, 3)

        envelope = gw.getAMFRequest([wrapper])

        self.assertEquals(envelope.amfVersion, pyamf.AMF3)
        self.assertEquals(envelope.clientType, pyamf.ClientTypes.FlashCom)
        self.assertEquals(envelope.keys(), ['/1'])

        request = envelope['/1']
        self.assertEquals(request.target, 'baz.gak')
        self.assertEquals(request.body, [1, 2, 3])

        envelope2 = gw.getAMFRequest(gw.requests)

        self.assertEquals(envelope2.amfVersion, pyamf.AMF3)
        self.assertEquals(envelope2.clientType, pyamf.ClientTypes.FlashCom)
        self.assertEquals(envelope2.keys(), ['/1'])

        request = envelope2['/1']
        self.assertEquals(request.target, 'baz.gak')
        self.assertEquals(request.body, [1, 2, 3])

    def test_execute_single(self):
        gw = client.RemotingService('http://example.org/x/y/z')
        dc = DummyConnection()
        gw.connection = dc

        dc.tc = self
        dc.expected_headers = {'Content-Type': remoting.CONTENT_TYPE,
                               'User-Agent': client.DEFAULT_USER_AGENT}

        service = gw.getService('baz', auto_execute=False)
        wrapper = service.gak()

        response = DummyResponse(200, '\x00\x00\x00\x00\x00\x01\x00\x0b/1/onRe'
            'sult\x00\x04null\x00\x00\x00\x00\x00\x02\x00\x05hello', {
            'Content-Type': 'application/x-amf', 'Content-Length': 50})
        response.tc = self

        dc.expected_url = '/x/y/z'
        dc.expected_value = '\x00\x00\x00\x00\x00\x01\x00\x07baz.gak\x00' + \
            '\x02/1\x00\x00\x00\x00\x0a\x00\x00\x00\x00'
        dc.response = response

        gw.execute_single(wrapper)
        self.assertEquals(gw.requests, [])

        wrapper = service.gak()

        response = DummyResponse(200, '\x00\x00\x00\x00\x00\x01\x00\x0b/2/onRe'
            'sult\x00\x04null\x00\x00\x00\x00\x00\x02\x00\x05hello', {
            'Content-Type': 'application/x-amf'})
        response.tc = self

        dc.expected_url = '/x/y/z'
        dc.expected_value = '\x00\x00\x00\x00\x00\x01\x00\x07baz.gak\x00' + \
            '\x02/2\x00\x00\x00\x00\n\x00\x00\x00\x00'
        dc.response = response

        gw.execute_single(wrapper)

    def test_execute(self):
        gw = client.RemotingService('http://example.org/x/y/z')
        dc = DummyConnection()
        gw.connection = dc

        dc.tc = self
        dc.expected_headers = {'Content-Type': 'application/x-amf',
                               'User-Agent': client.DEFAULT_USER_AGENT}

        baz = gw.getService('baz', auto_execute=False)
        spam = gw.getService('spam', auto_execute=False)
        wrapper = baz.gak()
        wrapper2 = spam.eggs()

        response = DummyResponse(200, '\x00\x00\x00\x00\x00\x02\x00\x0b/1/onRe'
            'sult\x00\x04null\x00\x00\x00\x00\x00\x02\x00\x05hello\x00\x0b/2/o'
            'nResult\x00\x04null\x00\x00\x00\x00\x00\x02\x00\x05hello', {
                'Content-Type': 'application/x-amf'})
        response.tc = self

        dc.expected_url = '/x/y/z'
        dc.expected_value = '\x00\x00\x00\x00\x00\x02\x00\x07baz.gak\x00\x02' + \
            '/1\x00\x00\x00\x00\n\x00\x00\x00\x00\x00\tspam.eggs\x00\x02/2' + \
            '\x00\x00\x00\x00\n\x00\x00\x00\x00'
        dc.response = response

        gw.execute()
        self.assertEquals(gw.requests, [])

    def test_get_response(self):
        gw = client.RemotingService('http://example.org/amf-gateway')
        dc = DummyConnection()
        gw.connection = dc

        response = DummyResponse(200, '\x00\x00\x00\x00\x00\x00', {
            'Content-Type': 'application/x-amf'
        })

        dc.response = response

        gw._getResponse()

        response = DummyResponse(404, '', {})
        dc.response = response

        self.assertRaises(remoting.RemotingError, gw._getResponse)

        # bad content type
        response = DummyResponse(200, '\x00\x00\x00\x00\x00\x00',
            {'Content-Type': 'text/html'})
        dc.response = response

        self.assertRaises(remoting.RemotingError, gw._getResponse)

    def test_credentials(self):
        gw = client.RemotingService('http://example.org/amf-gateway')

        self.assertFalse('Credentials' in gw.headers)
        gw.setCredentials('spam', 'eggs')
        self.assertTrue('Credentials' in gw.headers)
        self.assertEquals(gw.headers['Credentials'],
            {'userid': u'spam', 'password': u'eggs'})

        envelope = gw.getAMFRequest([])
        self.assertTrue('Credentials' in envelope.headers)

        cred = envelope.headers['Credentials']

        self.assertEquals(cred, gw.headers['Credentials'])

    def test_append_url_header(self):
        gw = client.RemotingService('http://example.org/amf-gateway')
        dc = DummyConnection()
        gw.connection = dc

        response = DummyResponse(200, '\x00\x00\x00\x01\x00\x12AppendToGatewayUrl'
            '\x01\x00\x00\x00\x00\x02\x00\x05hello\x00\x00', {
            'Content-Type': 'application/x-amf'})

        dc.response = response

        response = gw._getResponse()
        self.assertEquals(gw.original_url, 'http://example.org/amf-gatewayhello')

    def test_replace_url_header(self):
        gw = client.RemotingService('http://example.org/amf-gateway')
        dc = DummyConnection()
        gw.connection = dc

        response = DummyResponse(200, '\x00\x00\x00\x01\x00\x11ReplaceGatewayUrl'
            '\x01\x00\x00\x00\x00\x02\x00\x10http://spam.eggs\x00\x00', {
            'Content-Type': 'application/x-amf'})

        dc.response = response

        response = gw._getResponse()
        self.assertEquals(gw.original_url, 'http://spam.eggs')

    def test_close_http_response(self):
        gw = client.RemotingService('http://example.org/amf-gateway')
        dc = DummyConnection()
        gw.connection = dc
        dc.response = DummyResponse(200, '\x00\x00\x00\x01\x00\x11ReplaceGatewayUrl'
            '\x01\x00\x00\x00\x00\x02\x00\x10http://spam.eggs\x00\x00', {
            'Content-Type': 'application/x-amf'})

        gw._getResponse()
        self.assertTrue(dc.response.closed, True)

    def test_add_http_header(self):
        gw = client.RemotingService('http://example.org/amf-gateway')

        self.assertEquals(gw.http_headers, {})

        gw.addHTTPHeader('ETag', '29083457239804752309485')

        self.assertEquals(gw.http_headers, {
            'ETag': '29083457239804752309485'
        })

    def test_remove_http_header(self):
        gw = client.RemotingService('http://example.org/amf-gateway')

        gw.http_headers = {
            'Set-Cookie': 'foo-bar'
        }

        gw.removeHTTPHeader('Set-Cookie')

        self.assertEquals(gw.http_headers, {})
        self.assertRaises(KeyError, gw.removeHTTPHeader, 'foo-bar')

    def test_http_request_headers(self):
        gw = client.RemotingService('http://example.org/amf-gateway')
        dc = DummyConnection()
        gw.connection = dc
        dc.tc = self
        dc.expected_url = '/amf-gateway'
        dc.expected_value = '\x00\x00\x00\x00\x00\x00'

        gw.addHTTPHeader('ETag', '29083457239804752309485')
        dc.expected_headers = {
            'ETag': '29083457239804752309485',
            'Content-Type': 'application/x-amf',
            'User-Agent': gw.user_agent
        }

        dc.response = DummyResponse(200, '\x00\x00\x00\x01\x00\x11ReplaceGatewayUrl'
            '\x01\x00\x00\x00\x00\x02\x00\x10http://spam.eggs\x00\x00', {
            'Content-Type': 'application/x-amf'
        })

        gw.execute()
        self.assertTrue(dc.response.closed, True)

    def test_empty_content_length(self):
        gw = client.RemotingService('http://example.org/amf-gateway')
        dc = DummyConnection()
        gw.connection = dc

        http_response = DummyResponse(200, '\x00\x00\x00\x01\x00\x11ReplaceGatewayUrl'
            '\x01\x00\x00\x00\x00\x02\x00\x10http://spam.eggs\x00\x00', {
            'Content-Type': 'application/x-amf',
            'Content-Length': ''
        })

        dc.response = http_response
        gw._getResponse()

        self.assertTrue(http_response.closed)

    def test_bad_content_length(self):
        gw = client.RemotingService('http://example.org/amf-gateway')
        dc = DummyConnection()
        gw.connection = dc

        # test a really borked content-length header
        http_response = DummyResponse(200, '\x00\x00\x00\x01\x00\x11ReplaceGatewayUrl'
            '\x01\x00\x00\x00\x00\x02\x00\x10http://spam.eggs\x00\x00', {
            'Content-Type': 'application/x-amf',
            'Content-Length': 'asdfasdf'
        })

        dc.response = http_response
        self.assertRaises(ValueError, gw._getResponse)


def suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(ServiceMethodProxyTestCase))
    suite.addTest(unittest.makeSuite(ServiceProxyTestCase))
    suite.addTest(unittest.makeSuite(RequestWrapperTestCase))
    suite.addTest(unittest.makeSuite(RemotingServiceTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
