# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE for details.

"""
PyAMF Django adapter tests.

@since: 0.3.1
"""

import unittest, sys, os, new
import datetime

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

        app = new.module('adapters')

        app_models = new.module('adapters.models')
        setattr(app, 'models', app_models)
        setattr(app, '__file__', '')
        setattr(app_models, '__file__', '')

        sys.modules['adapters'] = app
        sys.modules['adapters.models'] = app_models

        self.app = app
        self.models = app_models

        setattr(mod, 'DATABASE_ENGINE', 'sqlite3')
        setattr(mod, 'DATABASE_NAME', ':memory:')
        setattr(mod, 'INSTALLED_APPS', ('adapters',))
        setattr(mod, 'USE_I18N', False)

        from pyamf.adapters import _django_db_models_base as models_adapter

        self.adapter = models_adapter

    def tearDown(self):
        util.replace_dict(os.environ, self.old_env)
        util.replace_dict(sys.modules, self.mods)

        if self.existing:
            from django import conf
            conf.settings = self.mod

    def resetDB(self):
        from django.db import connection
        import sys

        old_stderr = sys.stderr
        sys.stderr = util.NullFileDescriptor()

        self.db_name = connection.creation.create_test_db(0, autoclobber=True)

        sys.stderr = old_stderr

class TypeMapTestCase(ModelsBaseTestCase):
    def test_objects_all(self):
        from django.db import models

        class Spam(models.Model):
            pass

        self.resetDB()
        encoder = pyamf.get_encoder(pyamf.AMF0)

        encoder.writeElement(Spam.objects.all())
        self.assertEquals(encoder.stream.getvalue(), '\n\x00\x00\x00\x00')

        encoder = pyamf.get_encoder(pyamf.AMF3)
        encoder.writeElement(Spam.objects.all())
        self.assertEquals(encoder.stream.getvalue(), '\t\x01\x01')

    def test_NOT_PROVIDED(self):
        from django.db.models import fields

        encoder = pyamf.get_encoder(pyamf.AMF0)

        encoder.writeElement(fields.NOT_PROVIDED)
        self.assertEquals(encoder.stream.getvalue(), '\x06')

        encoder = pyamf.get_encoder(pyamf.AMF3)
        encoder.writeElement(fields.NOT_PROVIDED)
        self.assertEquals(encoder.stream.getvalue(), '\x00')

class ClassAliasTestCase(ModelsBaseTestCase):
    def test_time(self):
        from django.db import models

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

    def test_non_field_prop(self):
        from django.db import models

        class Book(models.Model):
            def _get_number_of_odd_pages(self):
                return 234

            # note the lack of a setter callable ..
            numberOfOddPages = property(_get_number_of_odd_pages)

        alias = self.adapter.DjangoClassAlias(Book, 'Book')

        x = Book()

        self.assertEquals(alias.getAttrs(x), (
            ['id', 'numberOfOddPages'],
            []
        ))

        self.assertEquals(alias.getAttributes(x), (
            {'numberOfOddPages': 234, 'id': None},
            {}
        ))

        # now we test sending the numberOfOddPages attribute
        alias.applyAttributes(x, {'numberOfOddPages': 24, 'id': None})

        # test it hasn't been set
        self.assertEquals(x.numberOfOddPages, 234)

class ForeignKeyTestCase(ModelsBaseTestCase):
    def test_one_to_many(self):
        from django.db import models

        class Reporter(models.Model):
            first_name = models.CharField(max_length=30)
            last_name = models.CharField(max_length=30)
            email = models.EmailField()

            def __unicode__(self):
                return u"%s %s" % (self.first_name, self.last_name)

        class Article(models.Model):
            headline = models.CharField(max_length=100)
            pub_date = models.DateField()
            reporter = models.ForeignKey(Reporter)

            def __unicode__(self):
                return self.headline

        self.resetDB()

        # initialise the db ..
        r = Reporter(first_name='John', last_name='Smith', email='john@example.com')
        r.save()

        r2 = Reporter(first_name='Paul', last_name='Jones', email='paul@example.com')
        r2.save()

        a = Article(headline="This is a test", pub_date=datetime.date(2005, 7, 27), reporter=r)
        a.save()

        self.assertEquals(a.id, 1)

        del a

        a = Article.objects.filter(pk=1)[0]

        self.assertFalse('_reporter_cache' in a.__dict__)
        a.reporter
        self.assertTrue('_reporter_cache' in a.__dict__)

        del a

        a = Article.objects.filter(pk=1)[0]
        alias = self.adapter.DjangoClassAlias(Reporter, None)

        self.assertFalse(hasattr(alias, 'fields'))
        self.assertEquals(alias.getAttrs(a), (
            ['id', 'headline', 'pub_date', 'reporter'],
            []
        ))
        self.assertTrue(hasattr(alias, 'fields'))
        self.assertEquals(alias.fields.keys(),
            ['headline', 'pub_date', 'id', 'reporter'])

        self.assertEquals(alias.getAttributes(a), (
            {
                'headline': u'This is a test',
                'pub_date': datetime.datetime(2005, 7, 27, 0, 0),
                'id': 1,
                'reporter': None,
            },
            {}
        ))

        self.assertFalse('_reporter_cache' in a.__dict__)
        self.assertEquals(pyamf.encode(a, encoding=pyamf.AMF3).getvalue(),
            '\nK\x01\x05id\x11headline\x11pub_date\x11reporter\x04\x01\x06'
            '\x1dThis is a test\x08\x01BpUYj@\x00\x00\x01\x01')

        del a

        # now with select_related to pull in the reporter object
        a = Article.objects.select_related().filter(pk=1)[0]

        alias = self.adapter.DjangoClassAlias(Reporter, None)

        self.assertFalse(hasattr(alias, 'fields'))
        self.assertEquals(alias.getAttrs(a), (
            ['id', 'headline', 'pub_date', 'reporter'],
            []
        ))
        self.assertTrue(hasattr(alias, 'fields'))
        self.assertEquals(alias.fields.keys(),
            ['headline', 'pub_date', 'id', 'reporter'])

        self.assertEquals(alias.getAttributes(a), (
            {
                'headline': u'This is a test',
                'pub_date': datetime.datetime(2005, 7, 27, 0, 0),
                'id': 1,
                'reporter': r,
            },
            {}
        ))

        self.assertTrue('_reporter_cache' in a.__dict__)
        self.assertEquals(pyamf.encode(a, encoding=pyamf.AMF3).getvalue(),
            '\nK\x01\x05id\x11headline\x11pub_date\x11reporter'
            '\x04\x01\x06\x1dThis is a test\x08\x01BpUYj@\x00\x00\nK'
            '\x01\x00\x15first_name\x13last_name\x0bemail\x04\x01\x06\tJohn'
            '\x06\x0bSmith\x06!john@example.com\x01\x01')

    def test_many_to_many(self):
        from django.db import models

        class Publication(models.Model):
            title = models.CharField(max_length=30)

            def __unicode__(self):
                return self.title

            class Meta:
                ordering = ('title',)

        class Article2(models.Model):
            headline = models.CharField(max_length=100)
            publications = models.ManyToManyField(Publication)

            def __unicode__(self):
                return self.headline

            class Meta:
                ordering = ('headline',)

        self.resetDB()

        # install some test data - taken from
        # http://www.djangoproject.com/documentation/models/many_to_many/
        p1 = Publication(id=None, title='The Python Journal')
        p1.save()
        p2 = Publication(id=None, title='Science News')
        p2.save()
        p3 = Publication(id=None, title='Science Weekly')
        p3.save()

        # Create an Article.
        a1 = Article2(id=None, headline='Django lets you build Web apps easily')
        a1.save()
        self.assertEquals(a1.id, 1)

        # Associate the Article with a Publication.
        a1.publications.add(p1)

        pub_alias = self.adapter.DjangoClassAlias(Publication, None)
        art_alias = self.adapter.DjangoClassAlias(Article2, None)

        test_publication = Publication.objects.filter(pk=1)[0]
        test_article = Article2.objects.filter(pk=1)[0]

        self.assertEquals(pub_alias.getAttrs(test_publication), (
            ['id', 'title'],
            []
        ))

        self.assertEquals(art_alias.getAttrs(test_article), (
            ['id', 'headline', 'publications'],
            []
        ))

        self.assertEquals(pub_alias.getAttributes(test_publication), (
            {'id': 1, 'title': u'The Python Journal'},
            {}
        ))

        self.assertEquals(art_alias.getAttributes(test_article), (
            {
                'headline': u'Django lets you build Web apps easily',
                'id': 1,
                'publications': [p1]
            },
            {},
        ))

        x = Article2()
        art_alias.applyAttributes(x, {
            'headline': u'Test',
            'id': 1,
            'publications': [p1]
        })

        self.assertEquals(x.headline, u'Test')
        self.assertEquals(x.id, 1)

        p = x.publications.all()

        self.assertEquals(len(p), 1)
        self.assertEquals(p[0], p1)

def suite():
    suite = unittest.TestSuite()

    try:
        import django
    except ImportError, e:
        return suite

    test_cases = [
        TypeMapTestCase,
        ClassAliasTestCase,
        ForeignKeyTestCase
    ]

    for tc in test_cases:
        suite.addTest(unittest.makeSuite(tc))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
