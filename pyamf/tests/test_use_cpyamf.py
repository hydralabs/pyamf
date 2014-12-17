# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Ensure cpyamf can be toggled to use or not use cpyamf versions of
amf coders.

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

    def test_use_cpyamf_for_amf3_decoder(self):
        """
        Ensure the amf3 decoder is from cpyamf by default.

        :return:
        """
        import pyamf
        decoder = pyamf.get_decoder(pyamf.AMF3)
        self.assertIn('cpyamf', str(decoder))

    def test_not_use_cpyamf_for_amf0_decoder(self):
        """
        Ensure the amf0 decoder is not from cpyamf
        when pyamf.USE_CPYAMF is False.

        :return:
        """
        import pyamf
        decoder = pyamf.get_decoder(pyamf.AMF0, disable_cpyamf=True)

        self.assertNotIn('cpyamf', str(decoder))
        self.assertIn('pyamf', str(decoder))

    def test_not_use_cpyamf_for_amf3_decoder(self):
        """
        Ensure the amf3 decoder is not from cpyamf
        when pyamf.USE_CPYAMF is False.

        :return:
        """
        import pyamf
        decoder = pyamf.get_decoder(pyamf.AMF3, disable_cpyamf=True)

        self.assertNotIn('cpyamf', str(decoder))
        self.assertIn('pyamf', str(decoder))

    def test_use_cpyamf_for_amf0_encoder(self):
        """
        Ensure the amf0 encoder is from cpyamf by default.

        :return:
        """
        import pyamf
        decoder = pyamf.get_encoder(pyamf.AMF0)
        self.assertIn('cpyamf', str(decoder))

    def test_use_cpyamf_for_amf3_encoder(self):
        """
        Ensure the amf3 encoder is from cpyamf by default.

        :return:
        """
        import pyamf
        decoder = pyamf.get_decoder(pyamf.AMF3)
        self.assertIn('cpyamf', str(decoder))

    def test_not_use_cpyamf_for_amf0_encoder(self):
        """
        Ensure the amf0 encoder is not from cpyamf
        when pyamf.USE_CPYAMF is False.

        :return:
        """
        import pyamf
        decoder = pyamf.get_encoder(pyamf.AMF0, disable_cpyamf=True)

        self.assertNotIn('cpyamf', str(decoder))
        self.assertIn('pyamf', str(decoder))

    def test_not_use_cpyamf_for_amf3_encoder(self):
        """
        Ensure the amf3 encoder is not from cpyamf
        when pyamf.USE_CPYAMF is False.

        :return:
        """
        import pyamf
        decoder = pyamf.get_encoder(pyamf.AMF3, disable_cpyamf=True)

        self.assertNotIn('cpyamf', str(decoder))
        self.assertIn('pyamf', str(decoder))
