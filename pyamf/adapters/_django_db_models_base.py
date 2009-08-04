# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.

"""
C{django.db.models} adapter module.

@see: U{Django Project<http://www.djangoproject.com>}

@since: 0.4.1
"""

from django.db.models.base import Model
from django.db import models
from django.db.models import fields
from django.db.models.fields import related, files

import datetime

import pyamf


class DjangoClassAlias(pyamf.ClassAlias):
    """
    """

    def getCustomProperties(self):
        self.fields = {}
        self.relations = {}
        self.columns = []

        self.meta = self.klass._meta

        for x in self.meta.local_fields:
            if isinstance(x, files.FileField):
                self.readonly_attrs.update([x.name])

            if not isinstance(x, related.ForeignKey):
                self.fields[x.name] = x
            else:
                self.relations[x.name] = x

            self.columns.append(x.attname)

        for k, v in self.klass.__dict__.iteritems():
            if isinstance(v, related.ReverseManyRelatedObjectsDescriptor):
                self.fields[k] = v.field

        parent_fields = []

        for field in self.meta.parents.values():
            parent_fields.append(field.attname)
            del self.relations[field.name]

        self.exclude_attrs.update(parent_fields)

        props = self.fields.keys()

        self.static_attrs.update(props)
        self.encodable_properties.update(props)
        self.decodable_properties.update(props)

    def _compile_base_class(self, klass):
        if klass is Model:
            return

        pyamf.ClassAlias._compile_base_class(self, klass)

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
        elif isinstance(value, files.FieldFile):
            return value.name

        return value

    def _decodeValue(self, field, value):
        if value is pyamf.Undefined:
            return fields.NOT_PROVIDED

        if isinstance(field, fields.AutoField) and value == 0:
            return None
        elif isinstance(field, fields.DateTimeField):
            # deal with dates
            return value
        elif isinstance(field, fields.DateField):
            return datetime.date(value.year, value.month, value.day)
        elif isinstance(field, fields.TimeField):
            return datetime.time(value.hour, value.minute, value.second, value.microsecond)

        return value

    def getEncodableAttributes(self, obj, **kwargs):
        sa, da = pyamf.ClassAlias.getEncodableAttributes(self, obj, **kwargs)

        for name, prop in self.fields.iteritems():
            if name not in sa:
                continue

            if isinstance(prop, related.ManyToManyField):
                sa[name] = [x for x in getattr(obj, name).all()]
            else:
                sa[name] = self._encodeValue(prop, getattr(obj, name))

        if not da:
            da = {}

        keys = da.keys()

        for key in keys:
            if key.startswith('_'):
                del da[key]
            elif key in self.columns:
                del da[key]

        for name, relation in self.relations.iteritems():
            if '_%s_cache' % name in obj.__dict__:
                da[name] = getattr(obj, name)
            else:
                da[name] = pyamf.Undefined

        if not da:
            da = None

        return sa, da

    def getDecodableAttributes(self, obj, attrs, **kwargs):
        attrs = pyamf.ClassAlias.getDecodableAttributes(self, obj, attrs, **kwargs)

        for n in self.decodable_properties:
            f = self.fields[n]

            attrs[f.attname] = self._decodeValue(f, attrs[n])

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

        return attrs


pyamf.register_alias_type(DjangoClassAlias, Model)
