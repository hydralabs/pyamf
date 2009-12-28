"""
Tests for L{pyamf.version}
"""

import unittest

from pyamf import versions


class VersionTestCase(unittest.TestCase):
    """
    Tests for L{pyamf.version.get_version}
    """

    def test_version(self):
        self.assertEquals(versions.get_version((0, 0)), '0.0')
        self.assertEquals(versions.get_version((0, 1)), '0.1')
        self.assertEquals(versions.get_version((3, 2)), '3.2')
        self.assertEquals(versions.get_version((3, 2, 1)), '3.2.1')

        self.assertEquals(versions.get_version((3, 2, 1, 'alpha')), '3.2.1alpha')
        self.assertEquals(versions.get_version((3, 2, 1, 'alpha', 0)), '3.2.1 pre-alpha')

        self.assertEquals(versions.get_version((3, 2, 1, 'final')), '3.2.1final')
        self.assertEquals(versions.get_version((3, 2, 1, 'beta', 1234)), '3.2.1beta1234')

    def test_class(self):
        V = versions.Version

        v1 = V(0, 1)

        self.assertEquals(v1, (0, 1))
        self.assertEquals(str(v1), '0.1')

        v2 = V(3, 2, 1, 'final')

        self.assertEquals(v2, (3, 2, 1, 'final'))
        self.assertEquals(str(v2), '3.2.1final')

        self.assertTrue(v2 > v1)


def suite():
    suite = unittest.TestSuite()

    test_cases = [
        VersionTestCase,
    ]

    for tc in test_cases:
        suite.addTest(unittest.makeSuite(tc))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
