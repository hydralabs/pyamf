# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.

"""
Test utilities.

@since: 0.1.0
"""

import unittest
import copy

import pyamf
from pyamf.util import BufferedByteStream

PosInf = 1e300000
NegInf = -1e300000
NaN = PosInf / PosInf


class ClassicSpam:
    def __readamf__(self, input):
        pass

    def __writeamf__(self, output):
        pass


class Spam(object):
    """
    A generic object to use for object encoding.
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
        for n in self.data:
            s = n[1:]
            n = n[0]

            self.encoder.writeElement(n)

            if isinstance(s, basestring):
                testcase.assertEqual(self.getval(), s)
            elif isinstance(s, (tuple, list)):
                val = self.getval()

                if not check_buffer(val, s):
                    testcase.fail('%r != %r' % (val, s))


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
    return str(float(val)) == str(NaN)


def isPosInf(val):
    return str(float(val)) == str(PosInf)


def isNegInf(val):
    return str(float(val)) == str(NegInf)


def check_buffer(buf, parts, inner=False):
    assert isinstance(parts, (tuple, list))

    orig = buf

    parts = [p for p in parts]

    for part in parts:
        if inner is False:
            if isinstance(part, (tuple, list)):
                buf = check_buffer(buf, part, inner=True)
            else:
                if not buf.startswith(part):
                    return False

                buf = buf[len(part):]
        else:
            for k in parts[:]:
                for p in parts[:]:
                    if isinstance(p, (tuple, list)):
                        buf = check_buffer(buf, p, inner=True)
                    else:
                        if buf.startswith(p):
                            parts.remove(p)
                            buf = buf[len(p):]

            return buf

    return len(buf) == 0


def assert_buffer(testcase, val, s):
    if not check_buffer(val, s):
        testcase.fail('%r != %r' % (val, s))


def replace_dict(src, dest):
    for name in dest.keys():
        if name not in src:
            del dest[name]

            continue

        if dest[name] is not src[name]:
            dest[name] = src[name]


class BaseCodecMixIn(object):
    amf_version = pyamf.AMF0

    def setUp(self):
        self.context = pyamf.get_context(self.amf_version)
        self.stream = BufferedByteStream()


class BaseDecoderMixIn(BaseCodecMixIn):
    def setUp(self):
        BaseCodecMixIn.setUp(self)

        self.decoder = pyamf.get_decoder(
            self.amf_version, data=self.stream, context=self.context)


class BaseEncoderMixIn(BaseCodecMixIn):
    def setUp(self):
        BaseCodecMixIn.setUp(self)

        self.encoder = pyamf.get_encoder(
            self.amf_version, stream=self.stream, context=self.context)


class NullFileDescriptor(object):
    def write(self, *args, **kwargs):
        pass


def get_fqcn(klass):
    return '%s.%s' % (klass.__module__, klass.__name__)
