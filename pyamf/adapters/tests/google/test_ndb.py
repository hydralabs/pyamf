"""
Tests for PyAMF support of google.appengine.ext.ndb
"""

import datetime

import pyamf
from pyamf.adapters.tests import google


if google.has_appengine_sdk():
    from google.appengine.ext import ndb

    from . import _ndb_models as models

    adapter = pyamf.get_adapter('google.appengine.ext.ndb')


class EncodeModelTestCase(google.BaseTestCase):
    """
    Tests for encoding an L{ndb.Model} instance.
    """

    def test_simple(self):
        """
        The simplest encode possible - anonymous class, no properties
        """
        entity = models.SimpleEntity()

        self.assertEncodes(entity, (
            b'\x03\x00',
            b'\x04_key\x05\x00'
            b'\x00\t'
        ), encoding=pyamf.AMF0)

        self.assertEncodes(entity, (
            b'\n\x0b'
            b'\x01\t_key\x01'
            b'\x01'
        ), encoding=pyamf.AMF3)

    def test_simple_named_alias(self):
        """
        Register SimpleEntity as a named class.
        """
        pyamf.register_class(models.SimpleEntity, 'foo.bar')

        entity = models.SimpleEntity()

        self.assertEncodes(entity, (
            b'\x10\x00'
            b'\x07foo.bar'
            b'\x00\x04_key\x05'
            b'\x00\x00\t'
        ), encoding=pyamf.AMF0)

        self.assertEncodes(entity, (
            b'\n\x0b\x0ffoo.bar\t_key\x01\x01'
        ), encoding=pyamf.AMF3)

    def test_encode_properties(self):
        """
        An entity with various properties declared should be able to be encoded
        """
        heidi_klum = models.SuperModel(
            # ty wikipedia
            name='Heidi Klum',
            height=1.765,
            birth_date=datetime.date(1973, 6, 1),
            measurements=[1, 2, 3]
        )

        self.assertEncodes(heidi_klum, (
            b'\x03', (
                b'\x00\x04name\x02\x00\nHeidi Klum',
                b'\x00\x04_key\x05',
                b'\x00\x0cmeasurements\n\x00\x00\x00\x03\x00?\xf0\x00\x00\x00',
                b'\x00\x00\x00\x00@\x00\x00\x00\x00\x00\x00\x00\x00@\x08\x00'
                b'\x00\x00\x00\x00\x00',
                b'\x00\x06height\x00?\xfc=p\xa3\xd7\n=',
                b'\x00\nbirth_date\x0bB9\x15\xda$\x00\x00\x00\x00\x00',
                b'\x00\x0bage_in_2000\x00@:\x00\x00\x00\x00\x00\x00',
            ),
            b'\x00\x00\t'
        ), encoding=pyamf.AMF0)

        self.assertEncodes(heidi_klum, (
            b'\n\x0b\x01', (
                b'\tname\x06\x15Heidi Klum',
                b'\t_key\x01',
                b'\x19measurements\t\x07\x01\x04\x01\x04\x02\x04\x03',
                b'\rheight\x05?\xfc=p\xa3\xd7\n=',
                b'\x15birth_date\x08\x01B9\x15\xda$\x00\x00\x00',
                b'\x17age_in_2000\x04\x1a',
            ),
            b'\x01'
        ), encoding=pyamf.AMF3)

    def test_ref_model(self):
        """
        Encoding a reference to an entity must work
        """
        entity = models.SimpleEntity()

        entity.put()

        self.assertEncodes([entity, entity], (
            '\t\x05\x01',
            '\n\x0b\x01\t_key\x06]agx0ZXN0YmVkLXRlc3RyEgsSDFNpbXBsZUVudGl0eRg'
            'BDA\x01',
            '\n\x02'
        ))


class EncodeTestCase(google.BaseTestCase):
    """
    Tests for encoding various ndb related objects.
    """

    def test_key(self):
        """
        Encode an ndb.Key instance must be converted a unicode.
        """
        key = ndb.Key('SimpleEntity', 'bar')

        self.assertEncodes(key, (
            b'\x02\x002agx0ZXN0YmVkLXRlc3RyFQsSDFNpbXBsZUVudGl0eSIDYmFyDA'
        ), encoding=pyamf.AMF0)

        self.assertEncodes(key, (
            b'\x06eagx0ZXN0YmVkLXRlc3RyFQsSDFNpbXBsZUVudGl0eSIDYmFyDA'
        ), encoding=pyamf.AMF3)

    def test_query(self):
        """
        Encoding a L{ndb.Query} should be returned as a list.
        """
        query = models.SimpleEntity.query()

        self.assertIsInstance(query, ndb.Query)

        self.assertEncodes(query, (
            b'\n\x00\x00\x00\x00'
        ), encoding=pyamf.AMF0)

        self.assertEncodes(query, (
            b'\t\x01\x01'
        ), encoding=pyamf.AMF3)


class DecodeModelTestCase(google.BaseTestCase):
    """
    """

    def setUp(self):
        super(DecodeModelTestCase, self).setUp()

        pyamf.register_class(models.SuperModel, 'pyamf.SM')

    def test_amf0(self):
        data = (
            b'\x10\x00\x08pyamf.SM\x00\x04_key\x05\x00\x0bage_in_2000\x00@:'
            b'\x00\x00\x00\x00\x00\x00\x00\nbirth_date\x0bB9\x15\xda$\x00\x00'
            b'\x00\x00\x00\x00\x06height\x00?\xfc=p\xa3\xd7\n=\x00\x0cmeasurem'
            b'ents\n\x00\x00\x00\x03\x00?\xf0\x00\x00\x00\x00\x00\x00\x00@\x00'
            '\x00\x00\x00\x00\x00\x00\x00@\x08\x00\x00\x00\x00\x00\x00\x00\x04'
            'name\x02\x00\nHeidi Klum\x00\x00\t'
        )

        decoder = pyamf.decode(data, encoding=pyamf.AMF0)

        heidi = decoder.next()

        self.assertEqual(heidi, models.SuperModel(
            birth_date=datetime.date(1973, 6, 1),
            name='Heidi Klum',
            measurements=[1, 2, 3],
            height=1.765
        ))

    def test_amf3(self):
        data = (
            b'\nk\x11pyamf.SM\t_key\x17age_in_2000\x15birth_date\rheight\x19me'
            b'asurements\tname\x01\x04\x1a\x08\x01B9\x15\xda$\x00\x00\x00\x05?'
            b'\xfc=p\xa3\xd7\n=\t\x07\x01\x04\x01\x04\x02\x04\x03\x06\x15Heidi'
            b' Klum\x01'
        )

        decoder = pyamf.decode(data, encoding=pyamf.AMF3)

        heidi = decoder.next()

        self.assertEqual(heidi, models.SuperModel(
            birth_date=datetime.date(1973, 6, 1),
            name='Heidi Klum',
            measurements=[1, 2, 3],
            height=1.765
        ))
