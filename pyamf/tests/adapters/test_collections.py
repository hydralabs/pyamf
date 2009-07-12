# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.

"""
Tests for the L{collections} L{pyamf.adapters._collections} module.

@since: 0.5
"""


import unittest
import collections

import pyamf


class CollectionsTestCase(unittest.TestCase):
    """
    """

    def encdec(self, encoding):
        return pyamf.decode(pyamf.encode(self.obj, encoding=encoding),
            encoding=encoding).next()


class DequeTestCase(CollectionsTestCase):
    """
    Tests for L{collections.deque}
    """

    def setUp(self):
        self.orig = [1, 2, 3]
        self.obj = collections.deque(self.orig)

    def test_amf0(self):
        self.assertEquals(self.encdec(pyamf.AMF0), self.orig)

    def test_amf3(self):
        self.assertEquals(self.encdec(pyamf.AMF3), self.orig)


class DefaultDictTestCase(CollectionsTestCase):
    """
    Tests for L{collections.defaultdict}
    """

    def setUp(self):
        s = 'mississippi'
        self.obj = collections.defaultdict(int)

        for k in s:
            self.obj[k] += 1

        self.orig = dict(self.obj)

    def test_amf0(self):
        self.assertEquals(self.encdec(pyamf.AMF3), self.orig)

    def test_amf3(self):
        self.assertEquals(self.encdec(pyamf.AMF3), self.orig)


def suite():
    suite = unittest.TestSuite()

    classes = []

    if hasattr(collections, 'deque'):
        classes.append(DequeTestCase)

    if hasattr(collections, 'defaultdict'):
        classes.append(DefaultDictTestCase)

    for x in classes:
        suite.addTest(unittest.makeSuite(x))

    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
