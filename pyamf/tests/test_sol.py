# -*- coding: utf-8 -*-
#
# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Tests for Local Shared Object (LSO) Implementation.

@since: 0.1.0
"""

import unittest
import os.path
import warnings
import tempfile

from io import BytesIO

import pyamf
from pyamf import sol
from pyamf.tests.util import check_buffer, expectedFailureIfAppengine

warnings.simplefilter('ignore', RuntimeWarning)


class DecoderTestCase(unittest.TestCase):
    def test_header(self):
        bytes = (
            b'\x00\xbf\x00\x00\x00\x15TCSO\x00\x04\x00\x00\x00\x00\x00\x05hello'
            b'\x00\x00\x00\x00'
        )

        try:
            sol.decode(bytes)
        except:
            self.fail("Error occurred during decoding stream")

    def test_invalid_header(self):
        bytes = (
            b'\x00\x00\x00\x00\x00\x15TCSO\x00\x04\x00\x00\x00\x00\x00\x05hello'
            b'\x00\x00\x00\x00'
        )
        self.assertRaises(pyamf.DecodeError, sol.decode, bytes)

    def test_invalid_header_length(self):
        bytes = (
            b'\x00\xbf\x00\x00\x00\x05TCSO\x00\x04\x00\x00\x00\x00\x00\x05hello'
            b'\x00\x00\x00\x00'
        )
        self.assertRaises(pyamf.DecodeError, sol.decode, bytes)

    def test_strict_header_length(self):
        bytes = (
            b'\x00\xbf\x00\x00\x00\x00TCSO\x00\x04\x00\x00\x00\x00\x00\x05hello'
            b'\x00\x00\x00\x00'
        )

        try:
            sol.decode(bytes, strict=False)
        except:
            self.fail("Error occurred during decoding stream")

    def test_invalid_signature(self):
        bytes = (
            b'\x00\xbf\x00\x00\x00\x15ABCD\x00\x04\x00\x00\x00\x00\x00\x05hello'
            b'\x00\x00\x00\x00'
        )
        self.assertRaises(pyamf.DecodeError, sol.decode, bytes)

    def test_invalid_header_name_length(self):
        bytes = (
            b'\x00\xbf\x00\x00\x00\x15TCSO\x00\x04\x00\x00\x00\x00\x00\x01hello'
            b'\x00\x00\x00\x00'
        )
        self.assertRaises(pyamf.DecodeError, sol.decode, bytes)

    def test_invalid_header_padding(self):
        bytes = (
            b'\x00\xbf\x00\x00\x00\x15TCSO\x00\x04\x00\x00\x00\x00\x00\x05hello'
            b'\x00\x00\x01\x00'
        )
        self.assertRaises(pyamf.DecodeError, sol.decode, bytes)

    def test_unknown_encoding(self):
        bytes = (
            b'\x00\xbf\x00\x00\x00\x15TCSO\x00\x04\x00\x00\x00\x00\x00\x05hello'
            b'\x00\x00\x00\x01'
        )
        self.assertRaises(ValueError, sol.decode, bytes)

    def test_amf3(self):
        bytes = (
            b'\x00\xbf\x00\x00\x00aTCSO\x00\x04\x00\x00\x00\x00\x00\x08'
            b'EchoTest\x00\x00\x00\x03\x0fhttpUri\x06=http://localhost:8000'
            b'/gateway/\x00\x0frtmpUri\x06+rtmp://localhost/echo\x00'
        )

        self.assertEqual(
            sol.decode(bytes), (
                u'EchoTest',
                {
                    u'httpUri': u'http://localhost:8000/gateway/',
                    u'rtmpUri': u'rtmp://localhost/echo'
                }
            )
        )


class EncoderTestCase(unittest.TestCase):
    def test_encode_header(self):
        stream = sol.encode('hello', {})

        self.assertEqual(
            stream.getvalue(),
            b'\x00\xbf\x00\x00\x00\x15TCSO\x00\x04\x00\x00\x00\x00\x00\x05hello'
            b'\x00\x00\x00\x00'
        )

    def test_multiple_values(self):
        stream = sol.encode('hello', {'name': 'value', 'spam': 'eggs'})

        self.assertTrue(
            check_buffer(stream.getvalue(), HelperTestCase.contents)
        )

    def test_amf3(self):
        bytes = (
            b'\x00\xbf\x00\x00\x00aTCSO\x00\x04\x00\x00\x00\x00\x00\x08'
            b'EchoTest\x00\x00\x00\x03', (
                b'\x0fhttpUri\x06=http://localhost:8000/gateway/\x00',
                b'\x0frtmpUri\x06+rtmp://localhost/echo\x00'
            )
        )

        stream = sol.encode(
            u'EchoTest', {
                u'httpUri': u'http://localhost:8000/gateway/',
                u'rtmpUri': u'rtmp://localhost/echo'
            },
            encoding=pyamf.AMF3
        )

        self.assertTrue(check_buffer(stream.getvalue(), bytes))


class HelperTestCase(unittest.TestCase):
    contents = (
        b'\x00\xbf\x00\x00\x002TCSO\x00\x04\x00\x00\x00\x00\x00\x05hello'
        b'\x00\x00\x00\x00', (
            b'\x00\x04name\x02\x00\x05value\x00',
            b'\x00\x04spam\x02\x00\x04eggs\x00'
        )
    )

    contents_str = (
        b'\x00\xbf\x00\x00\x002TCSO\x00\x04\x00\x00\x00\x00\x00'
        b'\x05hello\x00\x00\x00\x00\x00\x04name\x02\x00\x05value\x00\x00'
        b'\x04spam\x02\x00\x04eggs\x00')

    def setUp(self):
        try:
            self.fp, self.file_name = tempfile.mkstemp()
        except NotImplementedError:
            try:
                import google.appengine  # noqa
            except ImportError:
                raise
            else:
                self.skipTest('Not available on AppEngine')

        os.close(self.fp)

    def tearDown(self):
        if os.path.isfile(self.file_name):
            os.unlink(self.file_name)

    def _load(self):
        fp = open(self.file_name, 'wb+')

        fp.write(self.contents_str)
        fp.flush()

        return fp

    def test_load_name(self):
        fp = self._load()
        fp.close()

        s = sol.load(self.file_name)

        self.assertEqual(s.name, 'hello')
        self.assertEqual(s, {'name': 'value', 'spam': 'eggs'})

    def test_load_file(self):
        fp = self._load()
        y = fp.tell()
        fp.seek(0)

        s = sol.load(fp)

        self.assertEqual(s.name, 'hello')
        self.assertEqual(s, {'name': 'value', 'spam': 'eggs'})
        self.assertEqual(y, fp.tell())

    def test_save_name(self):
        s = sol.SOL('hello')
        s.update({'name': 'value', 'spam': 'eggs'})

        sol.save(s, self.file_name)

        fp = open(self.file_name, 'rb')

        try:
            self.assertTrue(check_buffer(fp.read(), self.contents))
        finally:
            fp.close()

    def test_save_file(self):
        fp = open(self.file_name, 'wb+')
        s = sol.SOL('hello')
        s.update({'name': 'value', 'spam': 'eggs'})

        sol.save(s, fp)
        fp.seek(0)

        self.assertFalse(fp.closed)
        self.assertTrue(check_buffer(fp.read(), self.contents))

        fp.close()


class SOLTestCase(unittest.TestCase):
    def test_create(self):
        s = sol.SOL('eggs')

        self.assertEqual(s, {})
        self.assertEqual(s.name, 'eggs')

    @expectedFailureIfAppengine
    def test_save(self):
        s = sol.SOL('hello')
        s.update({'name': 'value', 'spam': 'eggs'})

        x = BytesIO()

        s.save(x)

        self.assertTrue(check_buffer(x.getvalue(), HelperTestCase.contents))

        tmp_name = tempfile.mkstemp()[1]

        try:
            with open(tmp_name, 'wb+') as fp:
                self.assertEqual(fp.closed, False)

                s.save(fp)
                self.assertNotEqual(fp.tell(), 0)

                fp.seek(0)

                self.assertTrue(check_buffer(fp.read(), HelperTestCase.contents))
                self.assertEqual(fp.closed, False)

                with open(tmp_name, 'rb') as fp2:
                    self.assertTrue(
                        check_buffer(fp2.read(), HelperTestCase.contents)
                    )
        except:
            if os.path.isfile(tmp_name):
                os.unlink(tmp_name)

            raise
