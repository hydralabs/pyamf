# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE for details.

"""
PyAMF SQLAlchemy adapter tests.

@since 0.4
"""

import unittest

from sqlalchemy import MetaData, Table, Column, Integer, String, ForeignKey, \
                       create_engine
from sqlalchemy.orm import mapper, relation, sessionmaker, clear_mappers

import pyamf
import pyamf.flex

class BaseObject(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class User(BaseObject):
    pass

class Address(BaseObject):
    pass

class LazyLoaded(BaseObject):
    pass

class SATestCase(unittest.TestCase):
    def setUp(self):
        # Create DB and map objects
        metadata = MetaData()
        engine = create_engine('sqlite:///:memory:', echo=False)

        Session = sessionmaker(bind=engine)

        self.session = Session()

        users_table = Table('users_table', metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String(64)))

        addresses_table = Table('addresses_table', metadata,
            Column('id', Integer, primary_key=True),
            Column('user_id', Integer, ForeignKey('users_table.id')),
            Column('email_address', String(128)))

        lazy_loaded_table = Table('lazy_loaded', metadata,
            Column('id', Integer, primary_key=True),
            Column('user_id', Integer, ForeignKey('users_table.id')))

        mapper(User, users_table, properties={
               'addresses': relation(Address, backref='user', lazy=False),
               'lazy_loaded': relation(LazyLoaded, lazy=True)})

        mapper(Address, addresses_table)
        mapper(LazyLoaded, lazy_loaded_table)
        metadata.create_all(engine)

        try:
            pyamf.register_class(User, 'server.User')
            pyamf.register_class(Address, 'server.Address')
        except:
            # Classes are already registered
            pass

    def tearDown(self):
        clear_mappers()

    def _build_obj(self):
        user = User()
        user.name = "test_user"
        user.addresses.append(Address(email_address="test@example.org"))

        return user

    def _test_obj(self, encoded, decoded):
        self.assertEquals(User, decoded.__class__)
        self.assertEquals(encoded.name, decoded.name)
        self.assertEquals(encoded.addresses[0].email_address, decoded.addresses[0].email_address)

    def test_encode_decode_transient(self):
        user = self._build_obj()

        encoder = pyamf.get_encoder(pyamf.AMF3)
        encoder.writeElement(user)
        encoded = encoder.stream.getvalue()
        decoded = pyamf.get_decoder(pyamf.AMF3, encoded).readElement()

        self._test_obj(user, decoded)

    def test_encode_decode_persistent(self):
        user = self._build_obj()
        self.session.save(user)
        self.session.commit()
        self.session.refresh(user)

        encoder = pyamf.get_encoder(pyamf.AMF3)
        encoder.writeElement(user)
        encoded = encoder.stream.getvalue()
        decoded = pyamf.get_decoder(pyamf.AMF3, encoded).readElement()

        self._test_obj(user, decoded)

    def test_encode_decode_list(self):
        max = 5
        for i in range(0, max):
            user = self._build_obj()
            user.name = "%s" % i
            self.session.save(user)

        self.session.commit()
        users = self.session.query(User).all()

        encoder = pyamf.get_encoder(pyamf.AMF3)
        encoder.writeElement(users)
        encoded = encoder.stream.getvalue()
        decoded = pyamf.get_decoder(pyamf.AMF3, encoded).readElement()
        self.assertEquals([].__class__, decoded.__class__)

        for i in range(0, max):
            self._test_obj(users[i], decoded[i])

    def test_sa_merge(self):
        user = self._build_obj()

        for i, string in enumerate(['one', 'two', 'three']):
            addr = Address(email_address="%s@example.org" % string)
            user.addresses.append(addr)

        self.session.save(user)
        self.session.commit()
        self.session.refresh(user)

        encoder = pyamf.get_encoder(pyamf.AMF3)
        encoder.writeElement(user)
        encoded = encoder.stream.getvalue()

        decoded = pyamf.get_decoder(pyamf.AMF3, encoded).readElement()
        del decoded.addresses[0]
        del decoded.addresses[1]

        merged_user = self.session.merge(decoded)
        self.assertEqual(len(merged_user.addresses), 2)

    def test_lazy_load_attributes(self):
        user = self._build_obj()
        user.lazy_loaded.append(LazyLoaded())

        self.session.save(user)
        self.session.commit()
        self.session.clear()
        user = self.session.query(User).first()

        encoder = pyamf.get_encoder(pyamf.AMF3)
        encoder.writeElement(user)
        encoded = encoder.stream.getvalue()

        decoded = pyamf.get_decoder(pyamf.AMF3, encoded).readElement()
        self.assertFalse(decoded.__dict__.has_key('lazy_loaded'))

    def test_encode_decode_with_references(self):
        user = self._build_obj()
        self.session.save(user)
        self.session.commit()
        self.session.refresh(user)

        max = 5
        users = []
        for i in range(0, max):
            users.append(user)

        encoder = pyamf.get_encoder(pyamf.AMF3)
        encoder.writeElement(users)
        encoded = encoder.stream.getvalue()

        decoded = pyamf.get_decoder(pyamf.AMF3, encoded).readElement()

        for i in range(0, max):
            self.assertEquals(id(decoded[0]), id(decoded[i]))

def suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(SATestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
