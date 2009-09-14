# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.

"""
PyAMF Django adapter tests.

@since: 0.3.1
"""

import unittest
import sys
import os
import new
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

        sa, da = alias.getEncodableAttributes(x)

        self.assertEquals(sa, {
            'id': None,
            'd': datetime.datetime(2008, 3, 12, 0, 0),
            'dt': datetime.datetime(2008, 3, 12, 12, 12, 12),
            't': datetime.datetime(1970, 1, 1, 12, 12, 12)
        })

        self.assertEquals(da, None)

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

        y = TestClass()

        alias.applyAttributes(y, {
            'id': None,
            'd': None,
            'dt': None,
            't': None
        })

        self.assertEquals(y.id, None)
        self.assertEquals(y.d, None)
        self.assertEquals(y.dt, None)
        self.assertEquals(y.t, None)

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

        sa, da = alias.getEncodableAttributes(x)

        self.assertEquals(da, None)
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

        self.assertEquals(alias.getEncodableAttributes(x), (
            {'id': None},
            {'numberOfOddPages': 234}
        ))

        # now we test sending the numberOfOddPages attribute
        alias.applyAttributes(x, {'numberOfOddPages': 24, 'id': None})

        # test it hasn't been set
        self.assertEquals(x.numberOfOddPages, 234)

    def test_dynamic(self):
        """
        Test for dynamic property encoding.
        """
        from django.db import models

        class Foo(models.Model):
            pass

        alias = self.adapter.DjangoClassAlias(Foo, 'Book')

        x = Foo()
        x.spam = 'eggs'

        self.assertEquals(alias.getEncodableAttributes(x), (
            {'id': None},
            {'spam': 'eggs'}
        ))

        # now we test sending the numberOfOddPages attribute
        alias.applyAttributes(x, {'spam': 'foo', 'id': None})

        # test it has been set
        self.assertEquals(x.spam, 'foo')


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
        alias = self.adapter.DjangoClassAlias(Article, defer=True)

        self.assertFalse(hasattr(alias, 'fields'))
        sa, da = alias.getEncodableAttributes(a)
        self.assertEquals(sa, {
            'headline': u'This is a test',
            'pub_date': datetime.datetime(2005, 7, 27, 0, 0),
            'id': 1,
        })
        self.assertEquals(da, {
            'reporter': pyamf.Undefined
        })

        self.assertFalse('_reporter_cache' in a.__dict__)
        self.assertEquals(pyamf.encode(a, encoding=pyamf.AMF3).getvalue(),
            '\n;\x01\x11headline\x05id\x11pub_date\x06\x1dThis is a test\x04'
            '\x01\x08\x01BpUYj@\x00\x00\x11reporter\x00\x01')

        del a

        # now with select_related to pull in the reporter object
        a = Article.objects.select_related().filter(pk=1)[0]

        alias = self.adapter.DjangoClassAlias(Article, defer=True)

        self.assertFalse(hasattr(alias, 'fields'))
        self.assertEquals(alias.getEncodableAttributes(a), ({
            'headline': u'This is a test',
            'pub_date': datetime.datetime(2005, 7, 27, 0, 0),
            'id': 1,
        },
        {
            'reporter': r,
        }))

        self.assertTrue('_reporter_cache' in a.__dict__)
        self.assertEquals(pyamf.encode(a, encoding=pyamf.AMF3).getvalue(),
            '\n;\x01\x11headline\x05id\x11pub_date\x06\x1dThis is a test\x04'
            '\x01\x08\x01BpUYj@\x00\x00\x11reporter\nK\x01\x0bemail\x15'
            'first_name\x02\x13last_name\x06!john@example.com\x06\tJohn\x04'
            '\x01\x06\x0bSmith\x01\x01')

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

        sa, da = pub_alias.getEncodableAttributes(test_publication)
        self.assertEquals(sa, {'id': 1, 'title': u'The Python Journal'})
        self.assertEquals(da, None)

        sa, da = art_alias.getEncodableAttributes(test_article)
        self.assertEquals(sa, {
            'headline': u'Django lets you build Web apps easily',
            'id': 1,
            'publications': [p1]
        })
        self.assertEquals(da, None)

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


class I18NTestCase(ModelsBaseTestCase):
    def test_encode(self):
        from django.utils.translation import ugettext_lazy

        self.assertEquals(pyamf.encode(ugettext_lazy('Hello')).getvalue(),
            '\x02\x00\x05Hello')


class PKTestCase(ModelsBaseTestCase):
    """
    See ticket #599 for this. Check to make sure that django pk fields
    are set first
    """

    def test_behaviour(self):
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

        p = Publication(id=None, title='The Python Journal')
        a = Article2(id=None, headline='Django lets you build Web apps easily')

        # Associate the Article with a Publication.
        self.assertRaises(ValueError, lambda a, p: a.publications.add(p), a, p)

        p.save()
        a.save()

        self.assertEquals(a.id, 2)

        article_alias = self.adapter.DjangoClassAlias(Article2, None)
        x = Article2()

        article_alias.applyAttributes(x, {
            'headline': 'Foo bar!',
            'id': 2,
            'publications': [p]
        })

    def test_none(self):
        """
        See #556. Make sure that PK fields with a value of 0 are actually set
        to C{None}.
        """
        from django.db import models

        class Foo(models.Model):
            pass

        self.resetDB()

        alias = self.adapter.DjangoClassAlias(Foo, None)

        x = Foo()

        self.assertEquals(x.id, None)

        alias.applyAttributes(x, {
            'id': 0
        })

        self.assertEquals(x.id, None)


class ModelInheritanceTestCase(ModelsBaseTestCase):
    """
    Tests for L{Django model inheritance<http://docs.djangoproject.com/en/dev/topics/db/models/#model-inheritance>}
    """

    def test_abstract(self):
        from django.db import models

        class CommonInfo(models.Model):
            name = models.CharField(max_length=100)
            age = models.PositiveIntegerField()

            class Meta:
                abstract = True

        class Student(CommonInfo):
            home_group = models.CharField(max_length=5)

        self.resetDB()

        alias = self.adapter.DjangoClassAlias(Student)

        x = Student()

        sa, da = alias.getEncodableAttributes(x)

        self.assertEquals(sa, {
            'age': None,
            'home_group': '',
            'id': None,
            'name': ''
        })

        self.assertEquals(da, None)

    def test_concrete(self):
        from django.db import models

        class Place(models.Model):
            name = models.CharField(max_length=50)
            address = models.CharField(max_length=80)

        class Restaurant(Place):
            serves_hot_dogs = models.BooleanField()
            serves_pizza = models.BooleanField()

        self.resetDB()

        alias = self.adapter.DjangoClassAlias(Place)
        x = Place()

        sa, da = alias.getEncodableAttributes(x)

        self.assertEquals(sa, {
            'id': None,
            'name': '',
            'address': ''
        })

        self.assertEquals(da, None)

        alias = self.adapter.DjangoClassAlias(Restaurant)
        x = Restaurant()

        sa, da = alias.getEncodableAttributes(x)

        self.assertEquals(sa, {
            'id': None,
            'name': '',
            'address': '',
            'serves_hot_dogs': False,
            'serves_pizza': False
        })

        self.assertEquals(da, None)


class MockFile(object):
    """
    mock for L{django.core.files.base.File}
    """

    def chunks(self):
        return []

    def __len__(self):
        return 0

    def read(self, n):
        return ''


class FieldsTestCase(ModelsBaseTestCase):
    """
    Tests for L{fields}
    """

    def tearDown(self):
        ModelsBaseTestCase.tearDown(self)

        try:
            os.unlink(os.path.join(os.getcwd(), 'foo'))
        except OSError:
            raise
            pass

    def test_file(self):
        from django.db import models

        self.executed = False

        def get_studio_watermark(*args, **kwargs):
            self.executed = True

            return 'foo'

        class Image(models.Model):
            file = models.FileField(upload_to=get_studio_watermark)
            text = models.CharField(max_length=64)

        self.resetDB()

        alias = self.adapter.DjangoClassAlias(Image)

        i = Image()
        i.file.save('bar', MockFile())

        i.save()

        sa, da = alias.getEncodableAttributes(i)

        self.assertEquals(sa, {'text': '', 'id': 1, 'file': u'foo'})
        self.assertEquals(da, None)
        self.assertTrue(self.executed)

        attrs = alias.getDecodableAttributes(i, sa)

        self.assertEquals(attrs, {'text': ''})


class ImageTestCase(ModelsBaseTestCase):
    """
    Tests for L{fields}
    """

    def test_image(self):
        from django.db import models

        self.executed = False

        def get_studio_watermark(*args, **kwargs):
            self.executed = True

            return 'foo'

        class Profile(models.Model):
            file = models.ImageField(upload_to=get_studio_watermark)
            text = models.CharField(max_length=64)

        self.resetDB()

        alias = self.adapter.DjangoClassAlias(Profile)

        i = Profile()
        i.file.save('bar', MockFile())

        i.save()

        sa, da = alias.getEncodableAttributes(i)

        self.assertEquals(sa, {'text': '', 'id': 1, 'file': u'foo_'})
        self.assertEquals(da, None)
        self.assertTrue(self.executed)

        attrs = alias.getDecodableAttributes(i, sa)

        self.assertEquals(attrs, {'text': ''})


class ReferenceTestCase(ModelsBaseTestCase):
    """
    Test case to make sure that the same object from the database is encoded
    by reference.
    """

    def setUp(self):
        ModelsBaseTestCase.setUp(self)

        from django.db import models

        class ParentReference(models.Model):
            name = models.CharField(max_length=100)
            bar = models.ForeignKey('ChildReference', null=True)

        class ChildReference(models.Model):
            name = models.CharField(max_length=100)
            foo = models.ForeignKey(ParentReference)

        self.ParentReference = ParentReference
        self.ChildReference = ChildReference

        self.resetDB()

    def tearDown(self):
        ModelsBaseTestCase.tearDown(self)

    def test_not_referenced(self):
        """
        Test to ensure that we observe the correct behaviour in the Django
        ORM.
        """
        f = self.ParentReference()
        f.name = 'foo'

        b = self.ChildReference()
        b.name = 'bar'

        f.save()
        b.foo = f
        b.save()
        f.bar = b
        f.save()

        self.assertEquals(f.id, 1)
        foo = self.ParentReference.objects.select_related().get(id=1)

        self.assertFalse(foo.bar.foo is foo)

    def test_referenced_encode(self):
        f = self.ParentReference()
        f.name = 'foo'

        b = self.ChildReference()
        b.name = 'bar'

        f.save()
        b.foo = f
        b.save()
        f.bar = b
        f.save()

        self.assertEquals(f.id, 2)
        foo = self.ParentReference.objects.select_related().get(id=2)

        # ensure the referenced attribute resolves
        foo.bar.foo

        self.assertEquals(pyamf.encode(foo).getvalue(), '\x03\x00\x02id\x00'
            '@\x00\x00\x00\x00\x00\x00\x00\x00\x04name\x02\x00\x03foo\x00'
            '\x03bar\x03\x00\x02id\x00@\x00\x00\x00\x00\x00\x00\x00\x00\x04na'
            'me\x02\x00\x03bar\x00\x03foo\x07\x00\x00\x00\x00\t\x00\x00\t')


def suite():
    suite = unittest.TestSuite()

    try:
        import django
    except ImportError:
        return suite

    test_cases = [
        TypeMapTestCase,
        ClassAliasTestCase,
        ForeignKeyTestCase,
        I18NTestCase,
        PKTestCase,
        ModelInheritanceTestCase,
        FieldsTestCase,
        ReferenceTestCase
    ]

    try:
        import PIL
    except:
        pass
    else:
        test_cases.append(ImageTestCase)

    for tc in test_cases:
        suite.addTest(unittest.makeSuite(tc))

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
