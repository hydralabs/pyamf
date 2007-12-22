# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Twisted gateway tests.

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

from twisted.internet import defer, reactor
from twisted.web import http, server, client, error, resource
from twisted.protocols import loopback
from twisted.trial import unittest

import pyamf
from pyamf import remoting, util
from pyamf.remoting.twistedgateway import TwistedGateway

class TestService(object):
    def foo(self):
        return 'foo'

    def echo(self, x):
        return x

class TwistedServerTestCase(unittest.TestCase):
    def setUp(self):
        self.gw = TwistedGateway()
        root = resource.Resource()
        root.putChild('', self.gw)

        self.p = reactor.listenTCP(0, server.Site(root),
            interface="127.0.0.1")
        self.port = self.p.getHost().port

    def tearDown(self):
        return self.p.stopListening()

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

def suite():
    import unittest

    suite = unittest.TestSuite()
    
    suite.addTest(unittest.makeSuite(TwistedServerTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
