# -*- coding: utf-8 -*-
#
# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Tests for XML library integration

@since: 0.4
"""

import unittest
import sys
import traceback

import pyamf.xml
from pyamf import util


class ElementTreeTestCase(unittest.TestCase):
    """
    Tests the type mappings.
    """

    xml = '<foo bar="baz" />'

    def check_amf0(self, bytes, xml):
        b = util.BufferedByteStream(bytes)

        self.assertEqual(b.read_char(), 15)

        l = b.read_ulong()

        self.assertEqual(l, b.remaining())
        self.assertEqual(b.read(), xml)

    def check_amf3(self, bytes, xml):
        b = util.BufferedByteStream(bytes)

        self.assertEqual(b.read_char(), 11)

        l = b.read_uchar()

        self.assertEqual(l >> 1, b.remaining())
        self.assertEqual(b.read(), xml)


for mod in pyamf.xml.ETREE_MODULES:
    name = 'test_' + mod.replace('.', '_')

    def check_etree(self):
        # holy hack batman
        import inspect

        mod = inspect.stack()[1][0].f_locals['testMethod'].__name__[5:]
        mod = mod.replace('_', '.')

        try:
            etree = util.get_module(mod)
        except ImportError:
            self.skipTest('%r is not available' % (mod,))

        element = etree.fromstring(self.xml)
        xml = etree.tostring(element)
        bytes = pyamf.encode(element, encoding=pyamf.AMF0).getvalue()

        self.check_amf0(bytes, xml)

        bytes = pyamf.encode(element, encoding=pyamf.AMF3).getvalue()

        self.check_amf3(bytes, xml)

    check_etree.__name__ = name

    setattr(ElementTreeTestCase, name, check_etree)

