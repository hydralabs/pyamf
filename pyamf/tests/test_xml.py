# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2009 The PyAMF Project.
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
        import cElementTree

        self.assertEquals(self._encode(cElementTree), (
            ElementTreeTestCase.amf0_encoding,
            ElementTreeTestCase.amf3_encoding
        ))

    def test_xe_cElementTree(self):
        from xml.etree import cElementTree

        self.assertEquals(self._encode(cElementTree), (
            ElementTreeTestCase.amf0_encoding,
            ElementTreeTestCase.amf3_encoding
        ))

    def test_xe_ElementTree(self):
        from xml.etree import ElementTree

        self.assertEquals(self._encode(ElementTree), (
            ElementTreeTestCase.amf0_encoding,
            ElementTreeTestCase.amf3_encoding
        ))

    def test_ElementTree(self):
        from elementtree import ElementTree

        self.assertEquals(self._encode(ElementTree), (
            ElementTreeTestCase.amf0_encoding,
            ElementTreeTestCase.amf3_encoding
        ))

try:
    from xml.etree import cElementTree
except ImportError:
    del ElementTreeTestCase.test_xe_cElementTree

try:
    import cElementTree
except ImportError:
    del ElementTreeTestCase.test_cElementTree

try:
    from xml.etree import ElementTree
except ImportError:
    del ElementTreeTestCase.test_xe_ElementTree

try:
    from elementtree import ElementTree
except ImportError:
    del ElementTreeTestCase.test_ElementTree


def suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(ElementTreeTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
