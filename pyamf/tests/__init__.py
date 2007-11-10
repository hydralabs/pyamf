# -*- encoding: utf-8 -*-
#
# Copyright (c) 2007 The PyAMF Project. All rights reserved.
# 
# Arnar Birgisson
# Thijs Triemstra
# Nick Joyce
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

"""
Tests for PyAMF.

@author: U{Arnar Birgisson<mailto:arnarbi@gmail.com>}
@author: U{Thijs Triemstra<mailto:info@collab.nl>}
@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import unittest

from pyamf import Bag

class BagTestCase(unittest.TestCase):
    """
    I exercise all functionality relating to the Bag class
    """

    def test_init(self):
        bag = Bag(dict(foo='bar', baz='foo'))

        self.assertEquals(bag, dict(foo='bar', baz='foo'))
        self.assertEquals(bag.foo, 'bar')
        self.assertEquals(bag.baz, 'foo')

    def test_eq(self):
        bag = Bag()

        self.assertEquals(bag, {})
        self.assertNotEquals(bag, {'foo': 'bar'})

        bag2 = Bag()

        self.assertEquals(bag2, {})
        self.assertEquals(bag, bag2)
        self.assertNotEquals(bag, None)

    def test_setitem(self):
        bag = Bag()

        self.assertEquals(bag, {})
        
        bag['foo'] = 'bar'

        self.assertEquals(bag.foo, 'bar')

    def test_delitem(self):
        bag = Bag({'foo': 'bar'})

        self.assertEquals(bag.foo, 'bar')
        del bag['foo']

        self.assertRaises(AttributeError, lambda: bag.foo)
    
    def test_getitem(self):
        bag = Bag({'foo': 'bar'})

        self.assertEquals(bag['foo'], 'bar')

    def test_iter(self):
        bag = Bag({'foo': 'bar'})

        x = []

        for k, v in bag.iteritems():
            x.append((k, v))

        self.assertEquals(x, [('foo', 'bar')])

def suite():
    import pyamf
    from pyamf.tests import amf0, amf3, remoting

    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(BagTestCase))
    suite.addTest(amf0.suite())
    suite.addTest(amf3.suite())
    suite.addTest(remoting.suite())

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
