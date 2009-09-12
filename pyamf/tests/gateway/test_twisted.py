# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.

"""
Twisted gateway tests.

@since: 0.1.0
"""

from twisted.internet import reactor, defer
from twisted.python import failure
from twisted.web import http, server, client, error, resource
from twisted.trial import unittest

import pyamf
from pyamf import remoting
from pyamf.remoting import gateway
from pyamf.flex import messaging
from pyamf.remoting.gateway import twisted as _twisted


class TestService(object):
    def spam(self):
        return 'spam'

    def echo(self, x):
        return x


class TwistedServerTestCase(unittest.TestCase):
    def setUp(self):
        self.gw = _twisted.TwistedGateway(expose_request=False)
        root = resource.Resource()
        root.putChild('', self.gw)

        self.p = reactor.listenTCP(0, server.Site(root), interface="127.0.0.1")
        self.port = self.p.getHost().port

    def tearDown(self):
        self.p.stopListening()

    def test_invalid_method(self):
        """
        A classic GET on the xml server should return a NOT_ALLOWED.
        """
        d = client.getPage("http://127.0.0.1:%d/" % (self.port,))
        d = self.assertFailure(d, error.Error)
        d.addCallback(
            lambda exc: self.assertEquals(int(exc.args[0]), http.NOT_ALLOWED))

        return d

    def test_bad_content(self):
        d = client.getPage("http://127.0.0.1:%d/" % (self.port,),
                method="POST", postdata="spamandeggs")
        d = self.assertFailure(d, error.Error)
        d.addCallback(
            lambda exc: self.assertEquals(int(exc.args[0]), http.BAD_REQUEST))

        return d

    def test_process_request(self):
        def echo(data):
            return data

        self.gw.addService(echo)

        env = remoting.Envelope(pyamf.AMF0, pyamf.ClientTypes.Flash9)
        request = remoting.Request('echo', body=['hello'])
        env['/1'] = request

        d = client.getPage("http://127.0.0.1:%d/" % (self.port,),
                method="POST", postdata=remoting.encode(env).getvalue())

        def cb(result):
            response = remoting.decode(result)

            self.assertEquals(response.amfVersion, pyamf.AMF0)
            self.assertEquals(response.clientType, pyamf.ClientTypes.Flash9)

            self.assertTrue('/1' in response)
            body_response = response['/1']

            self.assertEquals(body_response.status, remoting.STATUS_OK)
            self.assertEquals(body_response.body, 'hello')

        return d.addCallback(cb)

    def test_deferred_service(self):
        def echo(data):
            x = defer.Deferred()
            reactor.callLater(0, x.callback, data)

            return x

        self.gw.addService(echo)

        env = remoting.Envelope(pyamf.AMF0, pyamf.ClientTypes.Flash9)
        request = remoting.Request('echo', body=['hello'])
        env['/1'] = request

        d = client.getPage("http://127.0.0.1:%d/" % (self.port,),
                method="POST", postdata=remoting.encode(env).getvalue())

        def cb(result):
            response = remoting.decode(result)

            self.assertEquals(response.amfVersion, pyamf.AMF0)
            self.assertEquals(response.clientType, pyamf.ClientTypes.Flash9)

            self.assertTrue('/1' in response)
            body_response = response['/1']

            self.assertEquals(body_response.status, remoting.STATUS_OK)
            self.assertEquals(body_response.body, 'hello')

        return d.addCallback(cb)

    def test_unknown_request(self):
        env = remoting.Envelope(pyamf.AMF0, pyamf.ClientTypes.Flash9)
        request = remoting.Request('echo', body=['hello'])
        env['/1'] = request

        d = client.getPage("http://127.0.0.1:%d/" % (self.port,),
                method="POST", postdata=remoting.encode(env).getvalue())

        def cb(result):
            response = remoting.decode(result)

            message = response['/1']

            self.assertEquals(message.status, remoting.STATUS_ERROR)
            body = message.body

            self.assertTrue(isinstance(body, remoting.ErrorFault))
            self.assertEquals(body.code, 'Service.ResourceNotFound')

        return d.addCallback(cb)

    def test_expose_request(self):
        self.gw.expose_request = True
        self.executed = False

        env = remoting.Envelope(pyamf.AMF0, pyamf.ClientTypes.Flash9)
        request = remoting.Request('echo', body=['hello'])
        env['/1'] = request

        def echo(http_request, data):
            self.assertTrue(isinstance(http_request, http.Request))

            self.assertTrue(hasattr(http_request, 'amf_request'))
            amf_request = http_request.amf_request

            self.assertEquals(request.target, 'echo')
            self.assertEquals(request.body, ['hello'])
            self.executed = True

            return data

        self.gw.addService(echo)

        d = client.getPage("http://127.0.0.1:%d/" % (self.port,),
                method="POST", postdata=remoting.encode(env).getvalue())

        return d.addCallback(lambda x: self.assertTrue(self.executed))

    def test_preprocessor(self):
        d = defer.Deferred()

        def pp(sr):
            self.assertIdentical(sr, self.service_request)
            d.callback(None)

        gw = _twisted.TwistedGateway({'echo': lambda x: x}, preprocessor=pp)
        self.service_request = gateway.ServiceRequest(None, gw.services['echo'], None)

        gw.preprocessRequest(self.service_request)

        return d

    def test_exposed_preprocessor(self):
        d = defer.Deferred()

        def pp(hr, sr):
            self.assertEquals(hr, 'hello')
            self.assertIdentical(sr, self.service_request)
            d.callback(None)

        pp = gateway.expose_request(pp)

        gw = _twisted.TwistedGateway({'echo': lambda x: x}, preprocessor=pp)
        self.service_request = gateway.ServiceRequest(None, gw.services['echo'], None)

        gw.preprocessRequest(self.service_request, http_request='hello')

        return d

    def test_exposed_preprocessor_no_request(self):
        d = defer.Deferred()

        def pp(hr, sr):
            self.assertEquals(hr, None)
            self.assertIdentical(sr, self.service_request)
            d.callback(None)

        pp = gateway.expose_request(pp)

        gw = _twisted.TwistedGateway({'echo': lambda x: x}, preprocessor=pp)
        self.service_request = gateway.ServiceRequest(None, gw.services['echo'], None)

        gw.preprocessRequest(self.service_request)

        return d

    def test_authenticate(self):
        d = defer.Deferred()

        def auth(u, p):
            try:
                self.assertEquals(u, 'u')
                self.assertEquals(p, 'p')
            except:
                d.errback(failure.Failure())
            else:
                d.callback(None)

        gw = _twisted.TwistedGateway({'echo': lambda x: x}, authenticator=auth)
        self.service_request = gateway.ServiceRequest(None, gw.services['echo'], None)

        gw.authenticateRequest(self.service_request, 'u', 'p')

        return d

    def test_exposed_authenticate(self):
        d = defer.Deferred()

        def auth(request, u, p):
            try:
                self.assertEquals(request, 'foo')
                self.assertEquals(u, 'u')
                self.assertEquals(p, 'p')
            except:
                d.errback(failure.Failure())
            else:
                d.callback(None)

        auth = gateway.expose_request(auth)

        gw = _twisted.TwistedGateway({'echo': lambda x: x}, authenticator=auth)
        self.service_request = gateway.ServiceRequest(None, gw.services['echo'], None)

        gw.authenticateRequest(self.service_request, 'u', 'p', http_request='foo')

        return d

    def test_encoding_error(self):
        encode = _twisted.remoting.encode

        def force_error(amf_request, context=None):
            raise pyamf.EncodeError

        def echo(request, data):
            return data

        self.gw.addService(echo)

        env = remoting.Envelope(pyamf.AMF0, pyamf.ClientTypes.Flash9)
        request = remoting.Request('echo', body=['hello'])
        env['/1'] = request

        d = client.getPage("http://127.0.0.1:%d/" % (self.port,),
                method="POST", postdata=remoting.encode(env).getvalue())

        _twisted.remoting.encode = force_error
        def switch(x):
            _twisted.remoting.encode = encode

        d = self.assertFailure(d, error.Error)

        def check(exc):
            self.assertEquals(int(exc.args[0]), http.INTERNAL_SERVER_ERROR)
            self.assertTrue(exc.args[1].startswith('500 Internal Server Error'))

        d.addCallback(check)

        return d.addBoth(switch)

    def test_tuple(self):
        def echo(data):
            return data

        self.gw.addService(echo)

        env = remoting.Envelope(pyamf.AMF0, pyamf.ClientTypes.Flash9)
        request = remoting.Request('echo', body=[('Hi', 'Mom')])
        env['/1'] = request

        d = client.getPage("http://127.0.0.1:%d/" % (self.port,),
                method="POST", postdata=remoting.encode(env).getvalue())

        def cb(result):
            response = remoting.decode(result)
            body_response = response['/1']

            self.assertEquals(body_response.status, remoting.STATUS_OK)
            self.assertEquals(body_response.body, ['Hi', 'Mom'])

        return d.addCallback(cb)

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

        d = client.getPage("http://127.0.0.1:%d/" % (self.port,),
                method="POST", postdata=stream.getvalue())

        def cb(response):
            envelope = remoting.decode(''.join(response))
            message = envelope['/1']

            self.assertEquals(message.status, remoting.STATUS_OK)
            self.assertEquals(message.body, now)

        return d.addCallback(cb)

    def test_double_encode(self):
        """
        See ticket #648
        """
        self.counter = 0

        def service():
            self.counter += 1

        self.gw.addService(service)

        env = remoting.Envelope(pyamf.AMF0, pyamf.ClientTypes.Flash9)
        request = remoting.Request('service')
        env['/1'] = request

        d = client.getPage("http://127.0.0.1:%d/" % (self.port,),
                method="POST", postdata=remoting.encode(env).getvalue())

        def cb(result):
            self.assertEquals(self.counter, 1)

        return d.addCallback(cb)


class DummyHTTPRequest:
    def __init__(self):
        self.headers = {}
        self.finished = False

    def setResponseCode(self, status):
        self.status = status

    def setHeader(self, n, v):
        self.headers[n] = v

    def write(self, s):
        self.content = s

    def finish(self):
        self.finished = True


class TwistedGatewayTestCase(unittest.TestCase):
    def test_finalise_request(self):
        request = DummyHTTPRequest()
        gw = _twisted.TwistedGateway()

        gw._finaliseRequest(request, 200, 'xyz', 'text/plain')

        self.assertEquals(request.status, 200)
        self.assertEquals(request.content, 'xyz')

        self.assertTrue('Content-Type' in request.headers)
        self.assertEquals(request.headers['Content-Type'], 'text/plain')
        self.assertTrue('Content-Length' in request.headers)
        self.assertEquals(request.headers['Content-Length'], '3')

        self.assertTrue(request.finished)

    def test_get_processor(self):
        a3 = pyamf.ASObject({'target': 'null'})
        a0 = pyamf.ASObject({'target': 'foo.bar'})

        gw = _twisted.TwistedGateway()

        self.assertTrue(isinstance(gw.getProcessor(a3), _twisted.AMF3RequestProcessor))
        self.assertTrue(isinstance(gw.getProcessor(a0), _twisted.AMF0RequestProcessor))


class AMF0RequestProcessorTestCase(unittest.TestCase):
    def test_unknown_service_request(self):
        gw = _twisted.TwistedGateway({'echo': lambda x: x})
        proc = _twisted.AMF0RequestProcessor(gw)

        request = remoting.Request('sdf')

        d = proc(request)

        self.assertTrue(isinstance(d, defer.Deferred))
        response = d.result
        self.assertTrue(isinstance(response, remoting.Response))
        self.assertTrue(response.status, remoting.STATUS_ERROR)
        self.assertTrue(isinstance(response.body, remoting.ErrorFault))

    def test_error_auth(self):
        def auth(u, p):
            raise IndexError

        gw = _twisted.TwistedGateway({'echo': lambda x: x}, authenticator=auth)
        proc = _twisted.AMF0RequestProcessor(gw)

        request = remoting.Request('echo', envelope=remoting.Envelope())

        d = proc(request)

        self.assertTrue(isinstance(d, defer.Deferred))
        response = d.result
        self.assertTrue(isinstance(response, remoting.Response))
        self.assertTrue(response.status, remoting.STATUS_ERROR)
        self.assertTrue(isinstance(response.body, remoting.ErrorFault))
        self.assertEquals(response.body.code, 'IndexError')

    def test_auth_fail(self):
        def auth(u, p):
            return False

        gw = _twisted.TwistedGateway({'echo': lambda x: x}, authenticator=auth)
        proc = _twisted.AMF0RequestProcessor(gw)

        request = remoting.Request('echo', envelope=remoting.Envelope())

        d = proc(request)

        self.assertTrue(isinstance(d, defer.Deferred))
        response = d.result
        self.assertTrue(isinstance(response, remoting.Response))
        self.assertTrue(response.status, remoting.STATUS_ERROR)
        self.assertTrue(isinstance(response.body, remoting.ErrorFault))
        self.assertEquals(response.body.code, 'AuthenticationError')

    def test_deferred_auth(self):
        d = defer.Deferred()

        def auth(u, p):
            return reactor.callLater(0, lambda: True)

        gw = _twisted.TwistedGateway({'echo': lambda x: x}, authenticator=auth)
        proc = _twisted.AMF0RequestProcessor(gw)

        request = remoting.Request('echo', envelope=remoting.Envelope())

        def cb(result):
            self.assertTrue(result)
            d.callback(None)

        proc(request).addCallback(cb).addErrback(lambda failure: d.errback())

        return d

    def test_error_preprocessor(self):
        def preprocessor(service_request):
            raise IndexError

        gw = _twisted.TwistedGateway({'echo': lambda x: x}, preprocessor=preprocessor)
        proc = _twisted.AMF0RequestProcessor(gw)

        request = remoting.Request('echo', envelope=remoting.Envelope())

        d = proc(request)

        self.assertTrue(isinstance(d, defer.Deferred))
        response = d.result
        self.assertTrue(isinstance(response, remoting.Response))
        self.assertTrue(response.status, remoting.STATUS_ERROR)
        self.assertTrue(isinstance(response.body, remoting.ErrorFault))
        self.assertEquals(response.body.code, 'IndexError')

    def test_deferred_preprocessor(self):
        d = defer.Deferred()

        def preprocessor(u, p):
            return reactor.callLater(0, lambda: True)

        gw = _twisted.TwistedGateway({'echo': lambda x: x}, preprocessor=preprocessor)
        proc = _twisted.AMF0RequestProcessor(gw)

        request = remoting.Request('echo', envelope=remoting.Envelope())

        def cb(result):
            self.assertTrue(result)
            d.callback(None)

        proc(request).addCallback(cb).addErrback(lambda failure: d.errback())

        return d

    def test_preprocessor(self):
        d = defer.Deferred()

        def preprocessor(service_request):
            d.callback(None)

        gw = _twisted.TwistedGateway({'echo': lambda x: x}, preprocessor=preprocessor)
        proc = _twisted.AMF0RequestProcessor(gw)

        request = remoting.Request('echo', envelope=remoting.Envelope())

        proc(request).addErrback(lambda failure: d.errback())

        return d

    def test_exposed_preprocessor(self):
        d = defer.Deferred()

        def preprocessor(http_request, service_request):
            return reactor.callLater(0, lambda: True)

        preprocessor = gateway.expose_request(preprocessor)
        gw = _twisted.TwistedGateway({'echo': lambda x: x}, preprocessor=preprocessor)
        proc = _twisted.AMF0RequestProcessor(gw)

        request = remoting.Request('echo', envelope=remoting.Envelope())

        def cb(result):
            self.assertTrue(result)
            d.callback(None)

        proc(request).addCallback(cb).addErrback(lambda failure: d.errback())

        return d

    def test_error_body(self):
        def echo(x):
            raise KeyError

        gw = _twisted.TwistedGateway({'echo': echo})
        proc = _twisted.AMF0RequestProcessor(gw)

        request = remoting.Request('echo', envelope=remoting.Envelope())

        d = proc(request)

        self.assertTrue(isinstance(d, defer.Deferred))
        response = d.result
        self.assertTrue(isinstance(response, remoting.Response))
        self.assertTrue(response.status, remoting.STATUS_ERROR)
        self.assertTrue(isinstance(response.body, remoting.ErrorFault))
        self.assertEquals(response.body.code, 'KeyError')

    def test_error_deferred_body(self):
        d = defer.Deferred()

        def echo(x):
            d2 = defer.Deferred()

            def cb(result):
                raise IndexError

            reactor.callLater(0, lambda: d2.callback(None))

            d2.addCallback(cb)
            return d2

        gw = _twisted.TwistedGateway({'echo': echo}, expose_request=False)
        proc = _twisted.AMF0RequestProcessor(gw)

        request = remoting.Request('echo', envelope=remoting.Envelope())
        request.body = ['a']

        def cb(result):
            try:
                self.assertTrue(isinstance(result, remoting.Response))
                self.assertTrue(result.status, remoting.STATUS_ERROR)
                self.assertTrue(isinstance(result.body, remoting.ErrorFault))
                self.assertEquals(result.body.code, 'IndexError')
            except:
                d.errback()
            else:
                d.callback(None)

        proc(request).addCallback(cb).addErrback(lambda x: d.errback())

        return d


class AMF3RequestProcessorTestCase(unittest.TestCase):
    def test_unknown_service_request(self):
        gw = _twisted.TwistedGateway({'echo': lambda x: x}, expose_request=False)
        proc = _twisted.AMF3RequestProcessor(gw)

        request = remoting.Request('null', body=[messaging.RemotingMessage(body=['spam.eggs'], operation='ss')])

        d = proc(request)

        self.assertTrue(isinstance(d, defer.Deferred))
        response = d.result
        self.assertTrue(isinstance(response, remoting.Response))
        self.assertTrue(response.status, remoting.STATUS_ERROR)
        self.assertTrue(isinstance(response.body, messaging.ErrorMessage))

    def test_error_preprocessor(self):
        def preprocessor(service_request, *args):
            raise IndexError

        gw = _twisted.TwistedGateway({'echo': lambda x: x},
            expose_request=False, preprocessor=preprocessor)
        proc = _twisted.AMF3RequestProcessor(gw)

        request = remoting.Request('null', body=[messaging.RemotingMessage(body=['spam.eggs'], operation='echo')])

        d = proc(request)

        self.assertTrue(isinstance(d, defer.Deferred))
        response = d.result
        self.assertTrue(isinstance(response, remoting.Response))
        self.assertTrue(response.status, remoting.STATUS_ERROR)
        self.assertTrue(isinstance(response.body, messaging.ErrorMessage))
        self.assertEquals(response.body.faultCode, 'IndexError')

    def test_deferred_preprocessor(self):
        d = defer.Deferred()

        def preprocessor(u, *args):
            d2 = defer.Deferred()
            reactor.callLater(0, lambda: d2.callback(None))

            return d2

        gw = _twisted.TwistedGateway({'echo': lambda x: x}, expose_request=False, preprocessor=preprocessor)
        proc = _twisted.AMF3RequestProcessor(gw)

        request = remoting.Request('null', body=[messaging.RemotingMessage(body=['spam.eggs'], operation='echo')])

        def cb(result):
            self.assertTrue(result)
            d.callback(None)

        proc(request).addCallback(cb).addErrback(lambda failure: d.errback())

        return d

    def test_preprocessor(self):
        d = defer.Deferred()

        def preprocessor(service_request, *args):
            d.callback(None)

        gw = _twisted.TwistedGateway({'echo': lambda x: x}, expose_request=False, preprocessor=preprocessor)
        proc = _twisted.AMF3RequestProcessor(gw)

        request = remoting.Request('null', body=[messaging.RemotingMessage(body=['spam.eggs'], operation='echo')])

        proc(request).addErrback(lambda failure: d.errback())

        return d

    def test_exposed_preprocessor(self):
        d = defer.Deferred()

        def preprocessor(http_request, service_request):
            return reactor.callLater(0, lambda: True)

        preprocessor = gateway.expose_request(preprocessor)
        gw = _twisted.TwistedGateway({'echo': lambda x: x}, expose_request=False, preprocessor=preprocessor)
        proc = _twisted.AMF3RequestProcessor(gw)

        request = remoting.Request('null', body=[messaging.RemotingMessage(body=['spam.eggs'], operation='echo')])

        def cb(result):
            try:
                self.assertTrue(result)
            except:
                d.errback()
            else:
                d.callback(None)

        proc(request).addCallback(cb).addErrback(lambda failure: d.errback())

        return d

    def test_error_body(self):
        def echo(x):
            raise KeyError

        gw = _twisted.TwistedGateway({'echo': echo}, expose_request=False)
        proc = _twisted.AMF3RequestProcessor(gw)

        request = remoting.Request('null', body=[messaging.RemotingMessage(body=['spam.eggs'], operation='echo')])

        d = proc(request)

        self.assertTrue(isinstance(d, defer.Deferred))
        response = d.result
        self.assertTrue(isinstance(response, remoting.Response))
        self.assertTrue(response.status, remoting.STATUS_ERROR)
        self.assertTrue(isinstance(response.body, messaging.ErrorMessage))
        self.assertEquals(response.body.faultCode, 'KeyError')

    def test_error_deferred_body(self):
        d = defer.Deferred()

        def echo(x):
            d2 = defer.Deferred()

            def cb(result):
                raise IndexError

            reactor.callLater(0, lambda: d2.callback(None))

            d2.addCallback(cb)
            return d2

        gw = _twisted.TwistedGateway({'echo': echo}, expose_request=False)
        proc = _twisted.AMF3RequestProcessor(gw)

        request = remoting.Request('null', body=[messaging.RemotingMessage(body=['spam.eggs'], operation='echo')])

        def cb(result):
            try:
                self.assertTrue(isinstance(result, remoting.Response))
                self.assertTrue(result.status, remoting.STATUS_ERROR)
                self.assertTrue(isinstance(result.body, messaging.ErrorMessage))
                self.assertEquals(result.body.faultCode, 'IndexError')
            except:
                d.errback()
            else:
                d.callback(None)

        proc(request).addCallback(cb).addErrback(lambda x: d.errback())

        return d

    def test_destination(self):
        d = defer.Deferred()

        gw = _twisted.TwistedGateway({'spam.eggs': lambda x: x}, expose_request=False)
        proc = _twisted.AMF3RequestProcessor(gw)

        request = remoting.Request('null', body=[messaging.RemotingMessage(body=[None], destination='spam', operation='eggs')])

        def cb(result):
            try:
                self.assertTrue(result)
            except:
                d.errback()
            else:
                d.callback(None)

        proc(request).addCallback(cb).addErrback(lambda failure: d.errback())

        return d

    def test_async(self):
        d = defer.Deferred()

        gw = _twisted.TwistedGateway({'spam.eggs': lambda x: x}, expose_request=False)
        proc = _twisted.AMF3RequestProcessor(gw)

        request = remoting.Request('null', body=[messaging.AsyncMessage(body=[None], destination='spam', operation='eggs')])

        def cb(result):
            msg = result.body

            try:
                self.assertTrue(isinstance(msg, messaging.AcknowledgeMessage))
            except:
                d.errback()
            else:
                d.callback(None)

        proc(request).addCallback(cb).addErrback(lambda failure: d.errback())

        return d


def suite():
    import unittest

    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(TwistedServerTestCase))
    suite.addTest(unittest.makeSuite(TwistedGatewayTestCase))
    suite.addTest(unittest.makeSuite(AMF0RequestProcessorTestCase))
    suite.addTest(unittest.makeSuite(AMF3RequestProcessorTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
