# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
PyAMF Django adapter tests.

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}
@since: 0.3.1
"""

import unittest, sys, os, new

import pyamf

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
        os.environ = self.old_env
        sys.modules = self.mods

        if self.existing:
            from django import conf
            conf.settings = self.mod

class TypeMapTestCase(ModelsBaseTestCase):
    def test_objects_all(self):
        try:
            from django.db import models, connection

            class Spam(models.Model):
                pass
        except:
            return

        cursor = connection.cursor()
        cursor.execute('CREATE TABLE adapters_spam (id INTEGER PRIMARY KEY)')

        encoder = pyamf.get_encoder(pyamf.AMF0)

        encoder.writeElement(Spam.objects.all())
        self.assertEquals(encoder.stream.getvalue(), '\n\x00\x00\x00\x00')

        encoder = pyamf.get_encoder(pyamf.AMF3)
        encoder.writeElement(Spam.objects.all())
        self.assertEquals(encoder.stream.getvalue(), '\t\x01\x01')

        cursor.execute('DROP TABLE adapters_spam')

def suite():
    suite = unittest.TestSuite()

    suite.addTest(unittest.makeSuite(TypeMapTestCase))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
