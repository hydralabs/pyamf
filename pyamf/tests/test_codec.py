# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Tests for AMF utilities.

@since: 0.1.0
"""

import unittest
import sys

import pyamf
from pyamf import codec


class TestObject(object):
    def __init__(self):
        self.name = 'test'


class IndexedCollectionTestCase(unittest.TestCase):
    """
    Tests for L{codec.IndexedCollection}
    """

    def setUp(self):
        self.collection = codec.IndexedCollection()

    def test_clear(self):
        o = object()

        self.assertEqual(self.collection.getReferenceTo(o), -1)

        self.collection.append(o)
        self.assertEqual(self.collection.getReferenceTo(o), 0)

        self.collection.clear()

        self.assertEqual(self.collection.getReferenceTo(o), -1)

    def test_append(self):
        n = 5

        for i in range(0, n):
            test_obj = TestObject()

            test_obj.name = i

            self.collection.append(test_obj)

        self.assertEqual(len(self.collection), n)

        for i in range(0, n):
            self.assertEqual(i, self.collection[i].name)

    def test_get_reference_to(self):
        test_obj = TestObject()

        self.collection.append(test_obj)

        idx = self.collection.getReferenceTo(test_obj)

        self.assertEqual(0, idx)
        self.assertEqual(-1, self.collection.getReferenceTo(TestObject()))

    def test_get_by_reference(self):
        test_obj = TestObject()
        idx = self.collection.append(test_obj)

        self.assertIdentical(test_obj, self.collection.getByReference(idx))

        idx = self.collection.getReferenceTo(test_obj)

        self.assertIdentical(test_obj, self.collection.getByReference(idx))
        self.assertRaises(pyamf.ReferenceError,
            self.collection.getByReference, 'bad ref')

        self.assertEqual(None, self.collection.getByReference(74))

    def test_len(self):
        self.assertEqual(0, len(self.collection))

        self.collection.append([])

        self.assertEqual(1, len(self.collection))

        self.collection.append({})

        self.assertEqual(2, len(self.collection))

        self.collection.clear()
        self.assertEqual(0, len(self.collection))

    def test_repr(self):
        x = "0x%x" % id(self.collection)

        self.assertEqual(repr(self.collection),
            '<pyamf.codec.IndexedCollection size=0 %s>' % (x,))

    def test_contains(self):
        o = object()

        self.assertFalse(o in self.collection)

        self.collection.append(o)

        self.assertTrue(o in self.collection)
