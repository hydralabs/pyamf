# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
SQLAlchemy adapter module.

@see: U{SQLAlchemy homepage (external)<http://www.sqlalchemy.org>}

@since: 0.4
"""

import sqlalchemy
from sqlalchemy.orm import collections
from sqlalchemy.orm.util import class_mapper

import pyamf
from pyamf.adapters import util

UnmappedInstanceError = None

try:
    class_mapper(dict())
except Exception, e:
    UnmappedInstanceError = e.__class__

class SaMappedClassAlias(pyamf.ClassAlias):
    KEY_ATTR = 'sa_key'
    LAZY_ATTR = 'sa_lazy'
    EXCLUDED_ATTRS = ['_sa_instance_state']

    def _getMapper(self, obj):
        if hasattr(self, 'primary_mapper'):
            return self.primary_mapper

        try:
            self.primary_mapper = sqlalchemy.orm.util.object_mapper(obj)
        except UnmappedInstanceError:
            self.primary_mapper = None

        return self.primary_mapper

    def getAttrs(self, obj, *args, **kwargs):
        """
        Returns list of allowed attribute names for this class.
        """
        mapper = self._getMapper(obj)

        if mapper is None:
            return pyamf.ClassAlias.getAttrs(self, obj, *args, **kwargs)

        static_attrs = [self.KEY_ATTR, self.LAZY_ATTR]
        dynamic_attrs = []

        for prop in mapper.iterate_properties:
            static_attrs.append(prop.key)

        for key in obj.__dict__.keys():
            if key in self.EXCLUDED_ATTRS:
                continue

            if key not in static_attrs:
                dynamic_attrs.append(key)

        return static_attrs, dynamic_attrs

    def getAttributes(self, obj, *args, **kwargs):
        """
        Returns a C{tuple} containing a dict of static and dynamic attributes
        for C{obj}.
        """
        mapper = self._getMapper(obj)

        if mapper is None:
            return pyamf.ClassAlias.getAttributes(self, obj, *args, **kwargs)

        static_attrs = {}
        dynamic_attrs = {}
        lazy_attrs = []

        static_attr_names, dynamic_attr_names = self.getAttrs(obj)

        for attr in static_attr_names:
             if attr in obj.__dict__:
                 static_attrs[attr] = getattr(obj, attr)
             else:
                 lazy_attrs.append(attr)
                 static_attrs[attr] = pyamf.Undefined

        for attr in dynamic_attr_names:
            if attr in obj.__dict__:
                 dynamic_attrs[attr] = getattr(obj, attr)

        static_attrs[self.KEY_ATTR] = mapper.primary_key_from_instance(obj)
        static_attrs[self.LAZY_ATTR] = lazy_attrs
        return static_attrs, dynamic_attrs

    def applyAttributes(self, obj, attrs, *args, **kwargs):
        """
        Add decoded attributes to instance.
        """
        mapper = self._getMapper(obj)

        if mapper is None:
            pyamf.ClassAlias.applyAttributes(self, obj, attrs, *args, **kwargs)
            return

        # Don't set lazy-loaded attrs
        if attrs.has_key(self.LAZY_ATTR) and attrs[self.LAZY_ATTR] is not None:
            static_attrs, dynamic_attrs = self.getAttrs(obj)

            for attr in static_attrs:
                if attrs.has_key(attr) and \
                    (attrs[attr] is None or attrs[attr] is pyamf.Undefined) and \
                    attr in attrs[self.LAZY_ATTR]:
                    del attrs[attr]
            del attrs[self.LAZY_ATTR]

        if attrs.has_key(self.KEY_ATTR):
            del attrs[self.KEY_ATTR]

        pyamf.util.set_attrs(obj, attrs)

def is_class_sa_mapped(klass):
    try:
        class_mapper(klass)
    except UnmappedInstanceError:
        return False

    return True

pyamf.register_alias_type(SaMappedClassAlias, is_class_sa_mapped)

pyamf.add_type(collections.InstrumentedList, util.to_list)
pyamf.add_type(collections.InstrumentedDict, util.to_dict)
pyamf.add_type(collections.InstrumentedSet, util.to_set)
