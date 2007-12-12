# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Twisted gateway tests.

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import unittest

from twisted.internet import defer, reactor

from pyamf import remoting
from pyamf.remoting import gateway
from pyamf.remoting.twistedgateway import ServiceRequest

class TestService(object):
    def foo(self):
        return 'foo'

    def echo(self, x):
        return x

class ServiceRequestTestCase(unittest.TestCase):
    def test_authenticate(self):
        sw = gateway.ServiceWrapper(TestService)
        request = remoting.Envelope()

        x = ServiceRequest(request, sw, None)

        self.assertTrue(x.authenticate(None, None))

        def auth(u, p):
            d = defer.Deferred()

            def _check(u, p):
                d.callback(u == 'foo' and p == 'bar')

            reactor.callLater(0, _check, u, p)

            return d

        sw = gateway.ServiceWrapper(TestService, authenticator=auth)
        request = remoting.Envelope()

        x = gateway.ServiceRequest(request, sw, None)

        self.assertFalse(x.authenticate(None, None))
        self.assertTrue(x.authenticate('foo', 'bar'))

    def test_call(self):
        sw = gateway.ServiceWrapper(TestService)
        request = remoting.Envelope()

        x = gateway.ServiceRequest(request, sw, None)

        self.assertRaises(TypeError, x)

        x = gateway.ServiceRequest(request, sw, 'foo')
        self.assertEquals(x(), 'foo')

        x = gateway.ServiceRequest(request, sw, 'echo')
        self.assertEquals(x(x), x)

class TwistedServerTestCase(unittest.TestCase):
    def test_basic(self):
        pass

def suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(ServiceRequestTestCase))
    suite.addTest(unittest.makeSuite(TwistedServerTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
