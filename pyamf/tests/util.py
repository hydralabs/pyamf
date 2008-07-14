# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Test utilities.

@since: 0.1.0
"""

import unittest, copy, sys
import pyamf

class ClassicSpam:
    def __readamf__(self, input):
        pass

    def __writeamf__(self, output):
        pass

class Spam(object):
    """
    A generic object to use for object encoding
    """
    def __init__(self, d={}):
        self.__dict__.update(d)

    def __readamf__(self, input):
        pass

    def __writeamf__(self, output):
        pass

class ClassCacheClearingTestCase(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)

        self._class_cache = pyamf.CLASS_CACHE.copy()
        self._class_loaders = copy.copy(pyamf.CLASS_LOADERS)

    def tearDown(self):
        unittest.TestCase.tearDown(self)

        pyamf.CLASS_CACHE = self._class_cache
        pyamf.CLASS_LOADERS = self._class_loaders

class EncoderTester(object):
    """
    A helper object that takes some input, runs over the encoder
    and checks the output.
    """

    def __init__(self, encoder, data):
        self.encoder = encoder
        self.buf = encoder.stream
        self.data = data

    def getval(self):
        t = self.buf.getvalue()
        self.buf.truncate(0)

        return t

    def run(self, testcase):
        for n, s in self.data:
            self.encoder.writeElement(n)

            testcase.assertEqual(self.getval(), s)

class DecoderTester(object):
    """
    A helper object that takes some input, runs over the decoder
    and checks the output.
    """

    def __init__(self, decoder, data):
        self.decoder = decoder
        self.buf = decoder.stream
        self.data = data

    def run(self, testcase):
        for n, s in self.data:
            self.buf.truncate(0)
            self.buf.write(s)
            self.buf.seek(0)

            testcase.assertEqual(self.decoder.readElement(), n)

            if self.buf.remaining() != 0:
                from pyamf.util import hexdump

                print hexdump(self.buf.getvalue())

            # make sure that the entire buffer was consumed
            testcase.assertEqual(self.buf.remaining(), 0)

def isNaN(val):
    if sys.version_info < (2, 5) or sys.platform.startswith('win'):
        import fpconst

        return fpconst.isNaN(val)
    else:
        return str(float(val)) == 'nan'

def isPosInf(val):
    if sys.version_info < (2, 5) or sys.platform.startswith('win'):
        import fpconst

        return fpconst.isPosInf(val)
    else:
        return val == float('inf')

def isNegInf(val):
    if sys.version_info < (2, 5) or sys.platform.startswith('win'):
        import fpconst

        return fpconst.isNegInf(val)
    else:
        return val == float('-inf')


def replace_dict(src, dest):
    for name in dest.keys():
        if name not in src:
            del dest[name]

            continue

        if dest[name] is not src[name]:
            dest[name] = src[name]
