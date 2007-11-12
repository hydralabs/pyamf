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
Tests for PyAMF.

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import unittest

from datetime import datetime
from StringIO import StringIO

from pyamf import util

class TimestampTestCase(unittest.TestCase):
    def test_get_timestamp(self):
        self.assertEqual(util.get_timestamp(datetime(2007, 11, 12)), 1194825600)

    def test_get_datetime(self):
        self.assertEqual(util.get_datetime(1194825600), datetime(2007, 11, 12))

class StringIOProxyTestCase(unittest.TestCase):
    def test_create(self):
        sp = util.StringIOProxy()

        self.assertEquals(sp._buffer.tell(), 0)
        self.assertEquals(sp._buffer.getvalue(), '')
        self.assertEquals(len(sp), 0)
        self.assertEquals(sp.getvalue(), '')

        sp = util.StringIOProxy(None)

        self.assertEquals(sp._buffer.tell(), 0)
        self.assertEquals(sp._buffer.getvalue(), '')
        self.assertEquals(len(sp), 0)
        self.assertEquals(sp.getvalue(), '')

        sp = util.StringIOProxy('')

        self.assertEquals(sp._buffer.tell(), 0)
        self.assertEquals(sp._buffer.getvalue(), '')
        self.assertEquals(len(sp), 0)
        self.assertEquals(sp.getvalue(), '')

        sp = util.StringIOProxy('foo')

        self.assertEquals(sp._buffer.tell(), 0)
        self.assertEquals(sp._buffer.getvalue(), 'foo')
        self.assertEquals(len(sp), 3)
        self.assertEquals(sp.getvalue(), 'foo')

        sp = util.StringIOProxy(StringIO('this is a test'))
        self.assertEquals(sp._buffer.tell(), 0)
        self.assertEquals(sp._buffer.getvalue(), 'this is a test')
        self.assertEquals(len(sp), 14)
        self.assertEquals(sp.getvalue(), 'this is a test')

        self.assertRaises(TypeError, util.StringIOProxy, self)

def suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(TimestampTestCase))
    suite.addTest(unittest.makeSuite(StringIOProxyTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
