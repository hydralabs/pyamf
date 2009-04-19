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
from pyamf.util import imports
from pyamf.adapters import util

class ModelStub(object):
    """
    This class represents a L{db.Model} or L{db.Expando} class as the typed
    object is being read from the AMF stream. Once the attributes have been
    read from the stream and through the magic of Python, the instance of this
    class will be converted into the correct type.

    @ivar klass: The referenced class either L{db.Model} or L{db.Expando}.
        This is used so we can proxy some of the method calls during decoding.
    @type klass: L{db.Model} or L{db.Expando}
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

        if klass not in self.keys():
            self[klass] = {}

        return self[klass]

    def getClassKey(self, klass, key):
        """
        Return an instance based on klass/key.

        If an instance cannot be found then L{KeyError} is raised.

        @param klass: The class of the instance.
        @param key: The key of the instance.
        @return: The instance linked to the C{klass}/C{key}.
        @rtype: Instance of L{klass}.
        """
        if not isinstance(key, basestring):
            raise TypeError('basestring type expected for test, got %s' % (repr(key),))

        d = self._getClass(klass)

        return d[key]

    def addClassKey(self, klass, key, obj):
        """
        Adds an object to the collection, based on klass and key.

        @param klass: The class of the object.
        @param key: The datastore key of the object.
        @param obj: The loaded instance from the datastore.
        """
        if not isinstance(key, basestring):
            raise TypeError('basestring type expected for test, got %s' % (repr(key),))

        d = self._getClass(klass)

        d[key] = obj

class DataStoreClassAlias(pyamf.ClassAlias):
    """
    This class contains all the business logic to interact with Google's
    Datastore API's. Any L{db.Model} or L{db.Expando} classes will use this
    class alias for encoding/decoding.

    We also add a number of indexes to the encoder context to aggressively
    decrease the number of Datastore API's that we need to complete.
    """

    # The name of the attribute used to represent the key
    KEY_ATTR = '_key'

    def getAttrs(self, obj, codec=None):
        """
        @since: 0.4
        """
        if not hasattr(self, 'static_attrs'):
            self.static_attrs = obj.properties().keys()
            self.static_attrs.insert(0, DataStoreClassAlias.KEY_ATTR)

            for k, v in self.klass.__dict__.iteritems():
                if isinstance(v, property):
                    self.static_attrs.append(k)

        dynamic_attrs = obj.dynamic_properties()

        for k, v in obj.__dict__.iteritems():
            if k.startswith('_'):
                continue

            if k not in self.static_attrs:
                dynamic_attrs.append(k)

        return self.static_attrs, dynamic_attrs

    def getAttributes(self, obj, codec=None):
        static_attrs = {}
        dynamic_attrs = {}
        static_attrs_names, dynamic_attrs_names = self.getAttrs(obj, codec=codec)
        gae_objects = None

        if codec is not None:
            gae_objects = getGAEObjects(codec.context)

        key = str(obj.key()) if obj.is_saved() else None

        static_attrs[DataStoreClassAlias.KEY_ATTR] = key
        kd = self.klass.__dict__

        for a in static_attrs_names:
            if a == DataStoreClassAlias.KEY_ATTR:
                continue

            try:
                prop = kd[a]
            except KeyError:
                prop = None

            if isinstance(prop, db.ReferenceProperty):
                if gae_objects is not None:
                    klass = prop.reference_class
                    key = prop.get_value_for_datastore(obj)

                    if key is not None:
                        key = str(key)

                        try:
                            static_attrs[a] = gae_objects.getClassKey(klass, key)
                        except KeyError:
                            ref_obj = getattr(obj, a)
                            gae_objects.addClassKey(klass, key, ref_obj)
                            static_attrs[a] = ref_obj

                        continue

            static_attrs[a] = getattr(obj, a)

        for a in dynamic_attrs_names:
            dynamic_attrs[a] = getattr(obj, a)

        return static_attrs, dynamic_attrs

    def createInstance(self, codec=None):
        return ModelStub(self.klass)

    def applyAttributes(self, obj, attrs, codec=None):
        new_obj = None

        # attempt to load the object from the datastore if KEY_ATTR exists.
        if DataStoreClassAlias.KEY_ATTR in attrs.keys():
            if attrs[DataStoreClassAlias.KEY_ATTR] is not None:
                key = attrs[DataStoreClassAlias.KEY_ATTR]
                new_obj = loadInstanceFromDatastore(self.klass, key, codec)

            del attrs[DataStoreClassAlias.KEY_ATTR]

        properties = self.klass.properties()
        p_keys = properties.keys()
        apply_init = True
        sa, da = self.getAttrs(obj)

        # clean up the stub
        if isinstance(obj, ModelStub) and hasattr(obj, 'klass'):
            del obj.klass

        if new_obj is not None:
            obj.__dict__ = new_obj.__dict__.copy()

        obj.__class__ = self.klass
        kd = self.klass.__dict__

        for k, v in attrs.copy().iteritems():
            if k in p_keys:
                prop = properties[k]

                if k not in sa:
                    del attrs[k]
                    continue

                if isinstance(prop, db.ListProperty) and v is None:
                    attrs[k] = []
                elif isinstance(v, datetime.datetime):
                    # Date/Time Property fields expect specific types of data
                    # whereas PyAMF only decodes into datetime.datetime objects.
                    if isinstance(prop, db.DateProperty):
                        attrs[k] = v.date()
                    elif isinstance(prop, db.TimeProperty):
                        attrs[k] = v.time()

                if new_obj is None and isinstance(v, ModelStub) and (k in kd and isinstance(kd[k], db.ReferenceProperty) and kd[k].required is True):
                    apply_init = False
                    del attrs[k]
                    continue
            elif k in kd:
                kp = kd[k]

                # check if the property is a defined as a collection_name.
                # These types of properties are read-only and the datastore
                # freaks out if you attempt to meddle with it. We delete the
                # attribute entirely ..
                if isinstance(kp, db._ReverseReferenceProperty):
                    del attrs[k]
                elif isinstance(kp, property):
                    if kp.fset is None:
                        del attrs[k]

        # If the object does not exist in the datastore, we must fire the
        # class constructor. This sets internal attributes that pyamf has
        # no business messing with ..
        if new_obj is None and apply_init is True:
            obj.__init__(**attrs)

        for k, v in attrs.iteritems():
            setattr(obj, k, v)

def getGAEObjects(context):
    """
    Returns a reference to the C{gae_objects} on the context. If it doesn't
    exist then it is created.

    @param context: The context to load the C{gae_objects} index from.
    @type context: Instance of L{pyamf.BaseContext}
    @return: The C{gae_objects} index reference.
    @rtype: Instance of L{GAEReferenceCollection}
    @since: 0.4.1
    """
    if not hasattr(context, 'gae_objects'):
        context.gae_objects = GAEReferenceCollection()

    return context.gae_objects

def loadInstanceFromDatastore(klass, key, codec=None):
    """
    Attempt to load an instance from the datastore, based on C{klass}
    and C{key}. We create an index on the codec's context (if it exists)
    so we can check that first before accessing the datastore.

    @param klass: The class that will be loaded from the datastore.
    @type klass: Sub-class of L{db.Model} or L{db.Expando}
    @param key: The key which is used to uniquely identify the instance in the
        datastore.
    @type key: C{str}
    @param codec: The codec to reference the C{gae_objects} index. If
        supplied,The codec must have have a context attribute.
    @type codec: Instance of L{pyamf.BaseEncoder} or L{pyamf.BaseDecoder}
    @return: The loaded instance from the datastore.
    @rtype: Instance of C{klass}.
    @since: 0.4.1
    """
    if not issubclass(klass, (db.Model, db.Expando)):
        raise TypeError('expected db.Model/db.Expando class, got %s' % (klass,))

    if not isinstance(key, basestring):
        raise TypeError('string expected for key, got %s', (repr(key),))

    key = str(key)

    if codec is None:
        return klass.get(key)

    gae_objects = getGAEObjects(codec.context)

    try:
        return gae_objects.getClassKey(klass, key)
    except KeyError:
        pass

    obj = klass.get(key)
    gae_objects.addClassKey(klass, key, obj)

    return obj

def writeGAEObject(self, object, *args, **kwargs):
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
    if not (isinstance(object, db.Model) and object.is_saved()):
        self.writeNonGAEObject(object, *args, **kwargs)

        return

    context = self.context
    kls = object.__class__
    s = str(object.key())

    gae_objects = getGAEObjects(context)
    referenced_object = None

    try:
        referenced_object = gae_objects.getClassKey(kls, s)
    except KeyError:
        gae_objects.addClassKey(kls, s, object)
        self.writeNonGAEObject(object, *args, **kwargs)

        return

    self.writeNonGAEObject(referenced_object, *args, **kwargs)

def install_gae_reference_model_hook(mod):
    """
    Called when L{pyamf.amf0} or L{pyamf.amf3} are imported. Attaches the
    L{writeGAEObject} method to the C{Encoder} class in that module.

    @param mod: The module imported.
    @since: 0.4.1
    """
    if not hasattr(mod.Encoder, 'writeNonGAEObject'):
        mod.Encoder.writeNonGAEObject = mod.Encoder.writeObject
        mod.Encoder.writeObject = writeGAEObject

# initialise the module here: hook into pyamf

pyamf.add_type(db.Query, util.to_list)
pyamf.register_alias_type(DataStoreClassAlias, db.Model, db.Expando)

# hook the L{writeGAEObject} method to the Encoder class on import
imports.whenImported('pyamf.amf0', install_gae_reference_model_hook)
imports.whenImported('pyamf.amf3', install_gae_reference_model_hook)
