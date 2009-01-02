# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE for details.

"""
Google App Engine adapter module.

Sets up basic type mapping and class mappings for using the Datastore API
in Google App Engine.

@see: U{Datastore API on Google App Engine (external)
<http://code.google.com/appengine/docs/datastore>}

@since: 0.3.1
"""

from google.appengine.ext import db
import datetime

import pyamf

class ModelStub(object):
    def __init__(self):
        for attr in DataStoreClassAlias.INTERNAL_ATTRS:
            setattr(self, attr, None)

class DataStoreClassAlias(pyamf.ClassAlias):
    # The name of the attribute used to represent the key
    KEY_ATTR = '_key'

    # A list of private attributes on a db.Model/db.Expando list that need to
    # be synced with the datastore instance
    INTERNAL_ATTRS = ['_entity', '_parent', '_key_name', '_app', '_parent_key']

    def getAttrs(self, obj):
        """
        @since: 0.4
        """
        static_attrs, dynamic_attrs = pyamf.ClassAlias.getAttrs(self, obj)

        if static_attrs is None:
            static_attrs = obj.properties().keys()

        if obj.is_saved():
            static_attrs.insert(0, self.KEY_ATTR)

        if dynamic_attrs is None:
            dynamic_attrs = obj.dynamic_properties()

        return static_attrs, dynamic_attrs

    def getAttributes(self, obj):
        static_attrs = {}
        dynamic_attrs = {}
        static_attrs_names, dynamic_attrs_names = self.getAttrs(obj)

        if self.KEY_ATTR in static_attrs_names:
            static_attrs_names.remove(self.KEY_ATTR)

        for a in static_attrs_names:
            static_attrs[a] = getattr(obj, a)

        if obj.is_saved():
            static_attrs[self.KEY_ATTR] = str(obj.key())

        for a in dynamic_attrs_names:
            dynamic_attrs[a] = getattr(obj, a)

        return static_attrs, dynamic_attrs

    def createInstance(self):
        return ModelStub()

    def applyAttributes(self, obj, attrs):
        new_obj = None

        if DataStoreClassAlias.KEY_ATTR in attrs.keys() and attrs[DataStoreClassAlias.KEY_ATTR] is not None:
            new_obj = self.klass.get(attrs[DataStoreClassAlias.KEY_ATTR])
            del attrs[DataStoreClassAlias.KEY_ATTR]

        properties = self.klass.properties()
        p_keys = properties.keys()

        if new_obj is not None:
            for a in DataStoreClassAlias.INTERNAL_ATTRS:
                if hasattr(new_obj, a):
                    setattr(obj, a, getattr(new_obj, a))

            for k in self.klass.properties().keys():
                setattr(obj, k, getattr(new_obj, k))

            for k in new_obj.dynamic_properties():
                setattr(obj, k, getattr(new_obj, k))

        obj.__class__ = self.klass

        for k, v in attrs.iteritems():
            if k in p_keys:
                prop = properties[k]

                if isinstance(v, datetime.datetime):
                    if isinstance(prop, db.DateProperty):
                        v = v.date()
                    elif isinstance(prop, db.TimeProperty):
                        v = v.time()

            setattr(obj, k, v)

def handleQuery(q):
    if q.count() == 0:
        return []

    return [i for i in q]

pyamf.add_type(db.Query, handleQuery)
pyamf.register_alias_type(DataStoreClassAlias, db.Model, db.Expando)
