# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Tests for Local Shared Object (LSO) Implementation.

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import unittest

import pyamf
from pyamf import amf0, util, sol

class DecoderTestCase(unittest.TestCase):
    def test_header(self):
        bytes = '\x00\xbf\x00\x00\x00\x15TCSO\x00\x04\x00\x00\x00\x00\x00\x05hello\x00\x00\x00\x00'

        try:
            sol.decode(bytes)
        except:
            raise
            self.fail("Error decoding stream")

    def test_invalid_header(self):
        bytes = '\x00\x00\x00\x00\x00\x15TCSO\x00\x04\x00\x00\x00\x00\x00\x05hello\x00\x00\x00\x00'
        self.assertRaises(pyamf.DecodeError, sol.decode, bytes)

    def test_invalid_header_length(self):
        bytes = '\x00\xbf\x00\x00\x00\x05TCSO\x00\x04\x00\x00\x00\x00\x00\x05hello\x00\x00\x00\x00'
        self.assertRaises(pyamf.DecodeError, sol.decode, bytes)

    def test_strict_header_length(self):
        bytes = '\x00\xbf\x00\x00\x00\x00TCSO\x00\x04\x00\x00\x00\x00\x00\x05hello\x00\x00\x00\x00'

        try:
            sol.decode(bytes, strict=False)
        except:
            self.fail("Error occurred decoding stream")

    def test_invalid_signature(self):
        bytes = '\x00\xbf\x00\x00\x00\x15ABCD\x00\x04\x00\x00\x00\x00\x00\x05hello\x00\x00\x00\x00'
        self.assertRaises(pyamf.DecodeError, sol.decode, bytes)

    def test_invalid_header_name_length(self):
        bytes = '\x00\xbf\x00\x00\x00\x15TCSO\x00\x04\x00\x00\x00\x00\x00\x01hello\x00\x00\x00\x00'
        self.assertRaises(pyamf.DecodeError, sol.decode, bytes)

    def test_invalid_header_padding(self):
        bytes = '\x00\xbf\x00\x00\x00\x15TCSO\x00\x04\x00\x00\x00\x00\x00\x05hello\x00\x00\x00\x01'
        self.assertRaises(pyamf.DecodeError, sol.decode, bytes)

class EncoderTestCase(unittest.TestCase):
    def test_encode_header(self):
        stream = sol.encode('hello', {})

        self.assertEquals(stream.getvalue(),
            '\x00\xbf\x00\x00\x00\x15TCSO\x00\x04\x00\x00\x00\x00\x00\x05hello\x00\x00\x00\x00')

    def test_multiple_values(self):
        stream = sol.encode('hello', {'name': 'value', 'spam': 'eggs'})

        self.assertEquals(stream.getvalue(),
            '\x00\xbf\x00\x00\x002TCSO\x00\x04\x00\x00\x00\x00\x00\x05hello'
            '\x00\x00\x00\x00\x00\x04name\x02\x00\x05value\x00\x00\x04spam'
            '\x02\x00\x04eggs\x00')

def suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(EncoderTestCase))
    suite.addTest(unittest.makeSuite(DecoderTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
