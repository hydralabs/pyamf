# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.

"""
C{django.db.models} adapter module.

@see: U{Django Project<http://www.djangoproject.com>}

@since: 0.4.1
"""

from django.db.models.base import Model
from django.db.models import fields
from django.db.models.fields import related

import datetime

import pyamf


class DjangoClassAlias(pyamf.ClassAlias):
    def getAttrs(self, obj, codec=None):
        static_attrs, dynamic_attrs = [], []

        if hasattr(self, 'static_attrs'):
            static_attrs = self.static_attrs
        else:
            static_attrs = self.static_attrs = []
            self.fields = {}
            self.columns = []

            for x in obj._meta.fields:
                if x.name not in static_attrs:
                    self.fields[x.name] = x
                    static_attrs.append(x.name)
                    self.columns.append(x.attname)

            for k, v in self.klass.__dict__.iteritems():
                if isinstance(v, property):
                    static_attrs.append(k)
                elif isinstance(v, related.ReverseManyRelatedObjectsDescriptor):
                    if k not in static_attrs:
                        self.fields[k] = v.field
                        static_attrs.append(k)

        # fetch all dynamic attributes
        for key in obj.__dict__.keys():
            if key.startswith('_'):
                continue

            if key in self.static_attrs:
                continue

            if key in self.columns:
                continue

            dynamic_attrs.append(key)

        return static_attrs, dynamic_attrs

    def _encodeValue(self, field, value):
        if value is fields.NOT_PROVIDED:
            return pyamf.Undefined

        # deal with dates ..
        if isinstance(field, fields.DateTimeField):
            return value
        elif isinstance(field, fields.DateField):
            return datetime.datetime(value.year, value.month, value.day, 0, 0, 0)
        elif isinstance(field, fields.TimeField):
            return datetime.datetime(1970, 1, 1,
                value.hour, value.minute, value.second, value.microsecond)

        return value

    def _decodeValue(self, field, value):
        if value is pyamf.Undefined:
            return fields.NOT_PROVIDED

        # deal with dates
        if isinstance(field, fields.DateTimeField):
            return value
        elif isinstance(field, fields.DateField):
            return datetime.date(value.year, value.month, value.day)
        elif isinstance(field, fields.TimeField):
            return datetime.time(value.hour, value.minute, value.second, value.microsecond)

        return value

    def getAttributes(self, obj, codec=None):
        from django.db import models

        san, dan = self.getAttrs(obj)
        static_attrs, dynamic_attrs = {}, {}

        for name in san:
            if name not in self.fields.keys():
                static_attrs[name] = getattr(obj, name)

                continue

            prop = self.fields[name]

            if isinstance(prop, related.ManyToManyField):
                static_attrs[name] = [x for x in getattr(obj, name).all()]
            elif isinstance(prop, models.ForeignKey):
                if '_%s_cache' % name in obj.__dict__:
                    static_attrs[name] = getattr(obj, name)
                else:
                    static_attrs[name] = None
            else:
                static_attrs[name] = self._encodeValue(prop, getattr(obj, name))

        for name in dan:
            dynamic_attrs[name] = getattr(obj, name)

        return static_attrs, dynamic_attrs

    def applyAttributes(self, obj, attrs, codec=None):
        if not hasattr(self, 'static_attrs'):
            self.getAttrs(obj)

        for n, f in self.fields.iteritems():
            attrs[f.attname] = self._decodeValue(f, attrs[n])

        for f in self.klass.__dict__:
            prop = self.klass.__dict__[f]

            if isinstance(prop, property) and f in attrs.keys():
                if prop.fset is None:
                    del attrs[f]

        # primary key of django object must always be set first for
        # relationships with other model objects to work properly
        # and dict.iteritems() does not guarantee order
        #
        # django also forces the use only one attribute as primary key, so
        # our obj._meta.pk.attname check is sufficient)
        try:
            setattr(obj, obj._meta.pk.attname, attrs[obj._meta.pk.attname])
            del attrs[obj._meta.pk.attname]
        except KeyError:
            pass

        return pyamf.ClassAlias.applyAttributes(self, obj, attrs)

pyamf.register_alias_type(DjangoClassAlias, Model)
