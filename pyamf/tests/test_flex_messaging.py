# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.

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
            raise
            self.fail()


class EncodingTestCase(unittest.TestCase):
    """
    Encoding tests for L{messaging}
    """

    def test_AcknowledgeMessage(self):
        m = messaging.AcknowledgeMessage()
        m.correlationId = '1234'

        self.assertEquals(pyamf.encode(m).getvalue(),
            '\x11\n\x81\x03Uflex.messaging.messages.AcknowledgeMessage\tbody'
            '\x11clientId\x1bcorrelationId\x17destination\x0fheaders\x13'
            'messageId\x15timeToLive\x13timestamp\x01\x01\x06\t1234\x01\n\x0b'
            '\x01\x01\x01\x04\x00\x04\x00')

    def test_CommandMessage(self):
        m = messaging.CommandMessage(operation='foo.bar')

        self.assertEquals(pyamf.encode(m).getvalue(),
            '\x11\n\x81\x13Mflex.messaging.messages.CommandMessage\tbody\x11'
            'clientId\x1bcorrelationId\x17destination\x0fheaders\x13messageId'
            '\x13operation\x15timeToLive\x13timestamp\x01\x01\x01\x01\n\x0b'
            '\x01\x01\x01\x06\x0ffoo.bar\x04\x00\x04\x00')

    def test_ErrorMessage(self):
        m = messaging.ErrorMessage(faultString='ValueError')

        self.assertEquals(pyamf.encode(m).getvalue(),
            '\x11\n\x81SIflex.messaging.messages.ErrorMessage\tbody\x11'
            'clientId\x1bcorrelationId\x17destination\x19extendedData\x13'
            'faultCode\x17faultDetail\x17faultString\x0fheaders\x13messageId'
            '\x13rootCause\x15timeToLive\x13timestamp\x01\x01\x01\x01\n\x0b'
            '\x01\x01\x01\x01\x06\x15ValueError\n\x0b\x01\x01\x01\n\x0b\x01'
            '\x01\x04\x00\x04\x00')

    def test_RemotingMessage(self):
        m = messaging.RemotingMessage(source='foo.bar')

        self.assertEquals(pyamf.encode(m).getvalue(),
            '\x11\n\x81\x13Oflex.messaging.messages.RemotingMessage'
            '\tbody\x11clientId\x17destination\x0fheaders\x13messageId\x13'
            'operation\rsource\x15timeToLive\x13timestamp\x01\x01\x01\n\x0b'
            '\x01\x01\x01\x01\x06\x0ffoo.bar\x04\x00\x04\x00')


def suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(AbstractMessageTestCase))
    suite.addTest(unittest.makeSuite(EncodingTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
