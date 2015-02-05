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

import datetime
import logging

from google.appengine.ext import db
from google.appengine.ext.db import polymodel

import pyamf
from pyamf.adapters import util, models as adapter_models

__all__ = [
    'DataStoreClassAlias',
]


class ModelStub(object):
    """
    This class represents a C{db.Model} or C{db.Expando} class as the typed
    object is being read from the AMF stream. Once the attributes have been
    read from the stream and through the magic of Python, the instance of this
    class will be converted into the correct type.
    """


class GAEReferenceCollection(dict):
    """
    This helper class holds a dict of klass to key/objects loaded from the
    Datastore.

    @since: 0.4.1
    """

    def _getClass(self, klass):
        if not issubclass(klass, (db.Model, db.Expando)):
            raise TypeError('expected db.Model/db.Expando class, got %s' % (
                klass,
            ))

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
    Does the job of maintaining a list of stubs -> object and transforms them
    when appropriate.
    """

    def __init__(self):
        self.stubs = {}
        self.to_fetch = []
        self.fetched_entities = None

    def addStub(self, stub, alias, attrs, key):
        """
        """
        self.stubs[stub] = (alias.klass, attrs, key)

        if key:
            self.to_fetch.append(key)

    def transformStub(self, stub, klass, attrs, key):
        stub.__dict__.clear()
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

    @ivar properties: A mapping of attribute -> property instance.
    @ivar reference_properties: A mapping of attribute -> db.ReferenceProperty
        which hold special significance when en/decoding.
    """

    # The name of the attribute used to represent the key
    KEY_ATTR = '_key'

    def _compile_base_class(self, klass):
        if klass in (db.Model, polymodel.PolyModel):
            # can't compile these classes, so this is as far as we go
            return

        pyamf.ClassAlias._compile_base_class(self, klass)

    def getCustomProperties(self):
        self.reference_properties = {}
        self.properties = {}
        reverse_props = []

        for name, prop in self.klass.properties().iteritems():
            self.properties[name] = prop

            if isinstance(prop, db.ReferenceProperty):
                self.reference_properties[name] = prop

        if issubclass(self.klass, polymodel.PolyModel):
            del self.properties['_class']

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
        """
        Called when PyAMF needs an object to use as part of the decoding
        process. This is sort of a hack but an POPO is returned which can then
        be transformed in to the db.Model instance.
        """
        return ModelStub()

    def getAttribute(self, obj, attr, codec=None):
        def _():
            return super(DataStoreClassAlias, self).getAttribute(
                obj, attr, codec=codec,
            )

        if codec is None:
            return _()

        if not self.reference_properties:
            return _()

        try:
            prop = self.reference_properties[attr]
        except KeyError:
            return _()

        gae_objects = getGAEObjects(codec.context.extra)
        klass = prop.reference_class
        key = prop.get_value_for_datastore(obj)

        if key is None:
            return _()

        try:
            return gae_objects.getClassKey(klass, key)
        except KeyError:
            pass

        try:
            ref_obj = _()
        except db.ReferencePropertyResolveError:
            logging.warn(
                'Attempted to get %r on %r with key %r',
                attr,
                type(obj),
                key
            )

            return None

        gae_objects.addClassKey(klass, key, ref_obj)

        return ref_obj

    def getEncodableAttributes(self, obj, codec=None):
        attrs = pyamf.ClassAlias.getEncodableAttributes(self, obj, codec=codec)

        for k in attrs.keys()[:]:
            if k.startswith('_'):
                del attrs[k]

        for attr in obj.dynamic_properties():
            attrs[attr] = self.getAttribute(obj, attr, codec=codec)

        attrs[self.KEY_ATTR] = unicode(obj.key()) if obj.is_saved() else None

        return attrs

    def makeStubCollection(self):
        return StubCollection()

    def getStubCollection(self, codec):
        extra = codec.context.extra

        stubs = extra.get('gae_xdb_stubs', None)

        if not stubs:
            stubs = extra['gae_xdb_stubs'] = self.makeStubCollection()

        return stubs

    def getDecodableAttributes(self, obj, attrs, codec=None):
        key = attrs.pop(self.KEY_ATTR, None)

        attrs = pyamf.ClassAlias.getDecodableAttributes(
            self,
            obj,
            attrs,
            codec=codec
        )

        if self.properties:
            adapter_models.decode_model_properties(self.properties, attrs)

        if key:
            key = db.Key(key)

        stubs = self.getStubCollection(codec)

        stubs.addStub(obj, self, attrs, key)

        # don't return any decodable properties as they will be set when the
        # stubs are transformed.
        return attrs


def getGAEObjects(context):
    """
    Returns a reference to the C{gae_objects} on the context. If it doesn't
    exist then it is created.

    @param context: The context to load the C{gae_objects} index from.
    @return: The C{gae_objects} index reference.
    @rtype: Instance of L{GAEReferenceCollection}
    @since: 0.4.1
    """
    ref_collection = context.get('gae_xdb_context', None)

    if ref_collection:
        return ref_collection

    context['gae_xdb_context'] = GAEReferenceCollection()

    return context['gae_xdb_context']


def write_entity(obj, encoder=None):
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


def write_db_key(key, encoder=None):
    """
    Convert the `db.Key` to it's entity and endcode it.
    """
    return unicode(key)


@adapter_models.register_property_decoder(db.FloatProperty)
def handle_float_property(prop, value):
    if isinstance(value, (int, long)):
        return float(value)

    return value


@adapter_models.register_property_decoder(db.IntegerProperty)
def handle_integer_property(prop, value):
    if isinstance(value, float):
        x = int(value)

        # only convert the type if there is no mantissa - otherwise let the
        # chips fall where they may
        if x == value:
            return x

    return value


@adapter_models.register_property_decoder(db.ListProperty)
def handle_list_property(prop, value):
    if value is None:
        return []

    # there is an issue with large ints and ListProperty(int) AMF leaves
    # ints > amf3.MAX_29B_INT as floats db.ListProperty complains pretty
    # hard in this case so we try to work around the issue.
    if prop.item_type in (float, basestring):
        return value

    for i, x in enumerate(value):
        if isinstance(x, float):
            y = int(x)

            # only convert the type if there is no mantissa
            # otherwise let the chips fall where they may
            if x == y:
                value[i] = y

    return value


@adapter_models.register_property_decoder(db.DateProperty)
def handle_date_property(prop, value):
    if not isinstance(value, datetime.datetime):
        return value

    # DateProperty fields expect specific types of data
    # whereas PyAMF only decodes into datetime.datetime
    # objects.
    return value.date()


@adapter_models.register_property_decoder(db.TimeProperty)
def handle_time_property(prop, value):
    if not isinstance(value, datetime.datetime):
        return value

    # TimeProperty fields expect specific types of data
    # whereas PyAMF only decodes into datetime.datetime
    # objects.
    return value.time()


def transform_stubs(payload, context):
    """
    Called when a successful decode has been performed. Transform the stubs
    within the payload to proper db.Model instances.
    """
    stubs = context.get('gae_xdb_stubs', None)

    if not stubs:
        return payload

    stubs.transform()

    return payload


# initialise the module here: hook into pyamf
pyamf.register_alias_type(DataStoreClassAlias, db.Model)
pyamf.add_type(db.Query, util.to_list)
pyamf.add_type(db.Model, write_entity)
pyamf.add_post_decode_processor(transform_stubs)
pyamf.add_type(db.Key, write_db_key)
