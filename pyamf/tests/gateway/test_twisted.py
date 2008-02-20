# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Twisted gateway tests.

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

from twisted.internet import reactor, defer
from twisted.web import http, server, client, error, resource
from twisted.trial import unittest

import pyamf
from pyamf import remoting
from pyamf.remoting import twistedgateway

class TestService(object):
    def spam(self):
        return 'spam'

    def echo(self, x):
        return x

class TwistedServerTestCase(unittest.TestCase):
    def setUp(self):
        self.gw = twistedgateway.TwistedGateway(expose_request=False)
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

        def echo(request, data):
            self.assertTrue(isinstance(request, http.Request))

            return data

        self.gw.addService(echo)

        env = remoting.Envelope(pyamf.AMF0, pyamf.ClientTypes.Flash9)
        request = remoting.Request('echo', body=['hello'])
        env['/1'] = request

        return client.getPage("http://127.0.0.1:%d/" % (self.port,),
                method="POST", postdata=remoting.encode(env).getvalue())

    def test_encoding_error(self):
        encode = twistedgateway.remoting.encode

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

        twistedgateway.remoting.encode = force_error
        def switch(x):
            twistedgateway.remoting.encode = encode

        d = self.assertFailure(d, error.Error)

        def check(exc):
            self.assertEquals(int(exc.args[0]), http.INTERNAL_SERVER_ERROR)
            self.assertTrue(exc.args[1].startswith('500 Internal Server Error'))

        d.addCallback(check)

        return d.addBoth(switch)

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
        gw = twistedgateway.TwistedGateway()

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

        gw = twistedgateway.TwistedGateway()

        self.assertTrue(isinstance(gw.getProcessor(a3), twistedgateway.AMF3RequestProcessor))
        self.assertTrue(isinstance(gw.getProcessor(a0), twistedgateway.AMF0RequestProcessor))

class AMF0RequestProcessorTestCase(unittest.TestCase):
    def test_auth_fail(self):
        def auth(username, password):
            return False

        gw = twistedgateway.TwistedGateway(expose_request=False)
        processor = twistedgateway.AMF0RequestProcessor(gw)

        self.gw.authenticator = auth

        env = remoting.Envelope(pyamf.AMF0, pyamf.ClientTypes.Flash9)
        request = remoting.Request('echo', body=['hello'])
        env['/1'] = request

        print self.gw(env)

def suite():
    import unittest

    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(TwistedServerTestCase))
    suite.addTest(unittest.makeSuite(TwistedGatewayTestCase))
    #suite.addTest(unittest.makeSuite(AMF0RequestProcessorTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
