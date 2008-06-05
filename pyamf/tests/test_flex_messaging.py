# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Flex Messaging compatibility tests.

@since: 0.3.2
"""

import unittest

from pyamf.flex import messaging

class AbstractMessageTestCase(unittest.TestCase):
    def test_repr(self):
        a = messaging.AbstractMessage()

        a.body = u'é,è'

        try:
            repr(a)
        except:
            self.fail()

def suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(AbstractMessageTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
