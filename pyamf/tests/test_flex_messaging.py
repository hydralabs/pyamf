# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE for details.

"""
Flex Messaging compatibility tests.

@since: 0.3.2
"""

import unittest

import pyamf
from pyamf.flex import messaging

class AbstractMessageTestCase(unittest.TestCase):
    def test_repr(self):
        a = messaging.AbstractMessage()

        a.body = u'é,è'

        try:
            repr(a)
        except:
            self.fail()

class EncodingTestCase(unittest.TestCase):
    def test_AsyncMessage(self):
        m = messaging.AsyncMessage()
        m.correlationId = '1234'

        self.assertEquals(pyamf.encode(m).getvalue(),
            '\x11\n\x81\x03Iflex.messaging.messages.AsyncMessage\x1b'
            'correlationId\tbody\x11clientId\x17destination\x0fheaders\x13'
            'messageId\x15timeToLive\x13timestamp\x06\t1234\x01\x01\x01\n\x0b'
            '\x01\x01\x01\x04\x00\x04\x00')

    def test_AcknowledgeMessage(self):
        m = messaging.AcknowledgeMessage()
        m.correlationId = '1234'

        self.assertEquals(pyamf.encode(m).getvalue(),
            '\x11\n\x81\x03Uflex.messaging.messages.AcknowledgeMessage'
            '\x1bcorrelationId\tbody\x11clientId\x17destination\x0fheaders\x13'
            'messageId\x15timeToLive\x13timestamp\x06\t1234\x01\x01\x01\n\x0b'
            '\x01\x01\x01\x04\x00\x04\x00')

    def test_CommandMessage(self):
        m = messaging.CommandMessage(operation='foo.bar')

        self.assertEquals(pyamf.encode(m).getvalue(),
            '\x11\n\x81#Mflex.messaging.messages.CommandMessage\x13operation'
            '\x1dmessageRefType\x1bcorrelationId\tbody\x11clientId\x17'
            'destination\x0fheaders\x13messageId\x15timeToLive\x13timestamp'
            '\x06\x0ffoo.bar\x01\x01\x01\x01\x01\n\x0b\x01\x01\x01\x04\x00'
            '\x04\x00')

    def test_ErrorMessage(self):
        m = messaging.ErrorMessage(faultString='ValueError')

        self.assertEquals(pyamf.encode(m).getvalue(),
            '\x11\n\x81SIflex.messaging.messages.ErrorMessage\x19extendedData'
            '\x13faultCode\x17faultDetail\x17faultString\x13rootCause\x1b'
            'correlationId\tbody\x11clientId\x17destination\x0fheaders\x13'
            'messageId\x15timeToLive\x13timestamp\n\x0b\x01\x01\x01\x01\x06'
            '\x15ValueError\n\x0b\x01\x01\x01\x01\x01\x01\n\x0b\x01\x01\x01'
            '\x04\x00\x04\x00')

    def test_RemotingMessage(self):
        m = messaging.RemotingMessage(source='foo.bar')

        self.assertEquals(pyamf.encode(m).getvalue(),
            '\x11\n\x81\x13Oflex.messaging.messages.RemotingMessage\x13'
            'operation\rsource\tbody\x11clientId\x17destination\x0fheaders\x13'
            'messageId\x15timeToLive\x13timestamp\x01\x06\x0ffoo.bar\x01\x01'
            '\x01\n\x0b\x01\x01\x01\x04\x00\x04\x00')

def suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(AbstractMessageTestCase))
    suite.addTest(unittest.makeSuite(EncodingTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
