# -*- coding: utf-8 -*-
#
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
    def setUp(self):
        self.collection = codec.IndexedCollection()

    def test_clear(self):
        o = object()

        self.assertEqual(sys.getrefcount(o), 2)
        self.collection.append(o)
        self.assertEqual(sys.getrefcount(o), 3)

        self.collection.clear()

        self.assertEqual(sys.getrefcount(o), 2)

    def test_delete(self):
        o = object()

        self.assertEqual(sys.getrefcount(o), 2)
        self.collection.append(o)
        self.assertEqual(sys.getrefcount(o), 3)

        del self.collection

        self.assertEqual(sys.getrefcount(o), 2)

    def test_append(self):
        max = 5
        for i in range(0, max):
            test_obj = TestObject()

            test_obj.name = i

            self.assertEqual(sys.getrefcount(test_obj), 2)
            self.collection.append(test_obj)
            self.assertEqual(sys.getrefcount(test_obj), 3)

        self.assertEqual(max, len(self.collection))

        for i in range(0, max):
            self.assertEqual(i, self.collection[i].name)

    def test_get_reference_to(self):
        test_obj = TestObject()

        self.collection.append(test_obj)

        self.assertEqual(sys.getrefcount(test_obj), 3)
        idx = self.collection.getReferenceTo(test_obj)
        self.assertEqual(sys.getrefcount(test_obj), 3)

        self.assertEqual(0, idx)
        self.assertEqual(-1, self.collection.getReferenceTo(TestObject()))

    def test_get_by_reference(self):
        test_obj = TestObject()
        idx = self.collection.append(test_obj)

        self.assertEqual(id(test_obj), id(self.collection.getByReference(idx)))

        idx = self.collection.getReferenceTo(test_obj)

        self.assertEqual(id(test_obj), id(self.collection.getByReference(idx)))
        self.assertRaises(TypeError, self.collection.getByReference, 'bad ref')

        self.assertEqual(None, self.collection.getByReference(74))

    def test_get_by_refererence_refcount(self):
        test_obj = TestObject()
        idx = self.collection.append(test_obj)

        o = self.collection.getByReference(idx)

        self.assertIdentical(o, test_obj)

    def test_array(self):
        test_obj = []
        idx = self.collection.append(test_obj)
        self.assertEqual(id(test_obj), id(self.collection.getByReference(idx)))