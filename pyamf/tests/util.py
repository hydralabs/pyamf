# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Test utilities.

@author: U{Arnar Birgisson<mailto:arnarbi@gmail.com>}
@author: U{Thijs Triemstra<mailto:info@collab.nl>}
@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

class GenericObject(object):
    """
    A basic object for en/decoding.
    """

    def __init__(self, dict):
        self.__dict__ = dict

    def __cmp__(self, other):
        return cmp(self.__dict__, other)

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
