# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE for details.

"""
PyAMF Django adapter tests.

@since: 0.3.1
"""

import unittest, sys, os, new

import pyamf
from pyamf.tests import util

class ModelsBaseTestCase(unittest.TestCase):
    def setUp(self):
        self.old_env = os.environ.copy()
        self.mods = sys.modules.copy()

        if 'DJANGO_SETTINGS_MODULE' in os.environ.keys():
            from django import conf
            import copy

            self.mod = copy.deepcopy(conf.settings)
            mod = conf.settings
            self.existing = True
        else:
            os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
            mod = new.module('settings')
            sys.modules['settings'] = mod

            self.existing = False

        setattr(mod, 'DATABASE_ENGINE', 'sqlite3')
        setattr(mod, 'DATABASE_NAME', ':memory:')

    def tearDown(self):
        util.replace_dict(os.environ, self.old_env)
        util.replace_dict(sys.modules, self.mods)

        if self.existing:
            from django import conf
            conf.settings = self.mod

class TypeMapTestCase(ModelsBaseTestCase):
    def test_objects_all(self):
        from django.db import connection, models

        class Spam(models.Model):
            pass

        cursor = connection.cursor()
        cursor.execute('CREATE TABLE adapters_spam (id INTEGER PRIMARY KEY)')

        encoder = pyamf.get_encoder(pyamf.AMF0)

        encoder.writeElement(Spam.objects.all())
        self.assertEquals(encoder.stream.getvalue(), '\n\x00\x00\x00\x00')

        encoder = pyamf.get_encoder(pyamf.AMF3)
        encoder.writeElement(Spam.objects.all())
        self.assertEquals(encoder.stream.getvalue(), '\t\x01\x01')

        cursor.execute('DROP TABLE adapters_spam')

    def test_NOT_PROVIDED(self):
        from django.db.models import fields

        encoder = pyamf.get_encoder(pyamf.AMF0)

        encoder.writeElement(fields.NOT_PROVIDED)
        self.assertEquals(encoder.stream.getvalue(), '\x06')

        encoder = pyamf.get_encoder(pyamf.AMF3)
        encoder.writeElement(fields.NOT_PROVIDED)
        self.assertEquals(encoder.stream.getvalue(), '\x00')

class ClassAliasTestCase(ModelsBaseTestCase):
    def setUp(self):
        ModelsBaseTestCase.setUp(self)

        from pyamf.adapters import _django_db_models_base as models_adapter

        self.adapter = models_adapter

    def test_time(self):
        from django.db import models
        import datetime

        class TestClass(models.Model):
            t = models.TimeField()
            d = models.DateField()
            dt = models.DateTimeField()

        x = TestClass()

        x.t = datetime.time(12, 12, 12)
        x.d = datetime.date(2008, 3, 12)
        x.dt = datetime.datetime(2008, 3, 12, 12, 12, 12)

        alias = self.adapter.DjangoClassAlias(TestClass, None)

        sa, da = alias.getAttributes(x)

        self.assertEquals(sa, {
            'id': None,
            'd': datetime.datetime(2008, 3, 12, 0, 0),
            'dt': datetime.datetime(2008, 3, 12, 12, 12, 12),
            't': datetime.datetime(1970, 1, 1, 12, 12, 12)
        })

        self.assertEquals(da, {})

        y = TestClass()


        alias.applyAttributes(y, {
            'id': None,
            'd': datetime.datetime(2008, 3, 12, 0, 0),
            'dt': datetime.datetime(2008, 3, 12, 12, 12, 12),
            't': datetime.datetime(1970, 1, 1, 12, 12, 12)
        })

        self.assertEquals(y.id, None)
        self.assertEquals(y.d, datetime.date(2008, 3, 12))
        self.assertEquals(y.dt, datetime.datetime(2008, 3, 12, 12, 12, 12))
        self.assertEquals(y.t, datetime.time(12, 12, 12))

    def test_undefined(self):
        from django.db import models
        from django.db.models import fields

        class UndefinedClass(models.Model):
            pass

        alias = self.adapter.DjangoClassAlias(UndefinedClass, None)

        x = UndefinedClass()

        alias.applyAttributes(x, {
            'id': pyamf.Undefined
        })

        self.assertEquals(x.id, fields.NOT_PROVIDED)
    
        x.id = fields.NOT_PROVIDED

        sa, da = alias.getAttributes(x)

        self.assertEquals(da, {})
        self.assertEquals(sa, {'id': pyamf.Undefined})

def suite():
    suite = unittest.TestSuite()

    try:
        import django
    except ImportError, e:
        return suite

    suite.addTest(unittest.makeSuite(TypeMapTestCase))
    suite.addTest(unittest.makeSuite(ClassAliasTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
