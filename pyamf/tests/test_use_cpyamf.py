# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Ensure encoders and decoders are from cpyamf by default and
from pure python pyamf if they are gotten with disable_cpyamf true.

@since: 0.6.2
"""


import unittest


class TestUseCpyamf(unittest.TestCase):
    def test_use_cpyamf_for_amf0_decoder(self):
        """
        Ensure the amf0 decoder is from cpyamf by default.

        :return:
        """
        import pyamf
        decoder = pyamf.get_decoder(pyamf.AMF0)
        self.assertIn('cpyamf', str(decoder))
        self.assertIn('amf0', str(decoder))

    def test_use_cpyamf_for_amf3_decoder(self):
        """
        Ensure the amf3 decoder is from cpyamf by default.

        :return:
        """
        import pyamf
        decoder = pyamf.get_decoder(pyamf.AMF3)
        self.assertIn('cpyamf', str(decoder))
        self.assertIn('amf3', str(decoder))

    def test_not_use_cpyamf_for_amf0_decoder(self):
        """
        Ensure the amf0 decoder is not from cpyamf
        when the disable_cpyamf keyword arg is True.

        :return:
        """
        import pyamf
        decoder = pyamf.get_decoder(pyamf.AMF0, disable_cpyamf=True)

        self.assertNotIn('cpyamf', str(decoder))
        self.assertIn('pyamf', str(decoder))
        self.assertIn('amf0', str(decoder))

    def test_not_use_cpyamf_for_amf3_decoder(self):
        """
        Ensure the amf3 decoder is not from cpyamf
        when the disable_cpyamf keyword arg is True.

        :return:
        """
        import pyamf
        decoder = pyamf.get_decoder(pyamf.AMF3, disable_cpyamf=True)

        self.assertNotIn('cpyamf', str(decoder))
        self.assertIn('pyamf', str(decoder))
        self.assertIn('amf3', str(decoder))

    def test_use_cpyamf_for_amf0_encoder(self):
        """
        Ensure the amf0 encoder is from cpyamf by default.

        :return:
        """
        import pyamf
        decoder = pyamf.get_encoder(pyamf.AMF0)
        self.assertIn('cpyamf', str(decoder))
        self.assertIn('amf0', str(decoder))

    def test_use_cpyamf_for_amf3_encoder(self):
        """
        Ensure the amf3 encoder is from cpyamf by default.

        :return:
        """
        import pyamf
        decoder = pyamf.get_decoder(pyamf.AMF3)
        self.assertIn('cpyamf', str(decoder))
        self.assertIn('amf3', str(decoder))

    def test_not_use_cpyamf_for_amf0_encoder(self):
        """
        Ensure the amf0 encoder is not from cpyamf
        when the disable_cpyamf keyword arg is True.

        :return:
        """
        import pyamf
        decoder = pyamf.get_encoder(pyamf.AMF0, disable_cpyamf=True)

        self.assertNotIn('cpyamf', str(decoder))
        self.assertIn('pyamf', str(decoder))
        self.assertIn('amf0', str(decoder))

    def test_not_use_cpyamf_for_amf3_encoder(self):
        """
        Ensure the amf3 encoder is not from cpyamf
        when the disable_cpyamf keyword arg is True.

        :return:
        """
        import pyamf
        decoder = pyamf.get_encoder(pyamf.AMF3, disable_cpyamf=True)

        self.assertNotIn('cpyamf', str(decoder))
        self.assertIn('pyamf', str(decoder))
        self.assertIn('amf3', str(decoder))
