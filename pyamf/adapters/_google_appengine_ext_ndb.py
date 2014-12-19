# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Google App Engine ndb adapter module.
"""

import datetime

from google.appengine.ext import db
from google.appengine.ext import ndb
from google.appengine.ext.ndb import polymodel
from google.appengine.ext.ndb import GeoPt

import pyamf
from pyamf.adapters import util


class NdbModelStub(object):
    """
    This class represents a C{ndb.Model} or C{ndb.Expando} class as the typed
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
        if not issubclass(klass, (ndb.Model, ndb.Expando)):
            raise TypeError('expected ndb.Model/ndb.Expando class, got %s' % (klass,))

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
        self.stubs = []
        self.to_fetch = []
        self.by_id = {}
        self.by_key = {}
        self.fetched_entities = None

    def addStub(self, stub, alias, attrs, key):
        """
        """
        if id(stub) not in self.by_id:
            to_add = (stub, alias.klass, attrs, key)
            self.by_id[id(stub)] = to_add
            self.stubs.append(to_add)

        if key:
            self.by_key[id(stub)] = key

            self.to_fetch.append(key)

    def transformStub(self, stub, klass, attrs, key):
        stub.__class__ = klass

        for k, v in attrs.items():
            if not isinstance(v, NdbModelStub):
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
        return dict(zip(self.to_fetch, ndb.get_multi(self.to_fetch)))

    def transform(self, stub=None):
        if self.fetched_entities is None:
            self.fetched_entities = self.fetchEntities()

        if stub is not None:
            stub, klass, attrs, key = self.stubs.pop(self.stubs.index(stub))

            self.transformStub(stub, klass, attrs, key)

            return

        for stub, klass, attrs, key in self.stubs:
            self.transformStub(stub, klass, attrs, key)


class NewDataStoreClassAlias(pyamf.ClassAlias):
    """
    This class contains all the business logic to interact with Google's
    Datastore API's. Any C{ndb.Model} or C{ndb.Expando} classes will use this
    class alias for encoding/decoding.

    We also add a number of indexes to the encoder context to aggressively
    decrease the number of Datastore API's that we need to complete.
    """

    # The name of the attribute used to represent the key
    KEY_ATTR = 'keyStr'

    def _compile_base_class(self, klass):
        if klass in (ndb.Model, polymodel.PolyModel):
            return

        pyamf.ClassAlias._compile_base_class(self, klass)

    def getCustomProperties(self):
        props = [self.KEY_ATTR]
        self.properties = {}
        reverse_props = []

        for name, prop in self.klass._properties.iteritems():
            self.properties[name] = prop

            props.append(name)

        if issubclass(self.klass, polymodel.PolyModel):
            del self.properties['class']
            props.remove('class')

        # check if the property is a defined as a computed property. These types
        # of properties are read-only and the datastore freaks out if you
        # attempt to meddle with it. We delete the attribute entirely ..
        for name, value in self.klass.__dict__.iteritems():
            if isinstance(value, ndb.ComputedProperty):
                reverse_props.append(name)

        self.encodable_properties.update(self.properties.keys())
        self.decodable_properties.update(self.properties.keys())
        self.readonly_attrs.update(reverse_props)

        if not self.properties:
            self.properties = None

    def _finalise_compile(self):
        pyamf.ClassAlias._finalise_compile(self)

        self.shortcut_decode = False

    def createInstance(self, codec=None):
        return NdbModelStub()

    def getEncodableValue(self, prop, value, single_of_repeated=False):
        """get value encodable from a python object for an amf stream"""
        if not isinstance(prop, ndb.Property):
            return value

        # repeat decoding for repeated values
        if prop._repeated and not single_of_repeated:
            encodable_value = []

            if value is None:
                return encodable_value

            for single_value in value:
                encodable_value.append(
                    self.getEncodableValue(
                        prop,
                        single_value,
                        single_of_repeated=True))

            return encodable_value

        if value is not None:
            if isinstance(prop, ndb.KeyProperty):
                return value.urlsafe()
            elif isinstance(prop, ndb.TimeProperty):
                if isinstance(value, datetime.time):
                    # The date will be removed when this is decoded
                    # but amf can only deal with datetime.datetime
                    return datetime.datetime.combine(
                        datetime.datetime(1970,1,1),value)
            elif isinstance(prop, ndb.DateProperty):
                return datetime.datetime.combine(value,datetime.time(0,0))

        return value



    def getEncodableAttributes(self, obj, codec=None):
        """encode a python object to an amf stream
        """

        attrs = pyamf.ClassAlias.getEncodableAttributes(self, obj,
                                                        codec=codec)

        for k in attrs.keys()[:]:
            if k.startswith('_'):
                del attrs[k]

        valid_properties = [prop for prop in obj._properties]

        if isinstance(obj, polymodel.PolyModel):
            valid_properties.remove('class')

        for attr in valid_properties:
            try:
                prop = getattr(obj.__class__,attr)
            except AttributeError:
                prop = ndb.GenericProperty()

            if attr in attrs and hasattr(obj, attr):
                attrs[attr] = self.getEncodableValue(prop, getattr(obj, attr))
            elif attr in attrs:
                del attrs[attr]

        attrs[self.KEY_ATTR] = obj.key.urlsafe() \
            if obj.key and obj.key.id() else None

        return attrs

    def getStubCollection(self):
        return StubCollection()

    def getDecodableValue(self, prop, value, single_of_repeated=False):
        """decode an amf stream to a python object
        """
        # repeat decoding for repeated values
        if prop._repeated and not single_of_repeated:
            decodable_value = []

            if value is None:
                return decodable_value

            for single_value in value:
                decodable_value.append(
                    self.getDecodableValue(
                        prop,
                        single_value,
                        single_of_repeated=True))

            return decodable_value

        if isinstance(prop, ndb.FloatProperty) \
                and isinstance(value, (int, long)):
            return float(value)
        elif isinstance(prop, ndb.IntegerProperty) \
                and isinstance(value, float) \
                and long(value) == value:
            # only convert the type if there is no mantissa - otherwise
            # let the chips fall where they may
            return long(value)
        elif isinstance(value, datetime.datetime):
            # Date/Time Property fields expect specific types of data
            # whereas PyAMF only decodes into datetime.datetime objects.
            if isinstance(prop, ndb.DateProperty):
                return value.date()
            elif isinstance(prop, ndb.TimeProperty):
                return value.time()
        elif value is not None and isinstance(prop, ndb.KeyProperty):
            return ndb.Key(urlsafe=value)
        elif value is not None and isinstance(prop, ndb.GeoPtProperty):
            return GeoPt(**value)

        return value

    def getDecodableAttributes(self, obj, attrs, codec=None):
        key = attrs.pop(self.KEY_ATTR, None)

        attrs = pyamf.ClassAlias.getDecodableAttributes(self, obj, attrs, codec=codec)

        if self.properties:
            for k in [k for k in attrs if k in self.properties]:
                prop = self.properties[k]
                value = attrs[k]
                attrs[k] = self.getDecodableValue(prop, value)

        e = pyamf.get_context(codec)

        try:
            stubs = e['ndb_stubs']
        except KeyError:
            stubs = e['ndb_stubs'] = self.getStubCollection()

        if key:
            key = ndb.Key(urlsafe=key)
        stubs.addStub(obj, self, attrs, key)

        return attrs


def getGAEObjects(context):
    """
    Returns a reference to the C{gae_ndb_objects} on the context. If it doesn't
    exist then it is created.

    @param context: The context to load the C{gae_ndb_objects} index from.
    @return: The C{gae_ndb_objects} index reference.
    @rtype: Instance of L{GAEReferenceCollection}
    @since: 0.4.1
    """
    try:
        return context['gae_ndb_objects']
    except KeyError:
        r = context['gae_ndb_objects'] = GAEReferenceCollection()

        return r


def writeGaeNdbObject(obj, encoder=None):
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
    if not obj.key or not obj.key.id():
        encoder.writeObject(obj)

        return

    kls = obj.__class__
    s = obj.key

    gae_objects = getGAEObjects(encoder.context.extra)

    try:
        referenced_object = gae_objects.getClassKey(kls, s)
    except KeyError:
        referenced_object = obj
        gae_objects.addClassKey(kls, s, obj)

    encoder.writeObject(referenced_object)


def writeGaeNdbKey(key, encoder=None):
    gae_objects = getGAEObjects(encoder.context.extra)

    klass = ndb.Model._kind_map.get(key.kind())

    try:
        referenced_object = gae_objects.getClassKey(klass, key)
    except KeyError:
        referenced_object = key.get()
        gae_objects.addClassKey(klass, key, referenced_object)

    encoder.writeObject(referenced_object)


def post_ndb_process(context):
    """
    """
    stubs = context.get('ndb_stubs', None)

    if not stubs:
        return

    stubs.transform()

# initialise the module here: hook into pyamf

pyamf.register_alias_type(NewDataStoreClassAlias, ndb.Model, ndb.Expando)
pyamf.add_type(ndb.Query, util.to_list)
pyamf.add_type(ndb.Model, writeGaeNdbObject)
pyamf.add_post_processor(post_ndb_process)
pyamf.add_type(ndb.Key, writeGaeNdbKey)
