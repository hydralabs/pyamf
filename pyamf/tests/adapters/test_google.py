# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE for details.

"""
PyAMF Google adapter tests.

@since: 0.3.1
"""

import unittest, datetime, struct

from google.appengine.ext import db

import pyamf
from pyamf import amf3
from pyamf.tests.util import ClassCacheClearingTestCase, Spam

from pyamf.adapters import _google_appengine_ext_db as adapter_db

# 'borrowed' from http://code.google.com/appengine/docs/datastore/entitiesandmodels.html
class PetModel(db.Model):
    name = db.StringProperty(required=True)
    type = db.StringProperty(required=True, choices=set(["cat", "dog", "bird"]))
    birthdate = db.DateProperty()
    weight_in_pounds = db.IntegerProperty()
    spayed_or_neutered = db.BooleanProperty()

class PetExpando(db.Expando):
    name = db.StringProperty(required=True)
    type = db.StringProperty(required=True, choices=set(["cat", "dog", "bird"]))
    birthdate = db.DateProperty()
    weight_in_pounds = db.IntegerProperty()
    spayed_or_neutered = db.BooleanProperty()

class EncodingModelTestCase(ClassCacheClearingTestCase):
    def setUp(self):
        ClassCacheClearingTestCase.setUp(self)

        self.jessica = PetModel(name='Jessica', type='cat')
        self.jessica.birthdate = datetime.date(1986, 10, 2)
        self.jessica.weight_in_pounds = 5
        self.jessica.spayed_or_neutered = False

    def tearDown(self):
        ClassCacheClearingTestCase.tearDown(self)

        try:
            self.jessica.delete()
        except:
            pass

    def test_amf0(self):
        encoder = pyamf.get_encoder(pyamf.AMF0)
        context = encoder.context

        alias = context.getClassAlias(PetModel)
        self.assertEquals(alias.__class__, adapter_db.DataStoreClassAlias)

        encoder.writeElement(self.jessica)
        self.assertEquals(encoder.stream.getvalue(),
            '\x03\x00\x10weight_in_pounds\x00@\x14\x00\x00\x00\x00\x00\x00\x00'
            '\x04name\x02\x00\x07Jessica\x00\x04_key\x05\x00\x04type\x02\x00'
            '\x03cat\x00\tbirthdate\x0bB^\xc4\xae\xaa\x00\x00\x00\x00\x00\x00'
            '\x12spayed_or_neutered\x01\x00\x00\x00\t')

    def test_amf3(self):
        encoder = pyamf.get_encoder(pyamf.AMF3)
        encoder.writeElement(self.jessica)
        self.assertEquals(encoder.stream.getvalue(),
            '\nk\x01\t_key!weight_in_pounds\ttype\tname\x13birthdate%'
            'spayed_or_neutered\x01\x04\x05\x06\x07cat\x06\x0fJessica\x08\x01'
            'B^\xc4\xae\xaa\x00\x00\x00\x02\x01')

    def test_save_amf0(self):
        self.jessica.put()

        k = str(self.jessica.key())
        encoder = pyamf.get_encoder(pyamf.AMF0)
        encoder.writeElement(self.jessica)

        self.assertEquals(encoder.stream.getvalue(),
            '\x03\x00\x10weight_in_pounds\x00@\x14\x00\x00\x00\x00\x00\x00\x00'
            '\x04name\x02\x00\x07Jessica\x00\x04_key\x02%s%s\x00\x04type\x02'
            '\x00\x03cat\x00\tbirthdate\x0bB^\xc4\xae\xaa\x00\x00\x00\x00\x00'
            '\x00\x12spayed_or_neutered\x01\x00\x00\x00\t' % (
            struct.pack('>H' ,len(k)), k))

    def test_save_amf3(self):
        self.jessica.put()

        k = str(self.jessica.key())
        encoder = pyamf.get_encoder(pyamf.AMF3)
        encoder.writeElement(self.jessica)

        self.assertEquals(encoder.stream.getvalue(),
            '\nk\x01\t_key!weight_in_pounds\ttype\tname\x13birthdate%%'
            'spayed_or_neutered\x06%s%s\x04\x05\x06\x07cat\x06\x0fJessica'
            '\x08\x01B^\xc4\xae\xaa\x00\x00\x00\x02\x01' % (
                amf3._encode_int(len(k) << 1 | amf3.REFERENCE_BIT), k
            ))

    def test_alias_amf0(self):
        pyamf.register_class(PetModel, 'Pet')
        encoder = pyamf.get_encoder(pyamf.AMF0)

        encoder.writeElement(self.jessica)
        self.assertEquals(encoder.stream.getvalue(),
            '\x10\x00\x03Pet\x00\x10weight_in_pounds\x00@\x14\x00\x00\x00\x00'
            '\x00\x00\x00\x04name\x02\x00\x07Jessica\x00\x04_key\x05\x00\x04'
            'type\x02\x00\x03cat\x00\tbirthdate\x0bB^\xc4\xae\xaa\x00\x00\x00'
            '\x00\x00\x00\x12spayed_or_neutered\x01\x00\x00\x00\t')

    def test_alias_amf3(self):
        pyamf.register_class(PetModel, 'Pet')
        encoder = pyamf.get_encoder(pyamf.AMF3)
        encoder.writeElement(self.jessica)

        self.assertEquals(encoder.stream.getvalue(),
            '\nk\x07Pet\t_key!weight_in_pounds\ttype\tname\x13birthdate%'
            'spayed_or_neutered\x01\x04\x05\x06\x07cat\x06\x0fJessica\x08\x01'
            'B^\xc4\xae\xaa\x00\x00\x00\x02\x01')

class EncodingExpandoTestCase(ClassCacheClearingTestCase):
    def setUp(self):
        ClassCacheClearingTestCase.setUp(self)

        self.jessica = PetExpando(name='Jessica', type='cat')
        self.jessica.birthdate = datetime.date(1986, 10, 2)
        self.jessica.weight_in_pounds = 5
        self.jessica.spayed_or_neutered = False
        self.jessica.foo = 'bar'

    def tearDown(self):
        ClassCacheClearingTestCase.tearDown(self)

        try:
            self.jessica.delete()
        except:
            pass

    def test_amf0(self):
        encoder = pyamf.get_encoder(pyamf.AMF0)
        encoder.writeElement(self.jessica)

        self.assertEquals(encoder.stream.getvalue(),
            '\x03\x00\x10weight_in_pounds\x00@\x14\x00\x00\x00\x00\x00\x00'
            '\x00\x04name\x02\x00\x07Jessica\x00\x04_key\x05\x00\x03foo\x02'
            '\x00\x03bar\x00\x04type\x02\x00\x03cat\x00\tbirthdate'
            '\x0bB^\xc4\xae\xaa\x00\x00\x00\x00\x00\x00\x12spayed_or_neutered'
            '\x01\x00\x00\x00\t')

    def test_amf3(self):
        encoder = pyamf.get_encoder(pyamf.AMF3)
        encoder.writeElement(self.jessica)

        self.assertEquals(encoder.stream.getvalue(),
            '\nk\x01\t_key!weight_in_pounds\ttype\tname\x13birthdate%'
            'spayed_or_neutered\x01\x04\x05\x06\x07cat\x06\x0fJessica\x08\x01'
            'B^\xc4\xae\xaa\x00\x00\x00\x02\x07foo\x06\x07bar\x01')

    def test_save_amf0(self):
        self.jessica.put()

        k = str(self.jessica.key())
        encoder = pyamf.get_encoder(pyamf.AMF0)
        encoder.writeElement(self.jessica)

        self.assertEquals(encoder.stream.getvalue(),
            '\x03\x00\x10weight_in_pounds\x00@\x14\x00\x00\x00\x00\x00\x00\x00'
            '\x04name\x02\x00\x07Jessica\x00\x04_key\x02%s%s\x00\x03foo\x02'
            '\x00\x03bar\x00\x04type\x02\x00\x03cat\x00\tbirthdate\x0bB^'
            '\xc4\xae\xaa\x00\x00\x00\x00\x00\x00\x12spayed_or_neutered\x01'
            '\x00\x00\x00\t' % (struct.pack('>H', len(k)), k))

    def test_save_amf3(self):
        self.jessica.put()

        k = str(self.jessica.key())
        encoder = pyamf.get_encoder(pyamf.AMF3)
        encoder.writeElement(self.jessica)

        self.assertEquals(encoder.stream.getvalue(),
            '\nk\x01\t_key!weight_in_pounds\ttype\tname\x13birthdate%%'
            'spayed_or_neutered\x06%s%s\x04\x05\x06\x07cat\x06\x0fJessica'
            '\x08\x01B^\xc4\xae\xaa\x00\x00\x00\x02\x07foo\x06\x07bar\x01' % (
                amf3._encode_int(len(k) << 1 | amf3.REFERENCE_BIT), k
            ))

    def test_alias_amf0(self):
        pyamf.register_class(PetExpando, 'Pet')
        encoder = pyamf.get_encoder(pyamf.AMF0)

        encoder.writeElement(self.jessica)
        self.assertEquals(encoder.stream.getvalue(),
            '\x10\x00\x03Pet\x00\x10weight_in_pounds\x00@\x14\x00\x00\x00\x00'
            '\x00\x00\x00\x04name\x02\x00\x07Jessica\x00\x04_key\x05\x00\x03'
            'foo\x02\x00\x03bar\x00\x04type\x02\x00\x03cat\x00\tbirthdate'
            '\x0bB^\xc4\xae\xaa\x00\x00\x00\x00\x00\x00\x12spayed_or_neutered'
            '\x01\x00\x00\x00\t')

    def test_alias_amf3(self):
        pyamf.register_class(PetExpando, 'Pet')
        encoder = pyamf.get_encoder(pyamf.AMF3)
        encoder.writeElement(self.jessica)

        self.assertEquals(encoder.stream.getvalue(),
            '\nk\x07Pet\t_key!weight_in_pounds\ttype\tname\x13birthdate%'
            'spayed_or_neutered\x01\x04\x05\x06\x07cat\x06\x0fJessica\x08\x01'
            'B^\xc4\xae\xaa\x00\x00\x00\x02\x07foo\x06\x07bar\x01')

class EncodingReferencesTestCase(ClassCacheClearingTestCase):
    """
    This test case refers to
    L{db.ReferenceProperty<http://code.google.com/appengine/docs/datastore/typesandpropertyclasses.html#ReferenceProperty>},
    not AMF references
    """

    def test_model(self):
        class Author(db.Model):
            name = db.StringProperty()

        class Novel(db.Model):
            title = db.StringProperty()
            author = db.ReferenceProperty(Author)

        a = Author(name='Jane Austen')
        a.put()
        k = str(a.key())

        b = Novel(title='Sense and Sensibility', author=a)

        self.assertEquals(b.author, a)

        try:
            encoder = pyamf.get_encoder(pyamf.AMF0)

            encoder.writeElement(b)
            self.assertEquals(encoder.stream.getvalue(),
                '\x03\x00\x04_key\x05\x00\x06author\x03\x00\x04_key\x02%s%s'
                '\x00\x04name\x02\x00\x0bJane Austen\x00\x00\t\x00\x05title'
                '\x02\x00\x15Sense and Sensibility\x00\x00\t' % (
                    struct.pack('>H', len(k)), k))

            encoder = pyamf.get_encoder(pyamf.AMF3)

            encoder.writeElement(b)
            self.assertEquals(encoder.stream.getvalue(),
                '\n;\x01\t_key\rauthor\x0btitle\x01\n+\x01\x00\tname\x06%s%s'
                '\x06\x17Jane Austen\x01\x06+Sense and Sensibility\x01' % (
                    amf3._encode_int(len(k) << 1 | amf3.REFERENCE_BIT), k))

            # now test with aliases ..
            pyamf.register_class(Author, 'Author')
            pyamf.register_class(Novel, 'Novel')

            encoder = pyamf.get_encoder(pyamf.AMF0)

            encoder.writeElement(b)
            self.assertEquals(encoder.stream.getvalue(), '\x10\x00\x05Novel'
                '\x00\x04_key\x05\x00\x06author\x10\x00\x06Author\x00\x04_key'
                '\x02%s%s\x00\x04name\x02\x00\x0bJane Austen\x00\x00\t\x00'
                '\x05title\x02\x00\x15Sense and Sensibility\x00\x00\t' % (
                    struct.pack('>H', len(k)), k))

            encoder = pyamf.get_encoder(pyamf.AMF3)

            encoder.writeElement(b)
            self.assertEquals(encoder.stream.getvalue(), '\n;\x0bNovel\t_key'
                '\rauthor\x0btitle\x01\n+\rAuthor\x02\tname\x06%s%s\x06\x17'
                'Jane Austen\x01\x06+Sense and Sensibility\x01' % (
                    amf3._encode_int(len(k) << 1 | amf3.REFERENCE_BIT), k))
        except:
            a.delete()
            raise

        a.delete()

    def test_expando(self):
        class Author(db.Expando):
            name = db.StringProperty()

        class Novel(db.Expando):
            title = db.StringProperty()
            author = db.ReferenceProperty(Author)

        a = Author(name='Jane Austen')
        a.put()
        k = str(a.key())

        b = Novel(title='Sense and Sensibility', author=a)

        self.assertEquals(b.author, a)

        try:
            encoder = pyamf.get_encoder(pyamf.AMF0)

            encoder.writeElement(b)
            self.assertEquals(encoder.stream.getvalue(),
                '\x03\x00\x04_key\x05\x00\x06author\x03\x00\x04_key\x02%s%s'
                '\x00\x04name\x02\x00\x0bJane Austen\x00\x00\t\x00\x05title'
                '\x02\x00\x15Sense and Sensibility\x00\x00\t' % (
                    struct.pack('>H', len(k)), k))

            encoder = pyamf.get_encoder(pyamf.AMF3)

            encoder.writeElement(b)
            self.assertEquals(encoder.stream.getvalue(),
                '\n;\x01\t_key\rauthor\x0btitle\x01\n+\x01\x00\tname\x06%s%s'
                '\x06\x17Jane Austen\x01\x06+Sense and Sensibility\x01' % (
                    amf3._encode_int(len(k) << 1 | amf3.REFERENCE_BIT), k))

            # now test with aliases ..
            pyamf.register_class(Author, 'Author')
            pyamf.register_class(Novel, 'Novel')

            encoder = pyamf.get_encoder(pyamf.AMF0)

            encoder.writeElement(b)
            self.assertEquals(encoder.stream.getvalue(), '\x10\x00\x05Novel'
                '\x00\x04_key\x05\x00\x06author\x10\x00\x06Author\x00\x04_key'
                '\x02%s%s\x00\x04name\x02\x00\x0bJane Austen\x00\x00\t\x00'
                '\x05title\x02\x00\x15Sense and Sensibility\x00\x00\t' % (
                    struct.pack('>H', len(k)), k))

            encoder = pyamf.get_encoder(pyamf.AMF3)

            encoder.writeElement(b)
            self.assertEquals(encoder.stream.getvalue(),
                '\n;\x0bNovel\t_key\rauthor\x0btitle\x01\n+\rAuthor\x02\tname'
                '\x06%s%s\x06\x17Jane Austen\x01\x06+Sense and Sensibility'
                '\x01' % (amf3._encode_int(len(k) << 1 | amf3.REFERENCE_BIT), k))
        except:
            a.delete()
            raise

        a.delete()

class ListModel(db.Model):
    numbers = db.ListProperty(long)

class ListPropertyTestCase(ClassCacheClearingTestCase):
    def test_encode(self):
        obj = ListModel()
        obj.numbers = [2, 4, 6, 8, 10]

        encoder = pyamf.get_encoder(pyamf.AMF0)

        encoder.writeElement(obj)
        self.assertEquals(encoder.stream.getvalue(),
            '\x03\x00\x04_key\x05\x00\x07numbers\n\x00\x00\x00\x05\x00@'
            '\x00\x00\x00\x00\x00\x00\x00\x00@\x10\x00\x00\x00\x00\x00\x00'
            '\x00@\x18\x00\x00\x00\x00\x00\x00\x00@ \x00\x00\x00\x00\x00\x00'
            '\x00@$\x00\x00\x00\x00\x00\x00\x00\x00\t')

        encoder = pyamf.get_encoder(pyamf.AMF3)

        encoder.writeElement(obj)
        self.assertEquals(encoder.stream.getvalue(),
            '\n+\x01\t_key\x0fnumbers\x01\t\x0b\x01\x04\x02\x04\x04\x04\x06'
            '\x04\x08\x04\n\x01')

        pyamf.register_class(ListModel, 'list-model')

        encoder = pyamf.get_encoder(pyamf.AMF0)

        encoder.writeElement(obj)
        self.assertEquals(encoder.stream.getvalue(),
            '\x10\x00\nlist-model\x00\x04_key\x05\x00\x07numbers\n\x00\x00'
            '\x00\x05\x00@\x00\x00\x00\x00\x00\x00\x00\x00@\x10\x00\x00\x00'
            '\x00\x00\x00\x00@\x18\x00\x00\x00\x00\x00\x00\x00@ \x00\x00\x00'
            '\x00\x00\x00\x00@$\x00\x00\x00\x00\x00\x00\x00\x00\t')

        encoder = pyamf.get_encoder(pyamf.AMF3)

        encoder.writeElement(obj)
        self.assertEquals(encoder.stream.getvalue(),
            '\n+\x15list-model\t_key\x0fnumbers\x01\t\x0b\x01\x04\x02\x04\x04'
            '\x04\x06\x04\x08\x04\n\x01')

    def test_decode(self):
        pyamf.register_class(ListModel, 'list-model')

        decoder = pyamf.get_decoder(pyamf.AMF0)
        decoder.stream.write(
            '\x10\x00\nlist-model\x00\x07numbers\n\x00\x00'
            '\x00\x05\x00@\x00\x00\x00\x00\x00\x00\x00\x00@\x10\x00\x00\x00'
            '\x00\x00\x00\x00@\x18\x00\x00\x00\x00\x00\x00\x00@ \x00\x00'
            '\x00\x00\x00\x00\x00@$\x00\x00\x00\x00\x00\x00\x00\x00\t')
        decoder.stream.seek(0)

        x = decoder.readElement()

        self.assertTrue(isinstance(x, ListModel))
        self.assertTrue(hasattr(x, 'numbers'))
        self.assertEquals(x.numbers, [2, 4, 6, 8, 10])

        decoder = pyamf.get_decoder(pyamf.AMF3)
        decoder.stream.write(
            '\n\x0b\x15list-model\x0fnumbers\t\x0b\x01\x04\x02\x04'
            '\x04\x04\x06\x04\x08\x04\n\x01')
        decoder.stream.seek(0)

        x = decoder.readElement()

        self.assertTrue(isinstance(x, ListModel))
        self.assertTrue(hasattr(x, 'numbers'))
        self.assertEquals(x.numbers, [2, 4, 6, 8, 10])

    def test_none(self):
        pyamf.register_class(ListModel, 'list-model')

        decoder = pyamf.get_decoder(pyamf.AMF0)
        decoder.stream.write(
            '\x10\x00\nlist-model\x00\x07numbers\x05\x00\x00\t')
        decoder.stream.seek(0)

        x = decoder.readElement()

        self.assertEquals(x.numbers, [])

class DecodingModelTestCase(ClassCacheClearingTestCase):
    def setUp(self):
        ClassCacheClearingTestCase.setUp(self)

        pyamf.register_class(PetModel, 'Pet')

        self.jessica = PetModel(name='Jessica', type='cat')
        self.jessica.birthdate = datetime.date(1986, 10, 2)
        self.jessica.weight_in_pounds = 5
        self.jessica.spayed_or_neutered = False

        self.jessica.put()
        self.key = str(self.jessica.key())

    def tearDown(self):
        ClassCacheClearingTestCase.tearDown(self)

        self.jessica.delete()

    def test_amf0(self):
        d = pyamf.get_decoder(pyamf.AMF0)
        b = d.stream

        b.write('\x10\x00\x03Pet\x00\x04_key\x02%s%s\x00\x04type\x02\x00\x03'
            'cat\x00\x10weight_in_pounds\x00@\x14\x00\x00\x00\x00\x00\x00\x00'
            '\x04name\x02\x00\x07Jessica\x00\tbirthdate\x0bB^\xc4\xae\xaa\x00'
            '\x00\x00\x00\x00\x00\x12spayed_or_neutered\x01\x00\x00\x00\t' % (
                struct.pack('>H', len(self.key)), self.key))

        b.seek(0)
        x = d.readElement()

        self.assertTrue(isinstance(x, PetModel))
        self.assertEquals(x.__class__, PetModel)

        self.assertEquals(x.type, self.jessica.type)
        self.assertEquals(x.weight_in_pounds, self.jessica.weight_in_pounds)
        self.assertEquals(x.birthdate, self.jessica.birthdate)
        self.assertEquals(x.spayed_or_neutered, self.jessica.spayed_or_neutered)

        # now check db.Model internals
        self.assertEquals(x.key(), self.jessica.key())
        self.assertEquals(x.kind(), self.jessica.kind())
        self.assertEquals(x.parent(), self.jessica.parent())
        self.assertEquals(x.parent_key(), self.jessica.parent_key())
        self.assertTrue(x.is_saved())

    def test_amf3(self):
        d = pyamf.get_decoder(pyamf.AMF3)
        b = d.stream

        b.write('\n\x0b\x07Pet\tname\x06\x0fJessica\t_key\x06%s%s\x13birthdate'
            '\x08\x01B^\xc4\xae\xaa\x00\x00\x00!weight_in_pounds\x04\x05\x07'
            'foo\x06\x07bar\ttype\x06\x07cat%%spayed_or_neutered\x02\x01' % (
                amf3._encode_int(len(self.key) << 1 | amf3.REFERENCE_BIT), self.key))

        b.seek(0)
        x = d.readElement()

        self.assertTrue(isinstance(x, PetModel))
        self.assertEquals(x.__class__, PetModel)

        self.assertEquals(x.type, self.jessica.type)
        self.assertEquals(x.weight_in_pounds, self.jessica.weight_in_pounds)
        self.assertEquals(x.birthdate, self.jessica.birthdate)
        self.assertEquals(x.spayed_or_neutered, self.jessica.spayed_or_neutered)

        # now check db.Model internals
        self.assertEquals(x.key(), self.jessica.key())
        self.assertEquals(x.kind(), self.jessica.kind())
        self.assertEquals(x.parent(), self.jessica.parent())
        self.assertEquals(x.parent_key(), self.jessica.parent_key())
        self.assertTrue(x.is_saved())

class DecodingExpandoTestCase(ClassCacheClearingTestCase):
    def setUp(self):
        ClassCacheClearingTestCase.setUp(self)

        pyamf.register_class(PetExpando, 'Pet')

        self.jessica = PetExpando(name='Jessica', type='cat')
        #self.jessica.birthdate = datetime.date(1986, 10, 2)
        self.jessica.weight_in_pounds = 5
        self.jessica.spayed_or_neutered = False
        self.jessica.foo = 'bar'

        self.jessica.put()
        self.key = str(self.jessica.key())

    def tearDown(self):
        ClassCacheClearingTestCase.tearDown(self)

        self.jessica.delete()

    def test_amf0(self):
        d = pyamf.get_decoder(pyamf.AMF0)
        b = d.stream

        b.write('\x10\x00\x03Pet\x00\x04_key\x02%s%s\x00\x04type\x02\x00\x03'
            'cat\x00\x10weight_in_pounds\x00@\x14\x00\x00\x00\x00\x00\x00\x00'
            '\x04name\x02\x00\x07Jessica\x00\tbirthdate\x0bB^\xc4\xae\xaa\x00'
            '\x00\x00\x00\x00\x00\x12spayed_or_neutered\x01\x00\x00\x00\t' % (
                struct.pack('>H', len(self.key)), self.key))

        b.seek(0)
        x = d.readElement()

        self.assertTrue(isinstance(x, PetExpando))
        self.assertEquals(x.__class__, PetExpando)

        self.assertEquals(x.type, self.jessica.type)
        self.assertEquals(x.weight_in_pounds, self.jessica.weight_in_pounds)
        self.assertEquals(x.birthdate, datetime.date(1986, 10, 2))
        self.assertEquals(x.spayed_or_neutered, self.jessica.spayed_or_neutered)

        # now check db.Expando internals
        self.assertEquals(x.key(), self.jessica.key())
        self.assertEquals(x.kind(), self.jessica.kind())
        self.assertEquals(x.parent(), self.jessica.parent())
        self.assertEquals(x.parent_key(), self.jessica.parent_key())
        self.assertTrue(x.is_saved())

    def test_amf3(self):
        d = pyamf.get_decoder(pyamf.AMF3)
        b = d.stream

        b.write('\n\x0b\x07Pet\tname\x06\x0fJessica\t_key\x06%s%s\x13birthdate'
            '\x08\x01B^\xc4\xae\xaa\x00\x00\x00!weight_in_pounds\x04\x05\x07'
            'foo\x06\x07bar\ttype\x06\x07cat%%spayed_or_neutered\x02\x01' % (
                amf3._encode_int(len(self.key) << 1 | amf3.REFERENCE_BIT), self.key))

        b.seek(0)
        x = d.readElement()

        self.assertTrue(isinstance(x, PetExpando))
        self.assertEquals(x.__class__, PetExpando)

        self.assertEquals(x.type, self.jessica.type)
        self.assertEquals(x.weight_in_pounds, self.jessica.weight_in_pounds)
        self.assertEquals(x.birthdate, datetime.date(1986, 10, 2))
        self.assertEquals(x.spayed_or_neutered, self.jessica.spayed_or_neutered)

        # now check db.Expando internals
        self.assertEquals(x.key(), self.jessica.key())
        self.assertEquals(x.kind(), self.jessica.kind())
        self.assertEquals(x.parent(), self.jessica.parent())
        self.assertEquals(x.parent_key(), self.jessica.parent_key())
        self.assertTrue(x.is_saved())

class ClassAliasTestCase(unittest.TestCase):
    def setUp(self):
        self.alias = adapter_db.DataStoreClassAlias(PetModel, 'foo.bar')

        self.jessica = PetModel(name='Jessica', type='cat')
        self.jessica_expando = PetExpando(name='Jessica', type='cat')
        self.jessica_expando.foo = 'bar'

    def tearDown(self):
        try:
            self.jessica.delete()
        except:
            pass

        if self.jessica_expando.is_saved():
            self.jessica_expando.delete()

    def test_create_instance(self):
        x = self.alias.createInstance()

        self.assertTrue(isinstance(x, adapter_db.ModelStub))

        #for y in adapter_db.DataStoreClassAlias.INTERNAL_ATTRS:
        #    self.assertEquals(None, getattr(x, y))

        self.assertTrue(hasattr(x, 'klass'))
        self.assertEquals(x.klass, self.alias.klass)

        # test some stub functions
        self.assertEquals(x.properties(), self.alias.klass.properties())
        self.assertEquals(x.dynamic_properties(), [])

    def test_apply(self):
        x = self.alias.createInstance()

        self.assertTrue(hasattr(x, 'klass'))

        self.alias.applyAttributes(x, {
            adapter_db.DataStoreClassAlias.KEY_ATTR: None,
            'name': 'Jessica',
            'type': 'cat'
        })

        self.assertFalse(hasattr(x, 'klass'))

    def test_get_attrs(self):
        self.assertEquals(self.alias.getAttrs(self.jessica), (
            # static attributes
            ['_key', 'weight_in_pounds', 'type', 'name', 'birthdate',
                'spayed_or_neutered'],
            # dynamic attributes
            []
        ))

    def test_get_attrs_expando(self):
        self.assertEquals(self.alias.getAttrs(self.jessica_expando), (
            # static attributes
            ['_key', 'weight_in_pounds', 'type', 'name', 'birthdate',
                'spayed_or_neutered'],
            # dynamic attributes
            ['foo']
        ))

    def test_get_attributes(self):
        sa, da = self.alias.getAttributes(self.jessica)

        self.assertEquals(sa, {
            'name': 'Jessica',
            '_key': None,
            'birthdate': None,
            'weight_in_pounds': None,
            'type': 'cat',
            'spayed_or_neutered': None
        })

        self.assertEquals(da, {})

    def test_get_attributes_saved(self):
        self.jessica.put()

        sa, da = self.alias.getAttributes(self.jessica)

        self.assertEquals(sa, {
            'name': 'Jessica',
            '_key': str(self.jessica.key()),
            'birthdate': None,
            'weight_in_pounds': None,
            'type': 'cat',
            'spayed_or_neutered': None
        })

        self.assertEquals(da, {})

    def test_get_attributes_expando(self):
        sa, da = self.alias.getAttributes(self.jessica_expando)

        self.assertEquals(sa, {
            'name': 'Jessica',
            '_key': None,
            'birthdate': None,
            'weight_in_pounds': None,
            'type': 'cat',
            'spayed_or_neutered': None
        })

        self.assertEquals(da, {
            'foo': 'bar'
        })

    def test_get_attributes_saved_expando(self):
        self.jessica_expando.put()

        sa, da = self.alias.getAttributes(self.jessica_expando)

        self.assertEquals(sa, {
            'name': 'Jessica',
            '_key': str(self.jessica_expando.key()),
            'birthdate': None,
            'weight_in_pounds': None,
            'type': 'cat',
            'spayed_or_neutered': None
        })

        self.assertEquals(da, {
            'foo': 'bar'
        })

class ReferencesTestCase(ClassCacheClearingTestCase):
    def setUp(self):
        ClassCacheClearingTestCase.setUp(self)

        self.jessica = PetModel(name='Jessica', type='cat')
        self.jessica.birthdate = datetime.date(1986, 10, 2)
        self.jessica.weight_in_pounds = 5
        self.jessica.spayed_or_neutered = False

        self.jessica.save()

        self.jessica2 = PetModel.all().filter('name', 'Jessica').get()

        self.assertNotEquals(id(self.jessica), id(self.jessica2))
        self.assertEquals(str(self.jessica.key()), str(self.jessica2.key()))

    def tearDown(self):
        ClassCacheClearingTestCase.tearDown(self)
        self.jessica.delete()

    def test_amf0(self):
        encoder = pyamf.get_encoder(pyamf.AMF0)
        context = encoder.context
        stream = encoder.stream
        s = str(self.jessica.key())

        self.assertFalse(hasattr(context, 'gae_objects'))

        encoder.writeObject(self.jessica)

        self.assertTrue(hasattr(context, 'gae_objects'))
        self.assertEquals(context.gae_objects, {PetModel: {s: self.jessica}})
        self.assertEquals(stream.getvalue(), '\x03\x00\x10weight_in_pounds'
            '\x00@\x14\x00\x00\x00\x00\x00\x00\x00\x04name\x02\x00\x07Jessica'
            '\x00\x04_key\x02%s%s\x00\x04type\x02\x00\x03cat\x00\tbirthdate'
            '\x0bB^\xc4\xae\xaa\x00\x00\x00\x00\x00\x00\x12spayed_or_neutered'
            '\x01\x00\x00\x00\t' % (struct.pack('>H', len(s)), s))

        stream.truncate()
        encoder.writeObject(self.jessica2)

        self.assertTrue(hasattr(context, 'gae_objects'))
        self.assertEquals(context.gae_objects, {PetModel: {s: self.jessica}})
        self.assertEquals(stream.getvalue(), '\x07\x00\x00')
        stream.truncate()

        # check a non referenced object
        toby = PetModel(name='Toby', type='cat')
        toby.put()

        try:
            encoder.writeObject(toby)
        finally:
            toby.delete()

    def test_amf3(self):
        encoder = pyamf.get_encoder(pyamf.AMF3)
        context = encoder.context
        stream = encoder.stream
        s = str(self.jessica.key())

        self.assertFalse(hasattr(context, 'gae_objects'))

        encoder.writeObject(self.jessica)

        self.assertTrue(hasattr(context, 'gae_objects'))
        self.assertEquals(context.gae_objects, {PetModel: {s: self.jessica}})
        self.assertEquals(stream.getvalue(), '\nk\x01\t_key!weight_in_pounds'
            '\ttype\tname\x13birthdate%%spayed_or_neutered\x06%s%s\x04\x05\x06'
            '\x07cat\x06\x0fJessica\x08\x01B^\xc4\xae\xaa'
            '\x00\x00\x00\x02\x01' % (
                amf3._encode_int(len(s) << 1 | amf3.REFERENCE_BIT), s))

        stream.truncate()
        encoder.writeObject(self.jessica2)

        self.assertTrue(hasattr(context, 'gae_objects'))
        self.assertEquals(context.gae_objects, {PetModel: {s: self.jessica}})
        self.assertEquals(stream.getvalue(), '\n\x00')

    def test_decode(self):
        pyamf.register_class(PetModel, 'Pet')
        k = str(self.jessica.key())

        bytes = '\x10\x00\x03Pet\x00\x04_key\x02%s%s\x00\x04type\x02\x00' + \
            '\x03cat\x00\x10weight_in_pounds\x00@\x14\x00\x00\x00\x00\x00' + \
            '\x00\x00\x04name\x02\x00\x07Jessica\x00\tbirthdate\x0bB^\xc4' + \
            '\xae\xaa\x00\x00\x00\x00\x00\x00\x12spayed_or_neutered' + \
            '\x01\x00\x00\x00\t'
        bytes = bytes % (struct.pack('>H', len(k)), k)

        decoder = pyamf.get_decoder(pyamf.AMF0)
        context = decoder.context
        stream = decoder.stream

        stream.write(bytes * 2)
        stream.seek(0)

        j = decoder.readElement()
        alias = context.getClassAlias(PetModel)

        self.assertTrue(isinstance(j, PetModel))
        self.assertTrue(isinstance(alias, adapter_db.DataStoreClassAlias))

        self.assertEquals(context.gae_objects, {PetModel: {k: j}})

        j2 = decoder.readElement()

        self.assertTrue(isinstance(j2, PetModel))
        self.assertEquals(context.gae_objects, {PetModel: {k: j}})

    def test_cached_reference_properties(self):
        gets = []

        class Author(db.Model):
            name = db.StringProperty()

            @staticmethod
            def get(*args, **kwargs):
                gets.append([Author, args, kwargs])

                return db.Model.get(*args, **kwargs)

        class Novel(db.Model):
            title = db.StringProperty()
            author = db.ReferenceProperty(Author)

            @staticmethod
            def get(*args, **kwargs):
                gets.append([Novel, args, kwargs])

                return db.Model.get(*args, **kwargs)

        a = Author(name='Jane Austen')
        a.put()
        k = str(a.key())

        b = Novel(title='Sense and Sensibility', author=a)
        b.put()

        c = Novel(title='Pride and Prejudice', author=a)
        c.put()

        try:
            s, p = Novel.all().order('-title').fetch(2)

            encoder = pyamf.get_encoder(pyamf.AMF3)
            stream = encoder.stream
            context = encoder.context

            self.assertFalse(hasattr(context, 'gae_objects'))
            self.assertEquals(gets, [])

            encoder.writeElement(s)

            self.assertTrue(hasattr(context, 'gae_objects'))
            self.assertEquals(context.gae_objects, {
                Novel: {str(s.key()): s},
                Author: {str(a.key()): a}
            })

            self.assertEquals(gets, [
                [Author, (k,), {}]
            ])

            encoder.writeElement(p)

            self.assertEquals(context.gae_objects, {
                Novel: {
                    str(s.key()): s,
                    str(p.key()): p,
                },
                Author: {str(a.key()): a}
            })

            self.assertEquals(gets, [
                [Author, (k,), {}]
            ])

        finally:
            a.delete()
            b.delete()
            c.delete()

        c = Novel(title='Pride and Prejudice', author=None)
        c.put()

        encoder = pyamf.get_encoder(encoding=pyamf.AMF3)
        alias = adapter_db.DataStoreClassAlias(Novel, None)

        self.assertEquals(alias.getAttributes(c, codec=encoder), (
            {
                '_key': str(c.key()),
                'title': 'Pride and Prejudice',
                'author': None
            },
            {}
        ))

class GAEReferenceCollectionTestCase(unittest.TestCase):
    def setUp(self):
        self.klass = adapter_db.GAEReferenceCollection

    def test_init(self):
        x = self.klass()

        self.assertEquals(x, {})

    def test_get(self):
        x = self.klass()

        # not a class type
        self.assertRaises(TypeError, x.getClassKey, chr, '')
        # not a subclass of db.Model/db.Expando
        self.assertRaises(TypeError, x.getClassKey, Spam, '')
        # wrong type for key
        self.assertRaises(TypeError, x.getClassKey, PetModel, 3)

        x = self.klass()

        self.assertRaises(KeyError, x.getClassKey, PetModel, 'foo')
        self.assertEquals(x, {PetModel: {}})

        obj = object()

        x[PetModel]['foo'] = obj

        obj2 = x.getClassKey(PetModel, 'foo')

        self.assertEquals(id(obj), id(obj2))
        self.assertEquals(x, {PetModel: {'foo': obj}})

    def test_add(self):
        x = self.klass()

        # not a class type
        self.assertRaises(TypeError, x.addClassKey, chr, '')
        # not a subclass of db.Model/db.Expando
        self.assertRaises(TypeError, x.addClassKey, Spam, '')
        # wrong type for key
        self.assertRaises(TypeError, x.addClassKey, PetModel, 3)

        x = self.klass()
        pm1 = PetModel(type='cat', name='Jessica')
        pm2 = PetModel(type='dog', name='Sam')
        pe1 = PetExpando(type='cat', name='Toby')

        self.assertEquals(x, {})

        x.addClassKey(PetModel, 'foo', pm1)
        self.assertEquals(x, {PetModel: {'foo': pm1}})
        x.addClassKey(PetModel, 'bar', pm2)
        self.assertEquals(x, {PetModel: {'foo': pm1, 'bar': pm2}})
        x.addClassKey(PetExpando, 'baz', pe1)
        self.assertEquals(x, {
            PetModel: {'foo': pm1, 'bar': pm2},
            PetExpando: {'baz': pe1}
        })

class GettableModelStub(db.Model):
    gets = []

    @staticmethod
    def get(*args, **kwargs):
        GettableModelStub.gets.append([args, kwargs])

class HelperTestCase(unittest.TestCase):
    def test_getGAEObjects(self):
        context = Spam()

        self.assertFalse(hasattr(context, 'gae_objects'))

        x = adapter_db.getGAEObjects(context)
        self.assertTrue(isinstance(x, adapter_db.GAEReferenceCollection))
        self.assertTrue(hasattr(context, 'gae_objects'))
        self.assertEquals(id(x), id(context.gae_objects))

    def test_loadInstanceFromDatastore(self):
        # not a class type
        self.assertRaises(TypeError, adapter_db.loadInstanceFromDatastore, chr, '')
        # not a subclass of db.Model/db.Expando
        self.assertRaises(TypeError, adapter_db.loadInstanceFromDatastore, Spam, '')
        # not a valid key type
        self.assertRaises(TypeError, adapter_db.loadInstanceFromDatastore, GettableModelStub, 2)

        self.assertEquals(GettableModelStub.gets, [])
        adapter_db.loadInstanceFromDatastore(GettableModelStub, 'foo', codec=None)
        self.assertEquals(GettableModelStub.gets, [[('foo',), {}]])

        codec = Spam()
        codec.context = Spam()
        GettableModelStub.gets = []

        self.assertFalse(hasattr(codec.context, 'gae_objects'))
        adapter_db.loadInstanceFromDatastore(GettableModelStub, 'foo', codec=codec)
        self.assertTrue(hasattr(codec.context, 'gae_objects'))
        self.assertEquals(GettableModelStub.gets, [[('foo',), {}]])

        gae_objects = codec.context.gae_objects
        self.assertTrue(isinstance(gae_objects, adapter_db.GAEReferenceCollection))
        self.assertEquals(gae_objects, {GettableModelStub: {'foo': None}})

    def test_Query_type(self):
        """
        L{db.Query} instances get converted to lists ..
        """
        q = PetModel.all()

        self.assertTrue(isinstance(q, db.Query))
        self.assertEquals(pyamf.encode(q).getvalue(), '\n\x00\x00\x00\x00')

def suite():
    suite = unittest.TestSuite()

    test_cases = [
        EncodingModelTestCase,
        EncodingExpandoTestCase,
        EncodingReferencesTestCase,
        ListPropertyTestCase,
        DecodingModelTestCase,
        DecodingExpandoTestCase,
        ClassAliasTestCase,
        ReferencesTestCase,
        GAEReferenceCollectionTestCase,
        HelperTestCase
    ]

    for tc in test_cases:
        suite.addTest(unittest.makeSuite(tc))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
