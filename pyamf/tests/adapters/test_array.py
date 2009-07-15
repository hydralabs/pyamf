# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.

"""
Tests for the L{collections} L{pyamf.adapters._collections} module.

@since: 0.5
"""


import unittest
import array

import pyamf


class ArrayTestCase(unittest.TestCase):
    """
    """

    def setUp(self):
        self.orig = ['f', 'o', 'o']
        self.obj = array.array('c')

        self.obj.append('f')
        self.obj.append('o')
        self.obj.append('o')

    def encdec(self, encoding):
        return pyamf.decode(pyamf.encode(self.obj, encoding=encoding),
            encoding=encoding).next()

    def test_amf0(self):
        self.assertEquals(self.encdec(pyamf.AMF0), self.orig)

    def test_amf3(self):
        self.assertEquals(self.encdec(pyamf.AMF3), self.orig)


def suite():
    suite = unittest.TestSuite()

    classes = []

    if hasattr(array, 'array'):
        classes.append(ArrayTestCase)

    for x in classes:
        suite.addTest(unittest.makeSuite(x))

    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
