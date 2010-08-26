# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
PyAMF Google adapter tests.

@since: 0.3.1
"""

import unittest
import datetime
import struct
import os


class MockDBModule(object):
    """
    Pretends to look like the C{google.appengine.ext.db} module so this file
    will import correctly
    """

    def __getattr__(self, name):
        class c(object):
            def __init__(self, *args, **kwargs):
                pass

        return c

    def __nonzero__(self):
        return False


try:
    from google.appengine.ext import db, blobstore
    from google.appengine.ext.db import polymodel

    from pyamf.adapters import _google_appengine_ext_db as adapter_db
    from pyamf.adapters import _google_appengine_ext_blobstore as adapter_blobstore
except ImportError:
    db = MockDBModule()

if os.environ.get('SERVER_SOFTWARE', None) is None:
    # we're not being run in appengine environment (at one that we are known to
    # work in)
    db = MockDBModule()


import pyamf
from pyamf import amf3
from pyamf.tests import util

Spam = util.Spam


class PetModel(db.Model):
    """
    """

    # 'borrowed' from http://code.google.com/appengine/docs/datastore/entitiesandmodels.html
    name = db.StringProperty(required=True)
    type = db.StringProperty(required=True, choices=set(["cat", "dog", "bird"]))
    birthdate = db.DateProperty()
    weight_in_pounds = db.IntegerProperty()
    spayed_or_neutered = db.BooleanProperty()


class PetExpando(db.Expando):
    """
    """

    name = db.StringProperty(required=True)
    type = db.StringProperty(required=True, choices=set(["cat", "dog", "bird"]))
    birthdate = db.DateProperty()
    weight_in_pounds = db.IntegerProperty()
    spayed_or_neutered = db.BooleanProperty()


class ListModel(db.Model):
    """
    """
    numbers = db.ListProperty(long)


class GettableModelStub(db.Model):
    """
    """

    gets = []

    @staticmethod
    def get(*args, **kwargs):
        GettableModelStub.gets.append([args, kwargs])


class Author(db.Model):
    name = db.StringProperty()


class Novel(db.Model):
    title = db.StringProperty()
    author = db.ReferenceProperty(Author)


class BaseTestCase(util.ClassCacheClearingTestCase):
    """
    """

    def setUp(self):
        if not db:
            self.skipTest("'google.appengine.ext.db' not available")

        util.ClassCacheClearingTestCase.setUp(self)

    def put(self, entity):
        entity.put()
        self.addCleanup(self.deleteEntity, entity)

    def deleteEntity(self, entity):
        if entity.is_saved():
            entity.delete()

    def decode(self, bytes, encoding=pyamf.AMF3):
        decoded = list(pyamf.decode(bytes, encoding=encoding))

        if len(decoded) == 1:
            return decoded[0]

        return decoded


class JessicaMixIn(object):
    """
    Provides jessica!
    """

    jessica_attrs = {
        'name': 'Jessica',
        'type': 'cat',
        'birthdate': datetime.date(1986, 10, 2),
        'weight_in_pounds': 5,
        'spayed_or_neutered': False
    }

    jessica_class = None

    def setUp(self):
        self.jessica = self.jessica_class(**self.jessica_attrs)


class EncodingModelTestCase(BaseTestCase, JessicaMixIn):
    """
    """

    jessica_class = PetModel

    def setUp(self):
        BaseTestCase.setUp(self)
        JessicaMixIn.setUp(self)

    def test_amf0(self):
        encoded = (
            '\x03', (
                '\x00\x04_key\x05',
                '\x00\tbirthdate\x0bB^\xc4\xae\xaa\x00\x00\x00\x00\x00',
                '\x00\x04name\x02\x00\x07Jessica',
                '\x00\x12spayed_or_neutered\x01\x00',
                '\x00\x04type\x02\x00\x03cat',
                '\x00\x10weight_in_pounds\x00@\x14\x00\x00\x00\x00\x00\x00'
            ),
            '\x00\x00\t'
        )

        self.assertEncodes(self.jessica, encoded, encoding=pyamf.AMF0)

    def test_amf3(self):
        bytes = (
            '\n\x0b\x01', (
                '\tname\x06\x0fJessica',
                '\t_key\x01',
                '\x13birthdate\x08\x01B^\xc4\xae\xaa\x00\x00\x00',
                '!weight_in_pounds\x04\x05',
                '\ttype\x06\x07cat',
                '%spayed_or_neutered\x02\x01'
            ))

        self.assertEncodes(self.jessica, bytes, encoding=pyamf.AMF3)

    def test_save_amf0(self):
        self.put(self.jessica)

        k = str(self.jessica.key())

        bytes = ('\x03', (
            '\x00\x04_key\x02%s%s' % (struct.pack('>H', len(k)), k),
            '\x00\tbirthdate\x0bB^\xc4\xae\xaa\x00\x00\x00\x00\x00',
            '\x00\x04name\x02\x00\x07Jessica',
            '\x00\x12spayed_or_neutered\x01\x00',
            '\x00\x04type\x02\x00\x03cat',
            '\x00\x10weight_in_pounds\x00@\x14\x00\x00\x00\x00\x00\x00'),
            '\x00\x00\t')

        self.assertEncodes(self.jessica, bytes, encoding=pyamf.AMF0)

    def test_save_amf3(self):
        self.put(self.jessica)

        k = str(self.jessica.key())
        encoded_key = '%s%s' % (amf3.encode_int(len(k) << 1 | amf3.REFERENCE_BIT), k)

        bytes = (
            '\n\x0b\x01', (
                '\tname\x06\x0fJessica',
                '\t_key\x06%s' % encoded_key,
                '\x13birthdate\x08\x01B^\xc4\xae\xaa\x00\x00\x00',
                '!weight_in_pounds\x04\x05',
                '\ttype\x06\x07cat',
                '%spayed_or_neutered\x02\x01'
            ))

        self.assertEncodes(self.jessica, bytes, encoding=pyamf.AMF3)

    def test_alias_amf0(self):
        pyamf.register_class(PetModel, 'Pet')

        bytes = (
            '\x10\x00\x03Pet', (
                '\x00\x04_key\x05',
                '\x00\tbirthdate\x0bB^\xc4\xae\xaa\x00\x00\x00\x00\x00',
                '\x00\x04name\x02\x00\x07Jessica',
                '\x00\x12spayed_or_neutered\x01\x00',
                '\x00\x04type\x02\x00\x03cat',
                '\x00\x10weight_in_pounds\x00@\x14\x00\x00\x00\x00\x00\x00'
            ),
            '\x00\x00\t'
        )

        self.assertEncodes(self.jessica, bytes, encoding=pyamf.AMF0)

    def test_alias_amf3(self):
        pyamf.register_class(PetModel, 'Pet')

        bytes = (
            '\n\x0b\x07Pet', (
                '\tname\x06\x0fJessica',
                '\t_key\x01',
                '\x13birthdate\x08\x01B^\xc4\xae\xaa\x00\x00\x00',
                '!weight_in_pounds\x04\x05',
                '\x07foo\x06\x07bar',
                '\ttype\x06\x07cat',
                '%spayed_or_neutered\x02\x01'
            ))

        self.assertEncodes(self.jessica, bytes, encoding=pyamf.AMF3)


class EncodingExpandoTestCase(BaseTestCase, JessicaMixIn):
    """
    Tests for encoding L{db.Expando} classes
    """

    jessica_class = PetExpando

    def setUp(self):
        BaseTestCase.setUp(self)
        JessicaMixIn.setUp(self)

        self.jessica.foo = 'bar'

        self.addCleanup(self.deleteEntity, self.jessica)

    def test_amf0(self):
        bytes = (
            '\x03', (
                '\x00\x04_key\x05',
                '\x00\tbirthdate\x0bB^\xc4\xae\xaa\x00\x00\x00\x00\x00',
                '\x00\x04name\x02\x00\x07Jessica',
                '\x00\x12spayed_or_neutered\x01\x00',
                '\x00\x04type\x02\x00\x03cat',
                '\x00\x10weight_in_pounds\x00@\x14\x00\x00\x00\x00\x00\x00',
                '\x00\x03foo\x02\x00\x03bar'
            ),
            '\x00\x00\t'
        )

        self.assertEncodes(self.jessica, bytes, encoding=pyamf.AMF0)

    def test_amf3(self):
        bytes = (
            '\n\x0b\x01', (
                '\tname\x06\x0fJessica',
                '\t_key\x01',
                '\x13birthdate\x08\x01B^\xc4\xae\xaa\x00\x00\x00',
                '!weight_in_pounds\x04\x05',
                '\x07foo\x06\x07bar',
                '\ttype\x06\x07cat',
                '%spayed_or_neutered\x02\x01'
            ))

        self.assertEncodes(self.jessica, bytes, encoding=pyamf.AMF3)

    def test_save_amf0(self):
        self.put(self.jessica)

        k = str(self.jessica.key())
        bytes = pyamf.encode(self.jessica, encoding=pyamf.AMF0).getvalue()

        self.assertBuffer(bytes, ('\x03', (
            '\x00\x04_key\x02%s%s' % (struct.pack('>H', len(k)), k),
            '\x00\tbirthdate\x0bB^\xc4\xae\xaa\x00\x00\x00\x00\x00',
            '\x00\x04name\x02\x00\x07Jessica',
            '\x00\x12spayed_or_neutered\x01\x00',
            '\x00\x04type\x02\x00\x03cat',
            '\x00\x10weight_in_pounds\x00@\x14\x00\x00\x00\x00\x00\x00',
            '\x00\x03foo\x02\x00\x03bar'),
            '\x00\x00\t'))

    def test_save_amf3(self):
        self.put(self.jessica)

        k = str(self.jessica.key())
        encoded_key = '%s%s' % (amf3.encode_int(len(k) << 1 | amf3.REFERENCE_BIT), k)

        bytes = (
            '\n\x0b\x01', (
                '\tname\x06\x0fJessica',
                '\t_key\x06%s' % encoded_key,
                '\x13birthdate\x08\x01B^\xc4\xae\xaa\x00\x00\x00',
                '!weight_in_pounds\x04\x05',
                '\x07foo\x06\x07bar',
                '\ttype\x06\x07cat',
                '%spayed_or_neutered\x02\x01'
            ))

        self.assertEncodes(self.jessica, bytes, encoding=pyamf.AMF3)

    def test_alias_amf0(self):
        pyamf.register_class(PetExpando, 'Pet')
        bytes = pyamf.encode(self.jessica, encoding=pyamf.AMF0).getvalue()

        self.assertBuffer(bytes, ('\x10\x00\x03Pet', (
            '\x00\x04_key\x05',
            '\x00\tbirthdate\x0bB^\xc4\xae\xaa\x00\x00\x00\x00\x00',
            '\x00\x04name\x02\x00\x07Jessica',
            '\x00\x12spayed_or_neutered\x01\x00',
            '\x00\x04type\x02\x00\x03cat',
            '\x00\x10weight_in_pounds\x00@\x14\x00\x00\x00\x00\x00\x00',
            '\x00\x03foo\x02\x00\x03bar'),
            '\x00\x00\t'))

    def test_alias_amf3(self):
        pyamf.register_class(PetExpando, 'Pet')

        bytes = (
            '\n\x0b\x07Pet', (
                '\tname\x06\x0fJessica',
                '\t_key\x01',
                '\x13birthdate\x08\x01B^\xc4\xae\xaa\x00\x00\x00',
                '!weight_in_pounds\x04\x05',
                '\x07foo\x06\x07bar',
                '\ttype\x06\x07cat',
                '%spayed_or_neutered\x02\x01'
            ))

        self.assertEncodes(self.jessica, bytes, encoding=pyamf.AMF3)


class EncodingReferencesTestCase(BaseTestCase):
    """
    This test case refers to
    L{db.ReferenceProperty<http://code.google.com/appengine/docs/datastore/typesandpropertyclasses.html#ReferenceProperty>},
    not AMF references.
    """

    def test_model(self):
        a = Author(name='Jane Austen')
        self.put(a)
        k = str(a.key())

        amf0_k = struct.pack('>H', len(k)) + k
        amf3_k = amf3.encode_int(len(k) << 1 | amf3.REFERENCE_BIT) + k

        b = Novel(title='Sense and Sensibility', author=a)

        self.assertIdentical(b.author, a)

        bytes = (
            '\x03', (
                '\x00\x05title\x02\x00\x15Sense and Sensibility',
                '\x00\x04_key\x02' + amf0_k,
                '\x00\x06author\x03', (
                    '\x00\x04name\x02\x00\x0bJane Austen',
                    '\x00\x04_key\x05'
                ),
                '\x00\x00\t'
            ),
            '\x00\x00\t')

        self.assertEncodes(b, bytes, encoding=pyamf.AMF0)

        bytes = (
            '\n\x0b\x01', ((
                '\rauthor\n\x0b\x01', (
                    '\t_key\x06' + amf3_k,
                    '\tname\x06\x17Jane Austen'
                ), '\x01\x06\x01'),
                '\x0btitle\x06+Sense and Sensibility'
            ),
            '\x01')

        self.assertEncodes(b, bytes, encoding=pyamf.AMF3)

        # now test with aliases ..
        pyamf.register_class(Author, 'Author')
        pyamf.register_class(Novel, 'Novel')

        bytes = (
            '\x10\x00\x05Novel', (
                '\x00\x05title\x02\x00\x15Sense and Sensibility',
                '\x00\x04_key\x02' + amf0_k,
                '\x00\x06author\x10\x00\x06Author', (
                    '\x00\x04name\x02\x00\x0bJane Austen',
                    '\x00\x04_key\x05'
                ),
                '\x00\x00\t'
            ),
            '\x00\x00\t')

        self.assertEncodes(b, bytes, encoding=pyamf.AMF0)

        bytes = (
            '\n\x0b\x0bNovel', ((
                '\rauthor\n\x0b\rAuthor', (
                    '\t_key\x06' + amf3_k,
                    '\tname\x06\x17Jane Austen'
                ), '\x01\n\x01'),
                '\x0btitle\x06+Sense and Sensibility'
            ),
            '\x01')

        self.assertEncodes(b, bytes, encoding=pyamf.AMF3)

    def test_expando(self):
        class Author(db.Expando):
            name = db.StringProperty()

        class Novel(db.Expando):
            title = db.StringProperty()
            author = db.ReferenceProperty(Author)

        a = Author(name='Jane Austen')
        self.put(a)
        k = str(a.key())

        amf0_k = struct.pack('>H', len(k)) + k
        amf3_k = amf3.encode_int(len(k) << 1 | amf3.REFERENCE_BIT) + k

        b = Novel(title='Sense and Sensibility', author=a)

        self.assertIdentical(b.author, a)

        bytes = (
            '\x03', (
                '\x00\x05title\x02\x00\x15Sense and Sensibility',
                '\x00\x04_key\x02' + amf0_k,
                '\x00\x06author\x03', (
                    '\x00\x04name\x02\x00\x0bJane Austen',
                    '\x00\x04_key\x05'
                ),
                '\x00\x00\t'
            ),
            '\x00\x00\t')

        self.assertEncodes(b, bytes, encoding=pyamf.AMF0)

        bytes = (
            '\n\x0b\x01', ((
                '\rauthor\n\x0b\x01', (
                    '\t_key\x06' + amf3_k,
                    '\tname\x06\x17Jane Austen\x01'
                ), '\x02\x01'),
                '\x0btitle\x06+Sense and Sensibility'
            ),
            '\x01')

        self.assertEncodes(b, bytes, encoding=pyamf.AMF3)

        # now test with aliases ..
        pyamf.register_class(Author, 'Author')
        pyamf.register_class(Novel, 'Novel')

        bytes = (
            '\x10\x00\x05Novel', (
                '\x00\x05title\x02\x00\x15Sense and Sensibility',
                '\x00\x04_key\x02' + amf0_k,
                '\x00\x06author\x10\x00\x06Author', (
                    '\x00\x04name\x02\x00\x0bJane Austen',
                    '\x00\x04_key\x05'
                ),
                '\x00\x00\t'
            ),
            '\x00\x00\t')

        self.assertEncodes(b, bytes, encoding=pyamf.AMF0)

        bytes = (
            '\n\x0b\x0bNovel', ((
                '\rauthor\n\x0b\rAuthor', (
                    '\t_key\x06' + amf3_k,
                    '\tname\x06\x17Jane Austen\x01'
                ), '\x06\x01'),
                '\x0btitle\x06+Sense and Sensibility'
            ),
            '\x01')

        self.assertEncodes(b, bytes, encoding=pyamf.AMF3)

    def test_dynamic_property_referenced_object(self):
        a = Author(name='Jane Austen')
        self.put(a)

        b = Novel(title='Sense and Sensibility', author=a)
        self.put(b)

        x = db.get(b.key())
        foo = [1, 2, 3]

        x.author.bar = foo
        k = str(x.key())
        ek = '%s%s' % (struct.pack('>H', len(k)), k)
        l = str(a.key())
        el = '%s%s' % (struct.pack('>H', len(l)), l)

        bytes = (
            '\x03', (
                '\x00\x05title\x02\x00\x15Sense and Sensibility',
                '\x00\x04_key\x02' + ek,
                '\x00\x06author\x03', (
                    '\x00\x03bar\n\x00\x00\x00\x03\x00?\xf0\x00\x00\x00\x00'
                    '\x00\x00\x00@\x00\x00\x00\x00\x00\x00\x00\x00@\x08\x00'
                    '\x00\x00\x00\x00\x00',
                    '\x00\x04name\x02\x00\x0bJane Austen',
                    '\x00\x04_key\x02' + el
                ),
                '\x00\x00\t'
            ),
            '\x00\x00\t')


        self.assertEncodes(x, bytes, encoding=pyamf.AMF0)


class ListPropertyTestCase(BaseTestCase):
    """
    Tests for L{db.ListProperty} properties.
    """

    def setUp(self):
        BaseTestCase.setUp(self)

        self.obj = ListModel()
        self.obj.numbers = [2, 4, 6, 8, 10]

        self.addCleanup(self.deleteEntity, self.obj)

    def test_encode_amf0(self):
        bytes = (
            '\x03', (
                '\x00\x04_key\x05',
                '\x00\x07numbers\n\x00\x00\x00\x05\x00@'
                '\x00\x00\x00\x00\x00\x00\x00\x00@\x10\x00\x00\x00\x00\x00'
                '\x00\x00@\x18\x00\x00\x00\x00\x00\x00\x00@\x20\x00\x00\x00'
                '\x00\x00\x00\x00@$\x00\x00\x00\x00\x00\x00'
            ),
            '\x00\x00\t'
        )

        self.assertEncodes(self.obj, bytes, encoding=pyamf.AMF0)

    def test_encode_amf3(self):
        bytes = (
            '\n\x0b\x01', (
                '\t_key\x01',
                '\x0fnumbers\t\x0b\x01\x04\x02\x04\x04\x04\x06\x04\x08\x04\n'
                    '\x01'
            )
        )

        self.assertEncodes(self.obj, bytes, encoding=pyamf.AMF3)

    def test_encode_amf0_registered(self):
        pyamf.register_class(ListModel, 'list-model')

        bytes = (
            '\x10\x00\nlist-model', (
                '\x00\x04_key\x05',
                '\x00\x07numbers\n\x00\x00\x00\x05\x00@'
                '\x00\x00\x00\x00\x00\x00\x00\x00@\x10\x00\x00\x00\x00\x00'
                '\x00\x00@\x18\x00\x00\x00\x00\x00\x00\x00@\x20\x00\x00\x00'
                '\x00\x00\x00\x00@$\x00\x00\x00\x00\x00\x00'
            ),
            '\x00\x00\t'
        )

        self.assertEncodes(self.obj, bytes, encoding=pyamf.AMF0)

    def test_encode_amf3_registered(self):
        pyamf.register_class(ListModel, 'list-model')

        bytes = (
            '\n\x0b\x15list-model', (
                '\t_key\x01',
                '\x0fnumbers\t\x0b\x01\x04\x02\x04\x04\x04\x06\x04\x08\x04\n'
                    '\x01'
            )
        )

        self.assertEncodes(self.obj, bytes, encoding=pyamf.AMF3)

    def _check_list(self, x):
        self.assertTrue(isinstance(x, ListModel))
        self.assertTrue(hasattr(x, 'numbers'))
        self.assertEqual(x.numbers, [2, 4, 6, 8, 10])

    def test_decode_amf0(self):
        pyamf.register_class(ListModel, 'list-model')

        bytes = (
            '\x10\x00\nlist-model\x00\x07numbers\n\x00\x00\x00\x05\x00@\x00'
            '\x00\x00\x00\x00\x00\x00\x00@\x10\x00\x00\x00\x00\x00\x00\x00@'
            '\x18\x00\x00\x00\x00\x00\x00\x00@ \x00\x00\x00\x00\x00\x00\x00@'
            '$\x00\x00\x00\x00\x00\x00\x00\x00\t')

        x = self.decode(bytes, encoding=pyamf.AMF0)
        self._check_list(x)

    def test_decode_amf3(self):
        pyamf.register_class(ListModel, 'list-model')

        bytes = (
            '\n\x0b\x15list-model\x0fnumbers\t\x0b\x01\x04\x02\x04\x04\x04'
            '\x06\x04\x08\x04\n\x01')

        x = self.decode(bytes, encoding=pyamf.AMF3)
        self._check_list(x)

    def test_none(self):
        pyamf.register_class(ListModel, 'list-model')

        bytes = '\x10\x00\nlist-model\x00\x07numbers\x05\x00\x00\t'

        x = self.decode(bytes, encoding=pyamf.AMF0)

        self.assertEqual(x.numbers, [])


class DecodingModelTestCase(BaseTestCase, JessicaMixIn):
    """
    """

    jessica_class = PetModel

    def setUp(self):
        BaseTestCase.setUp(self)
        JessicaMixIn.setUp(self)

        pyamf.register_class(self.jessica_class, 'Pet')

        self.put(self.jessica)
        self.key = str(self.jessica.key())

    def _check_model(self, x):
        self.assertTrue(isinstance(x, self.jessica_class))
        self.assertEqual(x.__class__, self.jessica_class)

        self.assertEqual(x.type, self.jessica.type)
        self.assertEqual(x.weight_in_pounds, self.jessica.weight_in_pounds)
        self.assertEqual(x.birthdate, self.jessica.birthdate)
        self.assertEqual(x.spayed_or_neutered, self.jessica.spayed_or_neutered)

        # now check db.Model internals
        self.assertEqual(x.key(), self.jessica.key())
        self.assertEqual(x.kind(), self.jessica.kind())
        self.assertEqual(x.parent(), self.jessica.parent())
        self.assertEqual(x.parent_key(), self.jessica.parent_key())
        self.assertTrue(x.is_saved())

    def test_amf0(self):
        encoded_key = '%s%s' % (struct.pack('>H', len(self.key)), self.key)

        bytes = (
            '\x10\x00\x03Pet\x00\x04_key\x02%s\x00\x04type\x02\x00\x03cat'
            '\x00\x10weight_in_pounds\x00@\x14\x00\x00\x00\x00\x00\x00\x00'
            '\x04name\x02\x00\x07Jessica\x00\tbirthdate\x0bB^\xc4\xae\xaa\x00'
            '\x00\x00\x00\x00\x00\x12spayed_or_neutered\x01\x00\x00\x00\t' % (
                encoded_key))

        x = self.decode(bytes, encoding=pyamf.AMF0)

        self._check_model(x)

    def test_amf3(self):
        encoded_key = '%s%s' % (
            amf3.encode_int(len(self.key) << 1 | amf3.REFERENCE_BIT), self.key)

        bytes = (
            '\n\x0b\x07Pet\tname\x06\x0fJessica\t_key\x06%s\x13birthdate'
            '\x08\x01B^\xc4\xae\xaa\x00\x00\x00!weight_in_pounds\x04\x05\x07'
            'foo\x06\x07bar\ttype\x06\x07cat%%spayed_or_neutered\x02\x01' % (
                encoded_key))

        x = self.decode(bytes, encoding=pyamf.AMF3)

        self._check_model(x)


class DecodingExpandoTestCase(DecodingModelTestCase):
    """
    """

    jessica_class = PetExpando


class ClassAliasTestCase(BaseTestCase):
    """
    """

    def setUp(self):
        BaseTestCase.setUp(self)

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

        try:
            pyamf.unregister_class(PetModel)
        except:
            pass

    def test_get_alias(self):
        alias = pyamf.register_class(PetModel)

        self.assertTrue(isinstance(alias, adapter_db.DataStoreClassAlias))

    def test_alias(self):
        self.alias.compile()

        self.assertEqual(self.alias.decodable_properties, [
            'birthdate',
            'name',
            'spayed_or_neutered',
            'type',
            'weight_in_pounds'
        ])

        self.assertEqual(self.alias.encodable_properties, [
            'birthdate',
            'name',
            'spayed_or_neutered',
            'type',
            'weight_in_pounds'
        ])

        self.assertEqual(self.alias.static_attrs, None)
        self.assertEqual(self.alias.readonly_attrs, None)
        self.assertEqual(self.alias.exclude_attrs, None)
        self.assertEqual(self.alias.reference_properties, None)

    def test_create_instance(self):
        x = self.alias.createInstance()

        self.assertTrue(isinstance(x, adapter_db.ModelStub))

        self.assertTrue(hasattr(x, 'klass'))
        self.assertEqual(x.klass, self.alias.klass)

        # test some stub functions
        self.assertEqual(x.properties(), self.alias.klass.properties())
        self.assertEqual(x.dynamic_properties(), [])

    def test_apply(self):
        x = self.alias.createInstance()

        self.assertTrue(hasattr(x, 'klass'))

        self.alias.applyAttributes(x, {
            adapter_db.DataStoreClassAlias.KEY_ATTR: None,
            'name': 'Jessica',
            'type': 'cat',
            'birthdate': None,
            'weight_in_pounds': None,
            'spayed_or_neutered': None
        })

        self.assertFalse(hasattr(x, 'klass'))

    def test_get_attrs(self):
        attrs = self.alias.getEncodableAttributes(self.jessica)
        self.assertEqual(attrs, {
            '_key': None,
            'type': 'cat',
            'name': 'Jessica',
            'birthdate': None,
            'weight_in_pounds': None,
            'spayed_or_neutered': None
        })

    def test_get_attrs_expando(self):
        attrs = self.alias.getEncodableAttributes(self.jessica_expando)
        self.assertEqual(attrs, {
            '_key': None,
            'type': 'cat',
            'name': 'Jessica',
            'birthdate': None,
            'weight_in_pounds': None,
            'spayed_or_neutered': None,
            'foo': 'bar'
        })

    def test_get_attributes(self):
        attrs = self.alias.getEncodableAttributes(self.jessica)

        self.assertEqual(attrs, {
            '_key': None,
            'type': 'cat',
            'name': 'Jessica',
            'birthdate': None,
            'weight_in_pounds': None,
            'spayed_or_neutered': None
        })

    def test_get_attributes_saved(self):
        self.put(self.jessica)

        attrs = self.alias.getEncodableAttributes(self.jessica)

        self.assertEqual(attrs, {
            'name': 'Jessica',
            '_key': str(self.jessica.key()),
            'type': 'cat',
            'birthdate': None,
            'weight_in_pounds': None,
            'spayed_or_neutered': None
        })

    def test_get_attributes_expando(self):
        attrs = self.alias.getEncodableAttributes(self.jessica_expando)

        self.assertEqual(attrs, {
            'name': 'Jessica',
            '_key': None,
            'type': 'cat',
            'birthdate': None,
            'weight_in_pounds': None,
            'spayed_or_neutered': None,
            'foo': 'bar'
        })

    def test_get_attributes_saved_expando(self):
        self.put(self.jessica_expando)

        attrs = self.alias.getEncodableAttributes(self.jessica_expando)

        self.assertEqual(attrs, {
            'name': 'Jessica',
            '_key': str(self.jessica_expando.key()),
            'type': 'cat',
            'birthdate': None,
            'weight_in_pounds': None,
            'spayed_or_neutered': None,
            'foo': 'bar'
        })

    def test_arbitrary_properties(self):
        self.jessica.foo = 'bar'

        attrs = self.alias.getEncodableAttributes(self.jessica)

        self.assertEqual(attrs, {
            '_key': None,
            'type': 'cat',
            'name': 'Jessica',
            'birthdate': None,
            'weight_in_pounds': None,
            'spayed_or_neutered': None,
            'foo': 'bar'
        })

    def test_property_type(self):
        class PropertyTypeModel(db.Model):
            @property
            def readonly(self):
                return True

            def _get_prop(self):
                return False

            def _set_prop(self, v):
                self.prop = v

            read_write = property(_get_prop, _set_prop)

        alias = adapter_db.DataStoreClassAlias(PropertyTypeModel, 'foo.bar')

        obj = PropertyTypeModel()

        attrs = alias.getEncodableAttributes(obj)
        self.assertEqual(attrs, {
            '_key': None,
            'read_write': False,
            'readonly': True
        })

        self.assertFalse(hasattr(obj, 'prop'))

        alias.applyAttributes(obj, {
            '_key': None,
            'readonly': False,
            'read_write': 'foo'
        })

        self.assertEqual(obj.prop, 'foo')


class ReferencesTestCase(BaseTestCase):
    """
    """

    def setUp(self):
        BaseTestCase.setUp(self)

        self.jessica = PetModel(name='Jessica', type='cat')
        self.jessica.birthdate = datetime.date(1986, 10, 2)
        self.jessica.weight_in_pounds = 5
        self.jessica.spayed_or_neutered = False

        self.put(self.jessica)

        self.jessica2 = db.get(self.jessica.key())

        self.assertNotIdentical(self.jessica,self.jessica2)
        self.assertEqual(str(self.jessica.key()), str(self.jessica2.key()))

    def failOnGet(self, *args, **kwargs):
        self.fail('Get attempted %r, %r' % (args, kwargs))

    def test_amf0(self):
        encoder = pyamf.get_encoder(pyamf.AMF0)
        stream = encoder.stream

        encoder.writeElement(self.jessica)

        stream.truncate()

        encoder.writeElement(self.jessica2)
        self.assertEqual(stream.getvalue(), '\x07\x00\x00')

    def test_amf3(self):
        encoder = pyamf.get_encoder(pyamf.AMF3)
        stream = encoder.stream

        encoder.writeElement(self.jessica)

        stream.truncate()

        encoder.writeElement(self.jessica2)
        self.assertEqual(stream.getvalue(), '\n\x00')

    def test_nullreference(self):
        c = Novel(title='Pride and Prejudice', author=None)
        self.put(c)

        encoder = pyamf.get_encoder(encoding=pyamf.AMF3)
        alias = adapter_db.DataStoreClassAlias(Novel, None)

        attrs = alias.getEncodableAttributes(c, codec=encoder)

        self.assertEqual(attrs, {
            '_key': str(c.key()),
            'title': 'Pride and Prejudice',
            'author': None
        })


class GAEReferenceCollectionTestCase(BaseTestCase):
    """
    """

    def setUp(self):
        BaseTestCase.setUp(self)
        self.klass = adapter_db.GAEReferenceCollection

    def test_init(self):
        x = self.klass()

        self.assertEqual(x, {})

    def test_get(self):
        x = self.klass()

        # not a class type
        self.assertRaises(TypeError, x.getClassKey, chr, '')
        # not a subclass of db.Model/db.Expando
        self.assertRaises(TypeError, x.getClassKey, Spam, '')

        x = self.klass()

        self.assertRaises(KeyError, x.getClassKey, PetModel, 'foo')
        self.assertEqual(x, {PetModel: {}})

        obj = object()

        x[PetModel]['foo'] = obj

        obj2 = x.getClassKey(PetModel, 'foo')

        self.assertEqual(id(obj), id(obj2))
        self.assertEqual(x, {PetModel: {'foo': obj}})

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

        self.assertEqual(x, {})

        x.addClassKey(PetModel, 'foo', pm1)
        self.assertEqual(x, {PetModel: {'foo': pm1}})
        x.addClassKey(PetModel, 'bar', pm2)
        self.assertEqual(x, {PetModel: {'foo': pm1, 'bar': pm2}})
        x.addClassKey(PetExpando, 'baz', pe1)
        self.assertEqual(x, {
            PetModel: {'foo': pm1, 'bar': pm2},
            PetExpando: {'baz': pe1}
        })


class HelperTestCase(BaseTestCase):
    """
    """

    def test_getGAEObjects(self):
        context = Spam()
        context.extra = {}

        x = adapter_db.getGAEObjects(context)
        self.assertTrue(isinstance(x, adapter_db.GAEReferenceCollection))
        self.assertTrue('gae_objects' in context.extra)
        self.assertEqual(id(x), id(context.extra['gae_objects']))

    def test_loadInstanceFromDatastore(self):
        # not a class type
        self.assertRaises(TypeError, adapter_db.loadInstanceFromDatastore, chr, '')
        # not a subclass of db.Model/db.Expando
        self.assertRaises(TypeError, adapter_db.loadInstanceFromDatastore, Spam, '')
        # not a valid key type
        self.assertRaises(TypeError, adapter_db.loadInstanceFromDatastore, GettableModelStub, 2)

        self.assertEqual(GettableModelStub.gets, [])
        adapter_db.loadInstanceFromDatastore(GettableModelStub, 'foo', codec=None)
        self.assertEqual(GettableModelStub.gets, [[('foo',), {}]])

        codec = Spam()
        codec.context = Spam()
        codec.context.extra = {}
        GettableModelStub.gets = []

        adapter_db.loadInstanceFromDatastore(GettableModelStub, 'foo', codec=codec)
        self.assertTrue('gae_objects' in codec.context.extra)
        self.assertEqual(GettableModelStub.gets, [[('foo',), {}]])

        gae_objects = codec.context.extra['gae_objects']
        self.assertTrue(isinstance(gae_objects, adapter_db.GAEReferenceCollection))
        self.assertEqual(gae_objects, {GettableModelStub: {'foo': None}})

    def test_Query_type(self):
        """
        L{db.Query} instances get converted to lists ..
        """
        q = PetModel.all()

        self.assertTrue(isinstance(q, db.Query))
        self.assertEncodes(q, '\n\x00\x00\x00\x00', encoding=pyamf.AMF0)
        self.assertEncodes(q, '\t\x01\x01', encoding=pyamf.AMF3)


class FloatPropertyTestCase(BaseTestCase):
    """
    Tests for #609.
    """

    def setUp(self):
        BaseTestCase.setUp(self)

        class FloatModel(db.Model):
            f = db.FloatProperty()

        self.klass = FloatModel
        self.f = FloatModel()
        self.alias = adapter_db.DataStoreClassAlias(self.klass, None)

    def tearDown(self):
        BaseTestCase.tearDown(self)

        if self.f.is_saved():
            self.f.delete()

    def test_behaviour(self):
        """
        Test the behaviour of the Google SDK not handling ints gracefully
        """
        self.assertRaises(db.BadValueError, setattr, self.f, 'f', 3)

        self.f.f = 3.0

        self.assertEqual(self.f.f, 3.0)

    def test_apply_attributes(self):
        self.alias.applyAttributes(self.f, {'f': 3})

        self.assertEqual(self.f.f, 3.0)


class PolyModelTestCase(BaseTestCase):
    """
    Tests for L{db.PolyModel}. See #633
    """

    def setUp(self):
        BaseTestCase.setUp(self)

        class Poly(polymodel.PolyModel):
            s = db.StringProperty()

        self.klass = Poly
        self.p = Poly()
        self.alias = adapter_db.DataStoreClassAlias(self.klass, None)

    def test_encode(self):
        self.p.s = 'foo'

        attrs = self.alias.getEncodableAttributes(self.p)

        self.assertEqual(attrs, {'_key': None, 's': 'foo'})

    def test_deep_inheritance(self):
        class DeepPoly(self.klass):
            d = db.IntegerProperty()

        self.alias = adapter_db.DataStoreClassAlias(DeepPoly, None)
        self.dp = DeepPoly()
        self.dp.s = 'bar'
        self.dp.d = 92

        attrs = self.alias.getEncodableAttributes(self.dp)

        self.assertEqual(attrs, {
            '_key': None,
            's': 'bar',
            'd': 92
        })


class BlobStoreTestCase(BaseTestCase):
    """
    Tests for L{blobstore}
    """

    bytes = (
        '\n\x0bOgoogle.appengine.ext.blobstore.BlobInfo', (
            '\tsize\x04\xcb\xad\x07',
            '\x11creation\x08\x01Br\x9c\x1d\xbeh\x80\x00',
            '\x07key\x06\rfoobar',
            '\x19content_type\x06\x15text/plain',
            '\x11filename\x06\x1fnot-telling.ogg'
        ), '\x01')

    values = {
        'content_type': 'text/plain',
        'size': 1234567,
        'filename': 'not-telling.ogg',
        'creation': datetime.datetime(2010, 07, 11, 14, 15, 01)
    }

    def setUp(self):
        BaseTestCase.setUp(self)

        self.key = blobstore.BlobKey('foobar')

        self.info = blobstore.BlobInfo(self.key, self.values)

    def test_class_alias(self):
        alias_klass = pyamf.get_class_alias(blobstore.BlobInfo)

        self.assertIdentical(alias_klass.__class__, adapter_blobstore.BlobInfoClassAlias)

    def test_encode(self):
        self.assertEncodes(self.info, self.bytes)

    def test_decode(self):
        def check(ret):
            self.assertEqual(ret.key(), self.key)

        self.assertDecodes(self.bytes, check)
