# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Test utilities.

@author: U{Arnar Birgisson<mailto:arnarbi@gmail.com>}
@author: U{Thijs Triemstra<mailto:info@collab.nl>}
@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

class EncoderTester(object):
    """
    A helper object that takes some input, runs over the encoder
    and checks the output.
    """

    def __init__(self, encoder, data):
        self.encoder = encoder
        self.buf = encoder.stream
        self.data = data

    def getval(self):
        t = self.buf.getvalue()
        self.buf.truncate(0)

        return t

    def run(self, testcase):
        for n, s in self.data:
            self.encoder.writeElement(n)

            testcase.assertEqual(self.getval(), s)

class DecoderTester(object):
    """
    A helper object that takes some input, runs over the decoder
    and checks the output.
    """

    def __init__(self, decoder, data):
        self.decoder = decoder
        self.buf = decoder.stream
        self.data = data

    def run(self, testcase):
        for n, s in self.data:
            self.buf.truncate(0)
            self.buf.write(s)
            self.buf.seek(0)

            testcase.assertEqual(self.decoder.readElement(), n)

            if self.buf.remaining() != 0:
                from pyamf.util import hexdump

                print hexdump(self.buf.getvalue())

            # make sure that the entire buffer was consumed
            testcase.assertEqual(self.buf.remaining(), 0)

# Some workarounds to bring unittest module up to scratch
import unittest

if not hasattr(unittest.TestCase, 'assertTrue'):
    def assertTrue(self, value):
        self.assertEquals(value, True)

    unittest.TestCase.assertTrue = assertTrue

if not hasattr(unittest.TestCase, 'assertFalse'):
    def assertFalse(self, value):
        self.assertEquals(value, False)

    unittest.TestCase.assertFalse = assertFalse
