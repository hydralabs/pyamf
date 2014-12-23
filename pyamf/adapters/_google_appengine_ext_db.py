# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Google App Engine adapter module.

Sets up basic type mapping and class mappings for using the Datastore API
in Google App Engine.

@see: U{Datastore API on Google App Engine<http://
    code.google.com/appengine/docs/python/datastore>}
@since: 0.3.1
"""

import logging

from google.appengine.api import datastore
from google.appengine.ext import db
from google.appengine.ext.db import polymodel
import datetime


import pyamf
from pyamf.adapters import util



class ModelStub(object):
    """
    This class represents a C{db.Model} or C{db.Expando} class as the typed
    object is being read from the AMF stream. Once the attributes have been
    read from the stream and through the magic of Python, the instance of this
    class will be converted into the correct type.

    @ivar klass: The referenced class either C{db.Model} or C{db.Expando}.
        This is used so we can proxy some of the method calls during decoding.
    @type klass: C{db.Model} or C{db.Expando}
    @see: L{DataStoreClassAlias.applyAttributes}
    """

    def __init__(self, klass):
        self.klass = klass

    def properties(self):
        return self.klass.properties()

    def dynamic_properties(self):
        return []


class GAEReferenceCollection(dict):
    """
    This helper class holds a dict of klass to key/objects loaded from the
    Datastore.

    @since: 0.4.1
    """

    def _getClass(self, klass):
        if not issubclass(klass, (db.Model, db.Expando)):
            raise TypeError('expected db.Model/db.Expando class, got %s' % (klass,))

        return self.setdefault(klass, {})

    def getClassKey(self, klass, key):
        """
        Return an instance based on klass/key.

        If an instance cannot be found then C{KeyError} is raised.

        @param klass: The class of the instance.
        @param key: The key of the instance.
        @return: The instance linked to the C{klass}/C{key}.
        @rtype: Instance of L{klass}.
        """
        d = self._getClass(klass)

        return d[key]

    def addClassKey(self, klass, key, obj):
        """
        Adds an object to the collection, based on klass and key.

        @param klass: The class of the object.
        @param key: The datastore key of the object.
        @param obj: The loaded instance from the datastore.
        """
        d = self._getClass(klass)

        d[key] = obj


class StubCollection(object):
    """
    """


    def __init__(self):
        self.stubs = {}
        self.to_fetch = []
        self.by_key = {}
        self.fetched_entities = None


    def addStub(self, stub, alias, attrs, key):
        """
        """
        self.stubs[stub] = (alias.klass, attrs, key)

        if key:
            self.by_key[stub] = key

            self.to_fetch.append(key)


    def transformStub(self, stub, klass, attrs, key):
        stub.__class__ = klass

        for k, v in attrs.items():
            if not isinstance(v, ModelStub):
                continue

            self.transform(v)

        if key is None:
            stub.__init__(**attrs)

            return

        ds_entity = self.fetched_entities.get(key, None)

        if not ds_entity:
            attrs['key'] = key
            stub.__init__(**attrs)
        else:
            stub.__dict__.update(ds_entity.__dict__)

            for k, v in attrs.items():
                setattr(stub, k, v)


    def fetchEntities(self):
        return dict(zip(self.to_fetch, db.get(self.to_fetch)))


    def transform(self, stub=None):
        if self.fetched_entities is None:
            self.fetched_entities = self.fetchEntities()

        if stub is not None:
            klass, attrs, key = self.stubs.pop(stub)

            self.transformStub(stub, klass, attrs, key)

            return

        while self.stubs:
            stub = iter(self.stubs).next()

            klass, attrs, key = self.stubs.pop(stub)

            self.transformStub(stub, klass, attrs, key)


class DataStoreClassAlias(pyamf.ClassAlias):
    """
    This class contains all the business logic to interact with Google's
    Datastore API's. Any C{db.Model} or C{db.Expando} classes will use this
    class alias for encoding/decoding.

    We also add a number of indexes to the encoder context to aggressively
    decrease the number of Datastore API's that we need to complete.
    """

    # The name of the attribute used to represent the key
    KEY_ATTR = 'keyStr'

    def _compile_base_class(self, klass):
        if klass in (db.Model, polymodel.PolyModel):
            return

        pyamf.ClassAlias._compile_base_class(self, klass)

    def getCustomProperties(self):
        props = [self.KEY_ATTR]
        self.reference_properties = {}
        self.properties = {}
        reverse_props = []

        for name, prop in self.klass.properties().iteritems():
            self.properties[name] = prop

            props.append(name)

            if isinstance(prop, db.ReferenceProperty):
                self.reference_properties[name] = prop

        if issubclass(self.klass, polymodel.PolyModel):
            del self.properties['_class']
            props.remove('_class')

        # check if the property is a defined as a collection_name. These types
        # of properties are read-only and the datastore freaks out if you
        # attempt to meddle with it. We delete the attribute entirely ..
        for name, value in self.klass.__dict__.iteritems():
            if isinstance(value, db._ReverseReferenceProperty):
                reverse_props.append(name)

        self.encodable_properties.update(self.properties.keys())
        self.decodable_properties.update(self.properties.keys())
        self.readonly_attrs.update(reverse_props)

        if not self.reference_properties:
            self.reference_properties = None

        if not self.properties:
            self.properties = None

    def _finalise_compile(self):
        pyamf.ClassAlias._finalise_compile(self)

        self.shortcut_decode = False

    def createInstance(self, codec=None):
        return ModelStub()

    def getAttribute(self, obj, attr, default=None, codec=None):
        """
        """
        def _():
            try:
                return super(DataStoreClassAlias, self).getAttribute(
                    obj, attr, default, codec)
            except db.ReferencePropertyResolveError:
                return None

        if codec is None:
            return _()

        if not self.reference_properties:
            return _()

        try:
            prop = self.reference_properties[attr]
        except KeyError:
            return _()

        context = pyamf.get_context(codec)
        gae_objects = getGAEObjects(context)
        klass = prop.reference_class
        key = prop.get_value_for_datastore(obj)

        if key is None:
            return _()

        try:
            return gae_objects.getClassKey(klass, key)
        except KeyError:
            try:
                ref_obj = getattr(obj, attr)
            except db.Error, e:
                # woo hack
                if str(e).startswith('ReferenceProperty failed to be resolved'):
                    logging.error(str(e))
                    logging.info('Attempted to get %r on %r with key %r',
                        attr, type(obj), key)

                    return None

                raise e

            gae_objects.addClassKey(klass, key, ref_obj)

            return ref_obj

    def getEncodableAttributes(self, obj, codec=None):
        attrs = pyamf.ClassAlias.getEncodableAttributes(self, obj, codec=codec)

        for k in attrs.keys()[:]:
            if k.startswith('_'):
                del attrs[k]

        for attr in obj.dynamic_properties():
            attrs[attr] = getattr(obj, attr)

        attrs[self.KEY_ATTR] = str(obj.key()) if obj.is_saved() else None

        return attrs

    def getEntityFromAttrs(self, attrs, key=None):
        """
        """
        if key is None:
            e = datastore.Entity(self.klass.kind())
        else:
            raise RuntimeError('entity from key')

        e.update(attrs)

        return e

    def getStubCollection(self):
        return StubCollection()

    def getDecodableAttributes(self, obj, attrs, codec=None):
        key = attrs.pop(self.KEY_ATTR, None)

        attrs = pyamf.ClassAlias.getDecodableAttributes(self, obj, attrs, codec=codec)

        if self.properties:
            for k in [k for k in attrs if k in self.properties]:
                prop = self.properties[k]
                v = attrs[k]

                if isinstance(prop, db.FloatProperty) and isinstance(v, (int, long)):
                    attrs[k] = float(v)
                elif isinstance(prop, db.IntegerProperty):
                    if v is None:
                        v = 0
                    x = long(v)

                    # only convert the type if there is no mantissa - otherwise
                    # let the chips fall where they may
                    if isinstance(v, float):
                        if x == v:
                            attrs[k] = x
                    else:
                        attrs[k] = x
                elif isinstance(prop, db.ListProperty):
                    if v is None:
                        attrs[k] = []

                        continue

                    # this will actually be given as a list of strings that
                    # need to be converted to longs
                    if prop.item_type == long:
                        for i, x in enumerate(v):
                            v[i] = long(x)

                    # there is an issue with large ints and ListProperty(int)
                    # AMF leaves ints > amf3.MAX_29B_INT as floats
                    # db.ListProperty complains pretty hard in this case so
                    # we try to work around the issue.
                    elif prop.item_type == int:
                        for i, x in enumerate(v):
                            if isinstance(x, float) and x == long(x):
                                y = long(x)

                                # only convert the type if there is no mantissa
                                # otherwise let the chips fall where they may
                                if x == y:
                                    v[i] = y

                elif isinstance(v, datetime.datetime):
                    # Date/Time Property fields expect specific types of data
                    # whereas PyAMF only decodes into datetime.datetime objects.
                    if isinstance(prop, db.DateProperty):
                        attrs[k] = v.date()
                    elif isinstance(prop, db.TimeProperty):
                        attrs[k] = v.time()

        e = pyamf.get_context(codec)

        try:
            stubs = e['stubs']
        except KeyError:
            stubs = e['stubs'] = self.getStubCollection()

        if key:
            key = db.Key(key)

        stubs.addStub(obj, self, attrs, key)

        return {}


def getGAEObjects(context):
    """
    Returns a reference to the C{gae_objects} on the context. If it doesn't
    exist then it is created.

    @param context: The context to load the C{gae_objects} index from.
    @return: The C{gae_objects} index reference.
    @rtype: Instance of L{GAEReferenceCollection}
    @since: 0.4.1
    """
    try:
        return context['gae_objects']
    except KeyError:
        r = context['gae_objects'] = GAEReferenceCollection()

        return r


def writeGAEObject(obj, encoder=None):
    """
    The GAE Datastore creates new instances of objects for each get request.
    This is a problem for PyAMF as it uses the id(obj) of the object to do
    reference checking.

    We could just ignore the problem, but the objects are conceptually the
    same so the effort should be made to attempt to resolve references for a
    given object graph.

    We create a new map on the encoder context object which contains a dict of
    C{object.__class__: {key1: object1, key2: object2, .., keyn: objectn}}. We
    use the datastore key to do the reference checking.

    @since: 0.4.1
    """
    if not obj.is_saved():
        encoder.writeObject(obj)

        return

    kls = obj.__class__
    s = obj.key()

    gae_objects = getGAEObjects(encoder.context.extra)

    try:
        referenced_object = gae_objects.getClassKey(kls, s)
    except KeyError:
        referenced_object = obj
        gae_objects.addClassKey(kls, s, obj)

    encoder.writeObject(referenced_object)


def writeGAEKey(key, encoder=None):
    gae_objects = getGAEObjects(encoder.context.extra)

    klass = db.class_for_kind(key.kind())

    try:
        referenced_object = gae_objects.getClassKey(klass, key)
    except KeyError:
        referenced_object = db.get(key)
        gae_objects.addClassKey(klass, key, referenced_object)

    encoder.writeObject(referenced_object)


def post_process(context):
    """
    """
    stubs = context.get('stubs', None)

    if not stubs:
        return

    stubs.transform()

# initialise the module here: hook into pyamf

pyamf.register_alias_type(DataStoreClassAlias, db.Model)
pyamf.add_type(db.Query, util.to_list)
pyamf.add_type(db.Model, writeGAEObject)
pyamf.add_post_processor(post_process)
pyamf.add_type(db.Key, writeGAEKey)
