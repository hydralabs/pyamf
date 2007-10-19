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

from pyamf import amf, util

class AMF0EncoderTestCase(unittest.TestCase):
    
    def setUp(self):
        self.buf = util.BufferedByteStream()
        self.e = amf.AMF0Encoder(self.buf)
    
    def getval(self):
        t = self.buf.getvalue()
        self.buf.truncate(0)
        return t
    
    def test_number(self):
        t = [(0,    '\x00\x00\x00\x00\x00\x00\x00\x00\x00'),
             (0.2,  '\x00\x3f\xc9\x99\x99\x99\x99\x99\x9a'),
             (1,    '\x00\x3f\xf0\x00\x00\x00\x00\x00\x00'),
             (42,   '\x00\x40\x45\x00\x00\x00\x00\x00\x00'),
             (-123, '\x00\xc0\x5e\xc0\x00\x00\x00\x00\x00'),
             (1.23456789, '\x00\x3f\xf3\xc0\xca\x42\x83\xde\x1b'),
            ]
        for n, s in t:
            self.e.writeNumber(n)
            self.assertEqual(self.getval(), s)
            self.e.writeElement(n)
            self.assertEqual(self.getval(), s)
    
    def test_boolean(self):
        self.e.writeElement(True)
        self.assertEqual(self.getval(), '\x01\x01')
        self.e.writeElement(False)
        self.assertEqual(self.getval(), '\x01\x00')

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AMF0EncoderTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
