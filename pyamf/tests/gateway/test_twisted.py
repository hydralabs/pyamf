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
Twisted Gateway tests.

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import unittest

from twisted.internet import defer, reactor

import pyamf
from pyamf import remoting, util, gateway
from pyamf.gateway.twisted import TwistedGateway, ServiceRequest

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
