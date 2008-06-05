# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
PyAMF Google adapter tests.

@since: 0.3.1
"""

import unittest, datetime

from google.appengine.ext import db

import pyamf

class EncodeDbTestCase(unittest.TestCase):
    def test_model(self):
        # 'borrowed' from http://code.google.com/appengine/docs/datastore/entitiesandmodels.html
        class Pet(db.Model):
            name = db.StringProperty(required=True)
            type = db.StringProperty(required=True, choices=set(["cat", "dog", "bird"]))
            birthdate = db.DateProperty()
            weight_in_pounds = db.IntegerProperty()
            spayed_or_neutered = db.BooleanProperty()

        jessica = Pet(name='Jessica', type='cat')
        jessica.birthdate = datetime.date(1986, 10, 2)
        jessica.weight_in_pounds = 5
        jessica.spayed_or_neutered = False

        encoder = pyamf.get_encoder(pyamf.AMF0)

        encoder.writeElement(jessica)
        self.assertEquals(encoder.stream.getvalue(),
            '\x03\x00\x10weight_in_pounds\x00@\x14\x00\x00\x00\x00\x00\x00'
            '\x00\x04type\x02\x00\x03cat\x00\x04name\x02\x00\x07Jessica\x00'
            '\tbirthdate\x0bB^\xc4\xae\xaa\x00\x00\x00\x00\x00\x00\x12'
            'spayed_or_neutered\x01\x00\x00\x00\t')

        encoder = pyamf.get_encoder(pyamf.AMF3)
        encoder.writeElement(jessica)
        self.assertEquals(encoder.stream.getvalue(),
            '\n\x0b\x01!weight_in_pounds\x04\x05\ttype\x06\x07cat\tname\x06'
            '\x0fJessica\x13birthdate\x08\x01B^\xc4\xae\xaa\x00\x00\x00%'
            'spayed_or_neutered\x02\x01')

    def test_expando(self):
        # 'borrowed' from http://code.google.com/appengine/docs/datastore/entitiesandmodels.html
        class Pet(db.Expando):
            name = db.StringProperty(required=True)
            type = db.StringProperty(required=True, choices=set(["cat", "dog", "bird"]))
            birthdate = db.DateProperty()
            weight_in_pounds = db.IntegerProperty()
            spayed_or_neutered = db.BooleanProperty()

        jessica = Pet(name='Jessica', type='cat')
        jessica.birthdate = datetime.date(1986, 10, 2)
        jessica.weight_in_pounds = 5
        jessica.spayed_or_neutered = False
        jessica.foo = 'bar'

        encoder = pyamf.get_encoder(pyamf.AMF0)

        encoder.writeElement(jessica)
        self.assertEquals(encoder.stream.getvalue(),
            '\x03\x00\x04name\x02\x00\x07Jessica\x00\tbirthdate\x0bB^\xc4\xae'
            '\xaa\x00\x00\x00\x00\x00\x00\x10weight_in_pounds\x00@\x14\x00'
            '\x00\x00\x00\x00\x00\x00\x03foo\x02\x00\x03bar\x00\x04type\x02'
            '\x00\x03cat\x00\x12spayed_or_neutered\x01\x00\x00\x00\t')

        encoder = pyamf.get_encoder(pyamf.AMF3)
        encoder.writeElement(jessica)
        self.assertEquals(encoder.stream.getvalue(),
            '\n\x0b\x01\tname\x06\x0fJessica\x13birthdate\x08\x01B^\xc4\xae'
            '\xaa\x00\x00\x00!weight_in_pounds\x04\x05\x07foo\x06\x07bar\t'
            'type\x06\x07cat%spayed_or_neutered\x02\x01')


def suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(EncodeDbTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
