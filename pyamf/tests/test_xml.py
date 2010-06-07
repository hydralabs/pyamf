# -*- coding: utf-8 -*-
#
# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Tests for XML library integration

@since: 0.4
"""

import unittest

import pyamf


class ElementTreeTestCase(unittest.TestCase):
    """
    Tests the type mappings.
    """

    amf0_encoding = '\x0f\x00\x00\x00\x11<foo bar="baz" />'
    amf3_encoding = '\x0b#<foo bar="baz" />'

    def _encode(self, mod):
        element = mod.Element('foo', bar='baz')

        return (
            pyamf.encode(element, encoding=pyamf.AMF0).getvalue(),
            pyamf.encode(element, encoding=pyamf.AMF3).getvalue()
        )

    def test_cElementTree(self):
        try:
            import cElementTree
        except ImportError:
            raise unittest.SkipTest("'cElementTree' is not available")

        self.assertEqual(self._encode(cElementTree), (
            ElementTreeTestCase.amf0_encoding,
            ElementTreeTestCase.amf3_encoding
        ))

    def test_xe_cElementTree(self):
        try:
            from xml.etree import cElementTree
        except ImportError:
            raise unittest.SkipTest("'xml.etree.cElementTree' is not available")

        self.assertEqual(self._encode(cElementTree), (
            ElementTreeTestCase.amf0_encoding,
            ElementTreeTestCase.amf3_encoding
        ))

    def test_xe_ElementTree(self):
        try:
            from xml.etree import ElementTree
        except ImportError:
            raise unittest.SkipTest("'xml.etree.ElementTree' is not available")

        self.assertEqual(self._encode(ElementTree), (
            ElementTreeTestCase.amf0_encoding,
            ElementTreeTestCase.amf3_encoding
        ))

    def test_ElementTree(self):
        try:
            from elementtree import ElementTree
        except ImportError:
            raise unittest.SkipTest("'elementtree.cElementTree' is not available")

        self.assertEqual(self._encode(ElementTree), (
            ElementTreeTestCase.amf0_encoding,
            ElementTreeTestCase.amf3_encoding
        ))
