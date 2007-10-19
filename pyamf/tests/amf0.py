# -*- encoding: utf-8 -*-
#
# Copyright (c) 2007 The PyAMF Project. All rights reserved.
# 
# Arnar Birgisson
# Thijs Triemstra
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
#

import unittest

from pyamf import amf0, util

class EncoderTester(object):
    """
    A helper object that takes some input, runs over the encoder and checks
    the output
    """

    def __init__(self, encoder, data):
        self.encoder = encoder
        self.buf = encoder.output
        self.data = data

    def getval(self):
        t = self.buf.getvalue()
        self.buf.truncate(0)

        return t

    def run(self, testcase):
        for n, s in self.data:
            self.encoder.writeElement(n)

            testcase.assertEqual(self.getval(), s)


class EncoderTestCase(unittest.TestCase):

    def setUp(self):
        self.buf = util.BufferedByteStream()
        self.e = amf0.Encoder(self.buf)
        
        
    def _run(self, data):
        e = EncoderTester(self.e, data)
        e.run(self)

    def test_number(self):
        data = [
            (0,    '\x00\x00\x00\x00\x00\x00\x00\x00\x00'),
            (0.2,  '\x00\x3f\xc9\x99\x99\x99\x99\x99\x9a'),
            (1,    '\x00\x3f\xf0\x00\x00\x00\x00\x00\x00'),
            (42,   '\x00\x40\x45\x00\x00\x00\x00\x00\x00'),            (-123, '\x00\xc0\x5e\xc0\x00\x00\x00\x00\x00'),
            (1.23456789, '\x00\x3f\xf3\xc0\xca\x42\x83\xde\x1b')]

        # XXX nick: Should we be testing python longs here?

        self._run(data)

    def test_boolean(self):
        data = [
            (True, '\x01\x01'),
            (False, '\x01\x00')]

        self._run(data)

    def test_string(self):
        data = [
            ('', '\x02\x00\x00'),
            ('hello', '\x02\x00\x05hello'),
            # unicode excerpt taken from http://www.columbia.edu/kermit/utf8.html
            (u'ᚠᛇᚻ', '\x02\x00\t\xe1\x9a\xa0\xe1\x9b\x87\xe1\x9a\xbb')]

        self._run(data)

    def test_null(self):
        data = [(None, '\x05')]

        self._run(data)

    def test_list(self):
        data = [
            ([], '\x0a\x00\x00'),
            ([1, 2, 3], '\x0a\x00\x03\x00?\xf0\x00\x00\x00\x00\x00\x00\x00@\x00\x00\x00\x00\x00\x00\x00\x00@\x08\x00\x00\x00\x00\x00\x00')]

        self._run(data)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(EncoderTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
