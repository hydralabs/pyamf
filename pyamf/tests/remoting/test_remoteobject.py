# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Remote Object Tests.

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}
@since: 0.1
"""

import unittest

import pyamf
from pyamf import remoting
from pyamf.remoting import amf3, gateway
from pyamf.flex import messaging

class RandomIdGeneratorTestCase(unittest.TestCase):
    def test_generate(self):
        x = []

        for i in range(5):
            id_ = amf3.generate_random_id()

            self.assertTrue(id_ not in x)
            x.append(id_)

class AcknowlegdementGeneratorTestCase(unittest.TestCase):
    def test_generate(self):
        ack = amf3.generate_acknowledgement()

        self.assertTrue(isinstance(ack, messaging.AcknowledgeMessage))
        self.assertTrue(ack.messageId is not None)
        self.assertTrue(ack.clientId is not None)
        self.assertTrue(ack.timestamp is not None)

    def test_request(self):
        ack = amf3.generate_acknowledgement(pyamf.Bag({'messageId': '123123'}))

        self.assertTrue(isinstance(ack, messaging.AcknowledgeMessage))
        self.assertTrue(ack.messageId is not None)
        self.assertTrue(ack.clientId is not None)
        self.assertTrue(ack.timestamp is not None)

        self.assertEquals(ack.correlationId, '123123')

class RequestProcessorTestCase(unittest.TestCase):
    def test_create(self):
        rp = amf3.RequestProcessor('xyz')
        self.assertEquals(rp.gateway, 'xyz')

    def test_ping(self):
        message = messaging.CommandMessage(operation=5)
        rp = amf3.RequestProcessor(None)
        request = remoting.Request('null', body=[message])

        response = rp(request)
        ack = response.body

        self.assertTrue(isinstance(response, remoting.Response))
        self.assertEquals(response.status, remoting.STATUS_OK)
        self.assertTrue(isinstance(ack, messaging.AcknowledgeMessage))
        self.assertEquals(ack.body, True)

    def test_request(self):
        def echo(x):
            return x

        gw = gateway.BaseGateway({'echo': echo})
        rp = amf3.RequestProcessor(gw)
        message = messaging.RemotingMessage(body=['foo.bar'], operation='echo')
        request = remoting.Request('null', body=[message])

        response = rp(request)
        ack = response.body

        self.assertTrue(isinstance(response, remoting.Response))
        self.assertEquals(response.status, remoting.STATUS_OK)
        self.assertTrue(isinstance(ack, messaging.AcknowledgeMessage))
        self.assertEquals(ack.body, 'foo.bar')

def suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(RandomIdGeneratorTestCase))
    suite.addTest(unittest.makeSuite(AcknowlegdementGeneratorTestCase))
    suite.addTest(unittest.makeSuite(RequestProcessorTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
