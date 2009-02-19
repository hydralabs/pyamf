# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE for details.

"""
C{django.db.models} adapter module.

@see: U{Django Project<http://www.djangoproject.com>}

@since: 0.4.1
"""

import sys

from django.db.models.base import Model
from django.db.models import fields

import datetime

import pyamf

class DjangoClassAlias(pyamf.ClassAlias):
    def getAttrs(self, obj, codec=None):
        static_attrs = None

        if hasattr(self, 'static_attrs'):
            static_attrs = self.static_attrs
        else:
            static_attrs = self.static_attrs = []
            self.foreign_keys = []

            for x in obj._meta.fields:
                static_attrs.append(x.name)

        dynamic_attrs = []

        return static_attrs, dynamic_attrs

    def getAttributes(self, obj, codec=None):
        static_attrs, dynamic_attrs = pyamf.ClassAlias.getAttributes(self, obj)

        for f in obj._meta.fields:
            name = f.attname

            if name not in static_attrs:
                continue

            v = static_attrs[name]

            if v is fields.NOT_PROVIDED:
                static_attrs[name] = pyamf.Undefined
            elif isinstance(f, fields.DateTimeField):
                pass
            elif isinstance(f, fields.DateField):
                static_attrs[name] = datetime.datetime(v.year, v.month, v.day, 0, 0, 0)
            elif isinstance(f, fields.TimeField):
                static_attrs[name] = datetime.datetime(1970, 1, 1, v.hour, v.minute, v.second, v.microsecond)

        return static_attrs, dynamic_attrs

    def applyAttributes(self, obj, attrs, codec=None):
        if not hasattr(self, 'static_attrs'):
            self.getAttrs(obj)

        for f in obj._meta.fields:
            v = attrs[f.attname]

            if v is pyamf.Undefined:
                attrs[f.attname] = fields.NOT_PROVIDED
            elif isinstance(f, fields.DateTimeField):
                pass
            elif isinstance(f, fields.DateField):
                attrs[f.attname] = datetime.date(v.year, v.month, v.day)
            elif isinstance(f, fields.TimeField):
                attrs[f.attname] = datetime.time(v.hour, v.minute, v.second, v.microsecond)

        return pyamf.ClassAlias.applyAttributes(self, obj, attrs)

pyamf.register_alias_type(DjangoClassAlias, Model)
