# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
PyAMF Google adapter tests.

@since: 0.3.1
"""

import unittest, datetime, struct

from google.appengine.ext import db

import pyamf
from pyamf import amf3
from pyamf.tests.util import ClassCacheClearingTestCase

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
            '\x03\x00\x04type\x02\x00\x03cat\x00\x10weight_in_pounds\x00@'
            '\x14\x00\x00\x00\x00\x00\x00\x00\x04name\x02\x00\x07Jessica'
            '\x00\tbirthdate\x0bB^\xc4\xae\xaa\x00\x00\x00\x00\x00\x00\x12'
            'spayed_or_neutered\x01\x00\x00\x00\t')

    def test_amf3(self):
        encoder = pyamf.get_encoder(pyamf.AMF3)
        encoder.writeElement(self.jessica)
        self.assertEquals(encoder.stream.getvalue(),
            '\n\x0b\x01\ttype\x06\x07cat!weight_in_pounds\x04\x05\tname\x06'
            '\x0fJessica\x13birthdate\x08\x01B^\xc4\xae\xaa\x00\x00\x00%'
            'spayed_or_neutered\x02\x01')

    def test_save_amf0(self):
        self.jessica.put()

        k = str(self.jessica.key())
        encoder = pyamf.get_encoder(pyamf.AMF0)
        encoder.writeElement(self.jessica)

        self.assertEquals(encoder.stream.getvalue(),
            '\x03\x00\x04name\x02\x00\x07Jessica\x00\x04_key\x02%s%s\x00'
            '\tbirthdate\x0bB^\xc4\xae\xaa\x00\x00\x00\x00\x00\x00\x10'
            'weight_in_pounds\x00@\x14\x00\x00\x00\x00\x00\x00\x00\x04'
            'type\x02\x00\x03cat\x00\x12spayed_or_neutered\x01\x00\x00'
            '\x00\t' % (struct.pack('>H' ,len(k)), k))

    def test_save_amf3(self):
        self.jessica.put()

        k = str(self.jessica.key())
        encoder = pyamf.get_encoder(pyamf.AMF3)
        encoder.writeElement(self.jessica)

        self.assertEquals(encoder.stream.getvalue(),
            '\n\x0b\x01\tname\x06\x0fJessica\t_key\x06%s%s\x13birthdate'
            '\x08\x01B^\xc4\xae\xaa\x00\x00\x00!weight_in_pounds'
            '\x04\x05\ttype\x06\x07cat%%spayed_or_neutered\x02\x01' % (
                amf3._encode_int(len(k) << 1 | amf3.REFERENCE_BIT), k
            ))

    def test_alias_amf0(self):
        pyamf.register_class(PetModel, 'Pet')
        encoder = pyamf.get_encoder(pyamf.AMF0)

        encoder.writeElement(self.jessica)
        self.assertEquals(encoder.stream.getvalue(),
            '\x10\x00\x03Pet\x00\x04type\x02\x00\x03cat\x00\x10'
            'weight_in_pounds\x00@\x14\x00\x00\x00\x00\x00\x00\x00\x04name'
            '\x02\x00\x07Jessica\x00\tbirthdate\x0bB^\xc4\xae\xaa\x00\x00'
            '\x00\x00\x00\x00\x12spayed_or_neutered\x01\x00\x00\x00\t')

    def test_alias_amf3(self):
        pyamf.register_class(PetModel, 'Pet')
        encoder = pyamf.get_encoder(pyamf.AMF3)
        encoder.writeElement(self.jessica)

        self.assertEquals(encoder.stream.getvalue(),
            '\n\x0b\x07Pet\ttype\x06\x07cat!weight_in_pounds\x04\x05\tname'
            '\x06\x0fJessica\x13birthdate\x08\x01B^\xc4\xae\xaa\x00\x00\x00%'
            'spayed_or_neutered\x02\x01')

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
            '\x03\x00\x04name\x02\x00\x07Jessica\x00\tbirthdate'
            '\x0bB^\xc4\xae\xaa\x00\x00\x00\x00\x00\x00\x10weight_in_pounds'
            '\x00@\x14\x00\x00\x00\x00\x00\x00\x00\x03foo\x02\x00\x03bar'
            '\x00\x04type\x02\x00\x03cat\x00\x12spayed_or_neutered'
            '\x01\x00\x00\x00\t')

    def test_amf3(self):
        encoder = pyamf.get_encoder(pyamf.AMF3)
        encoder.writeElement(self.jessica)

        self.assertEquals(encoder.stream.getvalue(),
            '\n\x0b\x01\tname\x06\x0fJessica\x13birthdate'
            '\x08\x01B^\xc4\xae\xaa\x00\x00\x00!weight_in_pounds\x04\x05\x07'
            'foo\x06\x07bar\ttype\x06\x07cat%spayed_or_neutered\x02\x01')

    def test_save_amf0(self):
        self.jessica.put()

        k = str(self.jessica.key())
        encoder = pyamf.get_encoder(pyamf.AMF0)
        encoder.writeElement(self.jessica)

        self.assertEquals(encoder.stream.getvalue(),
            '\x03\x00\x04name\x02\x00\x07Jessica\x00\x04_key\x02%s%s\x00'
            '\tbirthdate\x0bB^\xc4\xae\xaa\x00\x00\x00\x00\x00\x00\x10'
            'weight_in_pounds\x00@\x14\x00\x00\x00\x00\x00\x00\x00\x03'
            'foo\x02\x00\x03bar\x00\x04type\x02\x00\x03cat\x00\x12'
            'spayed_or_neutered\x01\x00\x00\x00\t' % (struct.pack('>H', len(k)), k))

    def test_save_amf3(self):
        self.jessica.put()

        k = str(self.jessica.key())
        encoder = pyamf.get_encoder(pyamf.AMF3)
        encoder.writeElement(self.jessica)

        self.assertEquals(encoder.stream.getvalue(),
            '\n\x0b\x01\tname\x06\x0fJessica\t_key\x06%s%s\x13birthdate'
            '\x08\x01B^\xc4\xae\xaa\x00\x00\x00!weight_in_pounds\x04\x05'
            '\x07foo\x06\x07bar\ttype\x06\x07cat%%spayed_or_neutered\x02\x01' % (
                amf3._encode_int(len(k) << 1 | amf3.REFERENCE_BIT), k
            ))

    def test_alias_amf0(self):
        pyamf.register_class(PetExpando, 'Pet')
        encoder = pyamf.get_encoder(pyamf.AMF0)

        encoder.writeElement(self.jessica)
        self.assertEquals(encoder.stream.getvalue(),
            '\x10\x00\x03Pet\x00\x04name\x02\x00\x07Jessica\x00\tbirthdate'
            '\x0bB^\xc4\xae\xaa\x00\x00\x00\x00\x00\x00\x10weight_in_pounds'
            '\x00@\x14\x00\x00\x00\x00\x00\x00\x00\x03foo\x02\x00\x03bar'
            '\x00\x04type\x02\x00\x03cat\x00\x12spayed_or_neutered\x01'
            '\x00\x00\x00\t')

    def test_alias_amf3(self):
        pyamf.register_class(PetExpando, 'Pet')
        encoder = pyamf.get_encoder(pyamf.AMF3)
        encoder.writeElement(self.jessica)

        self.assertEquals(encoder.stream.getvalue(),
            '\n\x0b\x07Pet\tname\x06\x0fJessica\x13birthdate\x08\x01'
            'B^\xc4\xae\xaa\x00\x00\x00!weight_in_pounds\x04\x05\x07foo'
            '\x06\x07bar\ttype\x06\x07cat%spayed_or_neutered\x02\x01')

class EncodingReferencesTestCase(ClassCacheClearingTestCase):
    """
    This test case refers to L{db.ReferenceProperty<http://code.google.com/appengine/docs/datastore/typesandpropertyclasses.html#ReferenceProperty>},
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
                '\x03\x00\x05title\x02\x00\x15Sense and Sensibility\x00\x06'
                'author\x03\x00\x04_key\x02%s%s\x00\x04name\x02\x00\x0b'
                'Jane Austen\x00\x00\t\x00\x00\t' % (
                    struct.pack('>H', len(k)), k))

            encoder = pyamf.get_encoder(pyamf.AMF3)

            encoder.writeElement(b)
            self.assertEquals(encoder.stream.getvalue(),
                '\n\x0b\x01\x0btitle\x06+Sense and Sensibility\rauthor\n\x0b'
                '\x01\t_key\x06%s%s\tname\x06\x17Jane Austen\x01\x01' % (
                    amf3._encode_int(len(k) << 1 | amf3.REFERENCE_BIT), k))

            # now test with aliases ..
            pyamf.register_class(Author, 'Author')
            pyamf.register_class(Novel, 'Novel')

            encoder = pyamf.get_encoder(pyamf.AMF0)

            encoder.writeElement(b)
            self.assertEquals(encoder.stream.getvalue(), '\x10\x00\x05Novel'
                '\x00\x05title\x02\x00\x15Sense and Sensibility\x00\x06author'
                '\x10\x00\x06Author\x00\x04_key\x02%s%s\x00\x04name\x02'
                '\x00\x0bJane Austen\x00\x00\t\x00\x00\t' % (
                    struct.pack('>H', len(k)), k))

            encoder = pyamf.get_encoder(pyamf.AMF3)

            encoder.writeElement(b)
            self.assertEquals(encoder.stream.getvalue(),
                '\n\x0b\x0bNovel\x0btitle\x06+Sense and Sensibility\rauthor'
                '\n\x0b\rAuthor\t_key\x06%s%s\tname\x06\x17Jane Austen\x01\x01' % (
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
                '\x03\x00\x05title\x02\x00\x15Sense and Sensibility\x00\x06'
                'author\x03\x00\x04_key\x02%s%s\x00\x04name\x02\x00\x0b'
                'Jane Austen\x00\x00\t\x00\x00\t' % (
                    struct.pack('>H', len(k)), k))

            encoder = pyamf.get_encoder(pyamf.AMF3)

            encoder.writeElement(b)
            self.assertEquals(encoder.stream.getvalue(),
                '\n\x0b\x01\x0btitle\x06+Sense and Sensibility\rauthor\n\x0b'
                '\x01\t_key\x06%s%s\tname\x06\x17Jane Austen\x01\x01' % (
                    amf3._encode_int(len(k) << 1 | amf3.REFERENCE_BIT), k))

            # now test with aliases ..
            pyamf.register_class(Author, 'Author')
            pyamf.register_class(Novel, 'Novel')

            encoder = pyamf.get_encoder(pyamf.AMF0)

            encoder.writeElement(b)
            self.assertEquals(encoder.stream.getvalue(), '\x10\x00\x05Novel'
                '\x00\x05title\x02\x00\x15Sense and Sensibility\x00\x06author'
                '\x10\x00\x06Author\x00\x04_key\x02%s%s\x00\x04name\x02'
                '\x00\x0bJane Austen\x00\x00\t\x00\x00\t' % (
                    struct.pack('>H', len(k)), k))

            encoder = pyamf.get_encoder(pyamf.AMF3)

            encoder.writeElement(b)
            self.assertEquals(encoder.stream.getvalue(),
                '\n\x0b\x0bNovel\x0btitle\x06+Sense and Sensibility\rauthor'
                '\n\x0b\rAuthor\t_key\x06%s%s\tname\x06\x17Jane Austen\x01\x01' % (
                    amf3._encode_int(len(k) << 1 | amf3.REFERENCE_BIT), k))
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
            '\x03\x00\x07numbers\n\x00\x00\x00\x05\x00@\x00\x00\x00\x00\x00'
            '\x00\x00\x00@\x10\x00\x00\x00\x00\x00\x00\x00@\x18\x00\x00\x00'
            '\x00\x00\x00\x00@ \x00\x00\x00\x00\x00\x00\x00@$\x00\x00\x00\x00'
            '\x00\x00\x00\x00\t')

        encoder = pyamf.get_encoder(pyamf.AMF3)

        encoder.writeElement(obj)
        self.assertEquals(encoder.stream.getvalue(),
            '\n\x0b\x01\x0fnumbers\t\x0b\x01\x04\x02\x04\x04\x04\x06\x04\x08'
            '\x04\n\x01')

        pyamf.register_class(ListModel, 'list-model')

        encoder = pyamf.get_encoder(pyamf.AMF0)

        encoder.writeElement(obj)
        self.assertEquals(encoder.stream.getvalue(),
            '\x10\x00\nlist-model\x00\x07numbers\n\x00\x00\x00\x05\x00@\x00'
            '\x00\x00\x00\x00\x00\x00\x00@\x10\x00\x00\x00\x00\x00\x00\x00@'
            '\x18\x00\x00\x00\x00\x00\x00\x00@ \x00\x00\x00\x00\x00\x00\x00@$'
            '\x00\x00\x00\x00\x00\x00\x00\x00\t')

        encoder = pyamf.get_encoder(pyamf.AMF3)

        encoder.writeElement(obj)
        self.assertEquals(encoder.stream.getvalue(),
            '\n\x0b\x15list-model\x0fnumbers\t\x0b\x01\x04\x02\x04\x04\x04'
            '\x06\x04\x08\x04\n\x01')

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

    def tearDown(self):
        try:
            self.jessica.delete()
        except:
            pass

    def test_create_instance(self):
        x = self.alias.createInstance()

        for y in adapter_db.DataStoreClassAlias.INTERNAL_ATTRS:
            self.assertEquals(None, getattr(x, y))

    def test_apply(self):
        x = self.alias.createInstance()

        self.alias.applyAttributes(x, {
            adapter_db.DataStoreClassAliasKEY_ATTR: None
        })

def suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(EncodingModelTestCase))
    suite.addTest(unittest.makeSuite(EncodingExpandoTestCase))
    suite.addTest(unittest.makeSuite(EncodingReferencesTestCase))
    suite.addTest(unittest.makeSuite(ListPropertyTestCase))
    suite.addTest(unittest.makeSuite(DecodingModelTestCase))
    suite.addTest(unittest.makeSuite(DecodingExpandoTestCase))
    suite.addTest(unittest.makeSuite(ClassAliasTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
