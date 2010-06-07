# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
**PyAMF** provides Action Message Format (AMF_) support for Python that is
compatible with the Adobe `Flash Player`_.

.. _AMF:          http://en.wikipedia.org/wiki/Action_Message_Format
.. _Flash Player: http://en.wikipedia.org/wiki/Flash_Player

:Copyright: Copyright (c) 2007-2010 The PyAMF Project. All Rights Reserved.
:Contact: users@pyamf.org
:See: http://pyamf.org
:Since: October 2007
:Status: Production/Stable
"""

import types
import inspect
import datetime

from pyamf import util, versions as v
from pyamf.adapters import register_adapters

try:
    set
except NameError:
    from sets import Set as set


__all__ = [
    'register_class',
    'register_class_loader',
    'encode',
    'decode',
    '__version__',
    'version'
]

#: PyAMF version number.
__version__ = version = v.Version(0, 6, 'b1')

#: Class mapping support.
CLASS_CACHE = {}
#: Class loaders.
CLASS_LOADERS = []
#: Custom type map.
TYPE_MAP = {}
#: Maps error classes to string codes.
ERROR_CLASS_MAP = {
    TypeError.__name__: TypeError,
    KeyError.__name__: KeyError,
    LookupError.__name__: LookupError,
    IndexError.__name__: IndexError,
    NameError.__name__: NameError,
    ValueError.__name__: ValueError
}
#: Alias mapping support
ALIAS_TYPES = {}

#: Specifies that objects are serialized using AMF for ActionScript 1.0
#: and 2.0 that were introduced in the Adobe Flash Player 6.
AMF0 = 0
#: Specifies that objects are serialized using AMF for ActionScript 3.0
#: that was introduced in the Adobe Flash Player 9.
AMF3 = 3
#: Supported AMF encoding types.
ENCODING_TYPES = (AMF0, AMF3)

#: Default encoding
DEFAULT_ENCODING = AMF3


class UndefinedType(object):

    def __repr__(self):
        return 'pyamf.Undefined'

#: Represents the `undefined` value in the Adobe Flash Player client.
Undefined = UndefinedType()


class BaseError(Exception):
    """
    Base AMF Error.

    All AMF related errors should be subclassed from this class.
    """


class DecodeError(BaseError):
    """
    Raised if there is an error in decoding an AMF data stream.
    """


class EOStream(BaseError):
    """
    Raised if the data stream has come to a natural end.
    """


class ReferenceError(BaseError):
    """
    Raised if an AMF data stream refers to a non-existent object
    or string reference.
    """


class EncodeError(BaseError):
    """
    Raised if the element could not be encoded to the stream.

    :Bug: See `Docuverse blog (external)`_ for more info about the empty key
          string array bug.

    .. _Docuverse blog (external): http://www.docuverse.com/blog/donpark/2007/05/14/flash-9-amf3-bug
    """


class ClassAliasError(BaseError):
    """
    Generic error for anything class alias related.
    """


class UnknownClassAlias(ClassAliasError):
    """
    Raised if the AMF stream specifies an Actionscript class that does not
    have a Python class alias.

    :See: :func:`register_class`
    """


class BaseContext(object):
    """
    I hold the AMF context for en/decoding streams.

    :ivar objects: An indexed collection of referencable objects encountered
        during en/decoding.
    :type objects: :class:`pyamf.util.IndexedCollection`
    :ivar class_aliases: A `dict` of `class` to :class:`ClassAlias`
    """

    def __init__(self):
        self.objects = util.IndexedCollection()

        self.clear()

    def clear(self):
        """
        Completely clears the context.
        """
        self.objects.clear()
        self.class_aliases = {}
        self.proxied_objects = {}
        self.unicodes = {}
        self.extra_context = {}

    def getObject(self, ref):
        """
        Gets an object based on a reference.

        :param ref: The reference for the object.
        :type ref: `int`
        :return: The referenced object or `None` if not found.
        """
        return self.objects.getByReference(ref)

    def getObjectReference(self, obj):
        """
        Gets a reference for an object.

        :param obj: The referenced object.
        :return: The reference to the object or `None` if the object is not
                 in the context.
        """
        return self.objects.getReferenceTo(obj)

    def addObject(self, obj):
        """
        Adds a reference to `obj`.

        :type obj: `mixed`
        :param obj: The object to add to the context.
        :rtype: `int`
        :return: Reference to `obj`.
        """
        return self.objects.append(obj)

    def getClassAlias(self, klass):
        """
        Gets a class alias based on the supplied `klass`.

        :param klass: The class object.
        :return: The :class:`ClassAlias` that is linked to `klass`
        """
        alias = self.class_aliases.get(klass)

        if alias is not None:
            return alias

        try:
            self.class_aliases[klass] = get_class_alias(klass)
        except UnknownClassAlias:
            # no alias has been found yet .. check subclasses
            alias = util.get_class_alias(klass)

            self.class_aliases[klass] = alias(klass)

        return self.class_aliases[klass]

    def getProxyForObject(self, obj):
        """
        Returns the proxied version of `obj` as stored in the context, or
        creates a new proxied object and returns that.

        :see: func:`pyamf.flex.proxy_object`
        :since: 0.6
        """
        proxied = self.proxied_objects.get(id(obj))

        if proxied is None:
            from pyamf import flex

            proxied = flex.proxy_object(obj)

            self.addProxyObject(obj, proxied)

        return proxied

    def getObjectForProxy(self, proxy):
        """
        Returns the unproxied version of `proxy` as stored in the context, or
        unproxies the proxy and returns that 'raw' object.

        :see: :func:`pyamf.flex.unproxy_object`
        :since: 0.6
        """
        obj = self.proxied_objects.get(id(proxy))

        if obj is None:
            from pyamf import flex

            obj = flex.unproxy_object(proxy)

            self.addProxyObject(obj, proxy)

        return obj

    def addProxyObject(self, obj, proxied):
        """
        Stores a reference to the unproxied and proxied versions of `obj` for
        later retrieval.

        :since: 0.6
        """
        self.proxied_objects[id(obj)] = proxied
        self.proxied_objects[id(proxied)] = obj

    def getUnicodeForString(self, s):
        """
        Returns the corresponding unicode object for a given string. If there
        is no unicode object, one is created.

        :since: 0.6
        """
        h = hash(s)
        u = self.unicodes.get(h, None)

        if u is not None:
            return u

        u = self.unicodes[h] = unicode(s, 'utf-8')

        return u

    def getStringForUnicode(self, u):
        """
        Returns the corresponding utf-8 encoded string for a given unicode
        object. If there is no string, one is encoded.

        :since: 0.6
        """
        h = hash(u)
        s = self.unicodes.get(h, None)

        if s is not None:
            return s

        s = self.unicodes[h] = u.encode('utf-8')

        return s


class ASObject(dict):
    """
    This class represents a Flash Actionscript Object (typed or untyped).

    I supply a `__builtin__.dict` interface to support `get`/`setattr`
    calls.

    :raise AttributeError: Unknown attribute.
    """

    class __amf__:
        dynamic = True

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)

    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError:
            raise AttributeError('Unknown attribute \'%s\'' % (k,))

    def __setattr__(self, k, v):
        self[k] = v

    def __repr__(self):
        return dict.__repr__(self)

    def __hash__(self):
        return id(self)


class MixedArray(dict):
    """
    Used to be able to specify the `mixedarray` type.
    """


class ClassAlias(object):
    """
    Class alias. Provides class/instance meta data to the En/Decoder to allow
    fine grain control and some performance increases.

    :ivar bases: A list of `(class, alias)` for all bases of this alias.
    """

    def __init__(self, klass, alias=None, **kwargs):
        if not isinstance(klass, (type, types.ClassType)):
            raise TypeError('klass must be a class type, got %r' % type(klass))

        self.checkClass(klass)

        self.klass = klass
        self.alias = alias

        self.static_attrs = kwargs.pop('static_attrs', None)
        self.exclude_attrs = kwargs.pop('exclude_attrs', None)
        self.readonly_attrs = kwargs.pop('readonly_attrs', None)
        self.proxy_attrs = kwargs.pop('proxy_attrs', None)
        self.amf3 = kwargs.pop('amf3', None)
        self.external = kwargs.pop('external', None)
        self.dynamic = kwargs.pop('dynamic', None)
        self.synonym = kwargs.pop('synonym', {})

        self._compiled = False
        self.anonymous = False
        self.sealed = None
        self.bases = None

        if self.alias is None:
            self.anonymous = True
            # we don't set this to None because AMF3 untyped objects have a
            # class name of ''
            self.alias = ''
        else:
            if self.alias == '':
                raise ValueError('Cannot set class alias as \'\'')

        if not kwargs.pop('defer', False):
            self.compile()

        if kwargs:
            raise TypeError('Unexpected keyword arguments %r' % (kwargs,))

    def _checkExternal(self):
        if not hasattr(self.klass, '__readamf__'):
            raise AttributeError("An externalised class was specified, but"
                " no __readamf__ attribute was found for %r" % (self.klass,))

        if not hasattr(self.klass, '__writeamf__'):
            raise AttributeError("An externalised class was specified, but"
                " no __writeamf__ attribute was found for %r" % (self.klass,))

        if not isinstance(self.klass.__readamf__, types.UnboundMethodType):
            raise TypeError("%s.__readamf__ must be callable" % (
                self.klass.__name__,))

        if not isinstance(self.klass.__writeamf__, types.UnboundMethodType):
            raise TypeError("%s.__writeamf__ must be callable" % (
                self.klass.__name__,))

    def compile(self):
        """
        This compiles the alias into a form that can be of most benefit to the
        en/decoder.
        """
        if self._compiled:
            return

        self.decodable_properties = set()
        self.encodable_properties = set()
        self.inherited_dynamic = None
        self.inherited_sealed = None
        self.bases = []

        self.exclude_attrs = set(self.exclude_attrs or [])
        self.readonly_attrs = set(self.readonly_attrs or [])
        self.static_attrs = set(self.static_attrs or [])
        self.proxy_attrs = set(self.proxy_attrs or [])

        self.sealed = util.is_class_sealed(self.klass)

        if self.external:
            self._checkExternal()
            self._finalise_compile()

            # this class is external so no more compiling is necessary
            return

        if hasattr(self.klass, '__slots__'):
            self.decodable_properties.update(self.klass.__slots__)
            self.encodable_properties.update(self.klass.__slots__)

        for k, v in self.klass.__dict__.iteritems():
            if not isinstance(v, property):
                continue

            if v.fget:
                self.encodable_properties.update([k])

            if v.fset:
                self.decodable_properties.update([k])
            else:
                self.readonly_attrs.update([k])

        mro = inspect.getmro(self.klass)[1:]

        for c in mro:
            self._compile_base_class(c)

        self.getCustomProperties()

        self._finalise_compile()

    def _compile_base_class(self, klass):
        if klass is object:
            return

        try:
            alias = get_class_alias(klass)
        except UnknownClassAlias:
            alias = register_class(klass)

        alias.compile()

        self.bases.append((klass, alias))

        if alias.exclude_attrs:
            self.exclude_attrs.update(alias.exclude_attrs)

        if alias.readonly_attrs:
            self.readonly_attrs.update(alias.readonly_attrs)

        if alias.static_attrs:
            self.static_attrs.update(alias.static_attrs)

        if alias.proxy_attrs:
            self.proxy_attrs.update(alias.proxy_attrs)

        if alias.encodable_properties:
            self.encodable_properties.update(alias.encodable_properties)

        if alias.decodable_properties:
            self.decodable_properties.update(alias.decodable_properties)

        if self.amf3 is None and alias.amf3:
            self.amf3 = alias.amf3

        if self.dynamic is None and alias.dynamic is not None:
            self.inherited_dynamic = alias.dynamic

        if alias.sealed is not None:
            self.inherited_sealed = alias.sealed

        if alias.synonym:
            self.synonym, x = alias.synonym.copy(), self.synonym
            self.synonym.update(x)

    def _finalise_compile(self):
        if self.dynamic is None:
            self.dynamic = True

            if self.inherited_dynamic is not None:
                if self.inherited_dynamic is False and not self.sealed and self.inherited_sealed:
                    self.dynamic = True
                else:
                    self.dynamic = self.inherited_dynamic

        if self.sealed:
            self.dynamic = False

        if self.amf3 is None:
            self.amf3 = False

        if self.external is None:
            self.external = False

        if not self.static_attrs:
            self.static_attrs = None
        else:
            self.encodable_properties.update(self.static_attrs)
            self.decodable_properties.update(self.static_attrs)

        if self.static_attrs is not None:
            if self.exclude_attrs:
                self.static_attrs.difference_update(self.exclude_attrs)

            self.static_attrs = list(self.static_attrs)
            self.static_attrs.sort()

        self.static_attrs_set = set(self.static_attrs or [])

        if not self.exclude_attrs:
            self.exclude_attrs = None
        else:
            self.encodable_properties.difference_update(self.exclude_attrs)
            self.decodable_properties.difference_update(self.exclude_attrs)

        if self.exclude_attrs is not None:
            self.exclude_attrs = list(self.exclude_attrs)
            self.exclude_attrs.sort()

        if not self.readonly_attrs:
            self.readonly_attrs = None
        else:
            self.decodable_properties.difference_update(self.readonly_attrs)

        if self.readonly_attrs is not None:
            self.readonly_attrs = list(self.readonly_attrs)
            self.readonly_attrs.sort()

        if not self.proxy_attrs:
            self.proxy_attrs = None
        else:
            self.proxy_attrs = list(self.proxy_attrs)
            self.proxy_attrs.sort()

        if len(self.decodable_properties) == 0:
            self.decodable_properties = None
        else:
            self.decodable_properties = list(self.decodable_properties)
            self.decodable_properties.sort()

        if len(self.encodable_properties) == 0:
            self.encodable_properties = None
        else:
            self.encodable_properties = list(self.encodable_properties)
            self.encodable_properties.sort()

        self.non_static_encodable_properties = None

        if self.encodable_properties:
            self.non_static_encodable_properties = set(self.encodable_properties)

            if self.static_attrs:
                self.non_static_encodable_properties.difference_update(self.static_attrs)

        self.shortcut_encode = True
        self.shortcut_decode = True

        if self.encodable_properties or self.static_attrs or self.exclude_attrs or self.proxy_attrs or self.external:
            self.shortcut_encode = False

        if self.decodable_properties or self.static_attrs or self.exclude_attrs or self.readonly_attrs or not self.dynamic or self.external:
            self.shortcut_decode = False

        self.is_dict = False

        if issubclass(self.klass, dict) or self.klass is dict:
            self.is_dict = True

        self._compiled = True

    def is_compiled(self):
        return self._compiled

    def __str__(self):
        return self.alias

    def __repr__(self):
        return '<ClassAlias alias=%s class=%s @ 0x%x>' % (
            self.alias, self.klass, id(self))

    def __eq__(self, other):
        if isinstance(other, basestring):
            return self.alias == other
        elif isinstance(other, self.__class__):
            return self.klass == other.klass
        elif isinstance(other, (type, types.ClassType)):
            return self.klass == other
        else:
            return False

    def __hash__(self):
        return id(self)

    def checkClass(self, klass):
        """
        This function is used to check if the class being aliased fits certain
        criteria. The default is to check that `__new__` is available or the
        `__init__` constructor does not need additional arguments.

        :since: 0.4
        :raise TypeError: `__new__` not available and `__init__` requires
                          additional arguments
        """
        # Check for __new__ support.
        if hasattr(klass, '__new__') and callable(klass.__new__):
            # Should be good to go.
            return

        # Check that the constructor of the class doesn't require any additonal
        # arguments.
        if not (hasattr(klass, '__init__') and callable(klass.__init__)):
            return

        klass_func = klass.__init__.im_func

        if not hasattr(klass_func, 'func_code'):
            # Can't examine it, assume it's OK.
            return

        if klass_func.func_defaults:
            available_arguments = len(klass_func.func_defaults) + 1
        else:
            available_arguments = 1

        needed_arguments = klass_func.func_code.co_argcount

        if available_arguments >= needed_arguments:
            # Looks good to me.
            return

        spec = inspect.getargspec(klass_func)

        raise TypeError("__init__ doesn't support additional arguments: %s"
            % inspect.formatargspec(*spec))

    def getEncodableAttributes(self, obj, codec=None):
        """
        Returns a dict of attributes to be encoded or `None`.

        :param codec: An optional argument that will contain the en/decoder
                      instance calling this function.
        :since: 0.5
        """
        if not self._compiled:
            self.compile()

        if self.is_dict:
            return dict(obj)

        if self.shortcut_encode and self.dynamic:
            return obj.__dict__

        attrs = {}

        if self.static_attrs:
            for attr in self.static_attrs:
                attrs[attr] = getattr(obj, attr, Undefined)

        if not self.dynamic:
            if self.non_static_encodable_properties:
                for attr in self.non_static_encodable_properties:
                    attrs[attr] = getattr(obj, attr)

            return attrs

        dynamic_props = util.get_properties(obj)

        if not self.shortcut_encode:
            dynamic_props = set(dynamic_props)

            if self.encodable_properties:
                dynamic_props.update(self.encodable_properties)

            if self.static_attrs:
                dynamic_props.difference_update(self.static_attrs)

            if self.exclude_attrs:
                dynamic_props.difference_update(self.exclude_attrs)

        if self.is_dict:
            for attr in dynamic_props:
                attrs[attr] = obj[attr]
        else:
            for attr in dynamic_props:
                attrs[attr] = getattr(obj, attr)

        if self.proxy_attrs is not None and attrs and codec:
            context = codec.context

            for k, v in attrs.copy().iteritems():
                if k in self.proxy_attrs:
                    attrs[k] = context.getProxyForObject(v)

        return attrs

    def getDecodableAttributes(self, obj, attrs, codec=None):
        """
        Returns a dictionary of attributes for `obj` that has been filtered,
        based on the supplied `attrs`. This allows for fine grain control
        over what will finally end up on the object or not.

        :param obj: The reference object.
        :param attrs: The `attrs` dictionary that has been decoded.
        :param codec: An optional argument that will contain the codec
                      instance calling this function.
        :return: A dictionary of attributes that can be applied to `obj`
        :since: 0.5
        """
        if not self._compiled:
            self.compile()

        changed = False

        props = set(attrs.keys())

        if self.static_attrs:
            missing_attrs = self.static_attrs_set.difference(props)

            if missing_attrs:
                raise AttributeError('Static attributes %r expected '
                    'when decoding %r' % (missing_attrs, self.klass))

            props.difference_update(self.static_attrs)

        if not props:
            return attrs

        if not self.dynamic:
            if not self.decodable_properties:
                props = set()
            else:
                props.intersection_update(self.decodable_properties)

            changed = True

        if self.readonly_attrs:
            props.difference_update(self.readonly_attrs)
            changed = True

        if self.exclude_attrs:
            props.difference_update(self.exclude_attrs)
            changed = True

        if self.proxy_attrs is not None and codec:
            context = codec.context

            for k in self.proxy_attrs:
                try:
                    v = attrs[k]
                except KeyError:
                    continue

                attrs[k] = context.getObjectForProxy(v)

        if not changed:
            return attrs

        a = {}

        [a.__setitem__(p, attrs[p]) for p in props]

        return a

    def applyAttributes(self, obj, attrs, codec=None):
        """
        Applies the collection of attributes `attrs` to aliased object `obj`.
        Called when decoding reading aliased objects from an AMF byte stream.

        Override this to provide fine grain control of application of
        attributes to `obj`.

        :param codec: An optional argument that will contain the en/decoder
                      instance calling this function.
        """
        if not self._compiled:
            self.compile()

        if self.shortcut_decode:
            if self.is_dict:
                obj.update(attrs)

                return

            if not self.sealed:
                obj.__dict__.update(attrs)

                return

        else:
            attrs = self.getDecodableAttributes(obj, attrs, codec=codec)

        util.set_attrs(obj, attrs)

    def getCustomProperties(self):
        """
        Overrride this to provide known static properties based on the aliased
        class.

        :since: 0.5
        """

    def createInstance(self, codec=None, *args, **kwargs):
        """
        Creates an instance of the klass.

        :return: Instance of `self.klass`.
        """
        if type(self.klass) is type:
            return self.klass.__new__(self.klass)

        return self.klass()


class TypedObject(dict):
    """
    This class is used when a strongly typed object is decoded but there is no
    registered class to apply it to.

    This object can only be used for 'simple' streams - i.e. not externalized
    data. If encountered, a :class:`DecodeError` will be raised.

    :ivar alias: The alias of the typed object.
    :type alias: `unicode`
    :since: 0.4
    """

    def __init__(self, alias):
        dict.__init__(self)

        self.alias = alias

    def __readamf__(self, o):
        raise DecodeError('Unable to decode an externalised stream with '
            'class alias \'%s\'.\n\nA class alias was found and because '
            'strict mode is False an attempt was made to decode the object '
            'automatically. To decode this stream, a registered class with '
            'the alias and a corresponding __readamf__ method will be '
            'required.' % (self.alias,))

    def __writeamf__(self, o):
        raise EncodeError('Unable to encode an externalised stream with '
            'class alias \'%s\'.\n\nA class alias was found and because '
            'strict mode is False an attempt was made to encode the object '
            'automatically. To encode this stream, a registered class with '
            'the alias and a corresponding __readamf__ method will be '
            'required.' % (self.alias,))


class TypedObjectClassAlias(ClassAlias):
    """
    :since: 0.4
    """

    klass = TypedObject

    def __init__(self, klass, alias, *args, **kwargs):
        # klass attr is ignored

        ClassAlias.__init__(self, self.klass, alias)

    def createInstance(self, codec=None):
        return self.klass(self.alias)

    def checkClass(kls, klass):
        pass


class ErrorAlias(ClassAlias):
    """
    Adapts Python exception objects to Adobe Flash Player error objects.

    :since: 0.5
    """

    def getCustomProperties(self):
        self.exclude_attrs.update(['args'])

    def getEncodableAttributes(self, obj, **kwargs):
        attrs = ClassAlias.getEncodableAttributes(self, obj, **kwargs)

        if not attrs:
            attrs = {}

        attrs['message'] = str(obj)
        attrs['name'] = obj.__class__.__name__

        return attrs


class BaseDecoder(object):
    """
    Base AMF decoder.

    :ivar context_class: The context for the decoding.
    :type context_class: An instance of :func:`BaseDecoder.context_class`
    :ivar type_map:
    :type type_map: `list`
    :ivar stream: The underlying data stream.
    :type stream: :class:`BufferedByteStream<pyamf.util.BufferedByteStream>`
    :ivar strict: Defines how strict the decoding should be. For the time
                  being this relates to typed objects in the stream that do not
                  have a registered alias. Introduced in 0.4.
    :type strict: `bool`
    :ivar timezone_offset: The offset from UTC for any datetime objects being
        decoded. Default to `None` means no offset.
    :type timezone_offset: `datetime.timedelta`
    """

    context_class = BaseContext
    type_map = {}

    def __init__(self, stream=None, context=None, strict=False, timezone_offset=None):
        if isinstance(stream, util.BufferedByteStream):
            self.stream = stream
        else:
            self.stream = util.BufferedByteStream(stream)

        if context is None:
            self.context = self.context_class()
        else:
            self.context = context

        self.strict = strict
        self.timezone_offset = timezone_offset

        self._func_cache = {}

    def readProxy(self, obj, **kwargs):
        """
        Decodes a proxied object from the stream.

        :since: 0.6
        """
        return self.context.getObjectForProxy(obj)

    def readElement(self):
        """
        Reads an AMF3 element from the data stream.

        :raise DecodeError: The ActionScript type is unsupported.
        :raise EOStream: No more data left to decode.
        """
        pos = self.stream.tell()

        try:
            t = self.stream.read(1)
        except IOError:
            raise EOStream

        try:
            func = self._func_cache[t]
        except KeyError:
            func = getattr(self, self.type_map[t])

            if not func:
                raise DecodeError("Unsupported ActionScript type %r" % (t,))

            self._func_cache[t] = func

        try:
            return func()
        except IOError:
            self.stream.seek(pos)

            raise

    def __iter__(self):
        try:
            while 1:
                yield self.readElement()
        except EOStream:
            raise StopIteration


class CustomTypeFunc(object):
    """
    Support for custom type mappings when encoding.
    """

    def __init__(self, encoder, func):
        self.encoder = encoder
        self.func = func

    def __call__(self, data, **kwargs):
        self.encoder.writeElement(self.func(data, encoder=self.encoder), **kwargs)


class BaseEncoder(object):
    """
    Base AMF encoder.

    :ivar type_map: A list of types -> functions. The types is a list of
                    possible instances or functions to call (that return a
                    `bool`) to determine the correct function to call to
                    encode the data.
    :type type_map: `list`
    :ivar context_class: Holds the class that will create context objects for
                         the implementing `Encoder`.
    :type context_class: `type` or `types.ClassType`
    :ivar stream: The underlying data stream.
    :type stream: :class:`BufferedByteStream<pyamf.util.BufferedByteStream>`
    :ivar context: The context for the encoding.
    :type context: An instance of `BaseEncoder.context_class`
    :ivar strict: Whether the encoder should operate in 'strict' mode. Nothing
                  is really affected by this for the time being - its just here for
                  flexibility.
    :type strict: `bool`, default is `False`.
    :ivar timezone_offset: The offset from UTC for any `datetime` objects being
                           encoded. Default to `None` means no offset.
    :type timezone_offset: `datetime.timedelta`
    """

    context_class = BaseContext

    type_map = {
        util.xml_types: 'writeXML'
    }

    def __init__(self, stream=None, context=None, strict=False, timezone_offset=None):
        if isinstance(stream, util.BufferedByteStream):
            self.stream = stream
        else:
            self.stream = util.BufferedByteStream(stream)

        if context is None:
            self.context = self.context_class()
        else:
            self.context = context

        self._func_cache = {}
        self.strict = strict
        self.timezone_offset = timezone_offset

    def writeProxy(self, obj, **kwargs):
        """
        Encodes a proxied object to the stream.

        :since: 0.6
        """
        proxy = self.context.getProxyForObject(obj)

        self.writeElement(proxy, use_proxies=False)

    def writeNull(self, obj, **kwargs):
        """
        Subclasses should override this and all write[type] functions
        """
        raise NotImplementedError

    writeString = writeNull
    writeBoolean = writeNull
    writeNumber = writeNull
    writeList = writeNull
    writeUndefined = writeNull
    writeDate = writeNull
    writeXML = writeNull
    writeObject = writeNull

    def getCustomTypeFunc(self, data):
        for type_, func in TYPE_MAP.iteritems():
            try:
                if isinstance(data, type_):
                    return CustomTypeFunc(self, func)
            except TypeError:
                if callable(type_) and type_(data):
                    return CustomTypeFunc(self, func)

    def getTypeFunc(self, data):
        """
        Gets a function used to encode the data.

        :type   data: `mixed`
        :param  data: Python data.
        :rtype: callable or `None`.
        :return: The function used to encode data to the stream.
        :raise EncodeError: Unable to find a corresponding function that will
            encode `data`.
        """
        t = type(data)

        if data is None:
            return self.writeNull
        elif t is str:
            return self.writeString
        elif t is unicode:
            return self.writeUnicode
        elif t is bool:
            return self.writeBoolean
        elif t in (int, long, float):
            return self.writeNumber
        elif isinstance(data, (list, tuple)):
            return self.writeList
        elif t is UndefinedType:
            return self.writeUndefined
        elif t in (types.ClassType, types.TypeType):
            # can't encode classes
            raise EncodeError("Cannot encode %r" % (data,))
        elif t in (datetime.date, datetime.datetime, datetime.time):
            return self.writeDate
        elif t in (types.BuiltinFunctionType, types.BuiltinMethodType,
                types.FunctionType, types.GeneratorType, types.ModuleType,
                types.LambdaType, types.MethodType):
            # can't encode code objects
            raise EncodeError("Cannot encode %r" % (data,))

        for t, method in self.type_map.iteritems():
            if not isinstance(data, t):
                continue

            if callable(method):
                return lambda *args, **kwargs: method(self, *args, **kwargs)

            return getattr(self, method)

        return self.writeObject

    def writeElement(self, data, **kwargs):
        """
        Writes the data. Overridden in subclass.

        :type   data: `mixed`
        :param  data: The data to be encoded to the data stream.
        """
        key = type(data)
        func = None

        try:
            func = self._func_cache[key]
        except KeyError:
            func = self.getCustomTypeFunc(data)

            if not func:
                func = self.getTypeFunc(data)

            self._func_cache[key] = func

        func(data, **kwargs)


def register_class(klass, alias=None):
    """
    Registers a class to be used in the data streaming.

    :return: The registered :class:`ClassAlias`.
    """
    meta = util.get_class_meta(klass)

    if alias is not None:
        meta['alias'] = alias

    alias_klass = util.get_class_alias(klass)

    x = alias_klass(klass, defer=True, **meta)

    if not x.anonymous:
        CLASS_CACHE[x.alias] = x

    CLASS_CACHE[klass] = x

    return x


def unregister_class(alias):
    """
    Deletes a class from the cache.

    If `alias` is a class, the matching alias is found.

    :type alias: `class` or `str`
    :param alias: Alias for class to delete.
    :raise UnknownClassAlias: Unknown alias.
    """
    try:
        x = CLASS_CACHE[alias]
    except KeyError:
        raise UnknownClassAlias('Unknown alias %r' % (alias,))

    if not x.anonymous:
        del CLASS_CACHE[x.alias]

    del CLASS_CACHE[x.klass]

    return x


def get_class_alias(klass):
    """
    Finds the alias registered to the class.

    :type klass: `object` or class object.
    :return: The class alias linked to `klass`.
    :rtype: :class:`ClassAlias`
    :raise UnknownClassAlias: Class not found.
    """
    if isinstance(klass, basestring):
        try:
            return CLASS_CACHE[klass]
        except KeyError:
            return load_class(klass)

    if not isinstance(klass, (type, types.ClassType)):
        if isinstance(klass, types.InstanceType):
            klass = klass.__class__
        elif isinstance(klass, types.ObjectType):
            klass = type(klass)

    try:
        return CLASS_CACHE[klass]
    except KeyError:
        raise UnknownClassAlias('Unknown alias for %r' % (klass,))


def register_class_loader(loader):
    """
    Registers a loader that is called to provide the `Class` for a specific
    alias.

    The `loader` is provided with one argument, the `Class` alias. If the
    loader succeeds in finding a suitable class then it should return that
    class, otherwise it should return `None`.

    :type loader: `callable`
    :raise TypeError: The `loader` is not callable.
    :raise ValueError: The `loader` is already registered.
    """
    if not callable(loader):
        raise TypeError("loader must be callable")

    if loader in CLASS_LOADERS:
        raise ValueError("loader has already been registered")

    CLASS_LOADERS.append(loader)


def unregister_class_loader(loader):
    """
    Unregisters a class loader.

    :type loader: `callable`
    :param loader: The object to be unregistered

    :raise LookupError: The `loader` was not registered.
    """
    if loader not in CLASS_LOADERS:
        raise LookupError("loader not found")

    CLASS_LOADERS.remove(loader)


def get_module(mod_name):
    """
    Load a module based on `mod_name`.

    :type mod_name: `str`
    :param mod_name: The module name.
    :return: Module.

    :raise ImportError: Unable to import an empty module.
    """
    if mod_name is '':
        raise ImportError("Unable to import empty module")

    mod = __import__(mod_name)
    components = mod_name.split('.')

    for comp in components[1:]:
        mod = getattr(mod, comp)

    return mod


def load_class(alias):
    """
    Finds the class registered to the alias.

    The search is done in order:
      1. Checks if the class name has been registered via :func:`register_class`
         or :func:`register_package`.
      2. Checks all functions registered via :func:`register_class_loader`.
      3. Attempts to load the class via standard module loading techniques.

    :type alias: `str`
    :param alias: The class name.
    :raise UnknownClassAlias: The `alias` was not found.
    :raise TypeError: Expecting class type or :class:`ClassAlias` from loader.
    :return: Class registered to the alias.
    """
    alias = str(alias)

    # Try the CLASS_CACHE first
    try:
        return CLASS_CACHE[alias]
    except KeyError:
        pass

    # Check each CLASS_LOADERS in turn
    for loader in CLASS_LOADERS:
        klass = loader(alias)

        if klass is None:
            continue

        if isinstance(klass, (type, types.ClassType)):
            return register_class(klass, alias)
        elif isinstance(klass, ClassAlias):
            CLASS_CACHE[str(alias)] = klass
            CLASS_CACHE[klass.klass] = klass

            return klass
        else:
            raise TypeError("Expecting class type or ClassAlias from loader")

    # XXX nick: Are there security concerns for loading classes this way?
    mod_class = alias.split('.')

    if mod_class:
        module = '.'.join(mod_class[:-1])
        klass = mod_class[-1]

        try:
            module = get_module(module)
        except (ImportError, AttributeError):
            # XXX What to do here?
            pass
        else:
            klass = getattr(module, klass)

            if isinstance(klass, (type, types.ClassType)):
                return register_class(klass, alias)
            elif isinstance(klass, ClassAlias):
                CLASS_CACHE[str(alias)] = klass
                CLASS_CACHE[klass.klass] = klass

                return klass.klass
            else:
                raise TypeError("Expecting class type or ClassAlias from loader")

    # All available methods for finding the class have been exhausted
    raise UnknownClassAlias("Unknown alias for %r" % (alias,))


def decode(*args, **kwargs):
    """
    A generator function to decode a datastream.

    :kwarg stream: AMF data.
    :type stream: :class:`BufferedByteStream<pyamf.util.BufferedByteStream>`
    :type encoding: `int`
    :kwarg encoding: AMF encoding type.
    :type context: :class:`AMF0 Context<pyamf.amf0.Context>` or
                   :class:`AMF3 Context<pyamf.amf3.Context>`
    :kwarg context: Context.
    :return: Each element in the stream.
    """
    encoding = kwargs.pop('encoding', DEFAULT_ENCODING)
    decoder = _get_decoder_class(encoding)(*args, **kwargs)

    while 1:
        try:
            yield decoder.readElement()
        except EOStream:
            break


def encode(*args, **kwargs):
    """
    A helper function to encode an element.

    :type args: `mixed`
    :keyword element: Python data.
    :type encoding: `int`
    :keyword encoding: AMF encoding type.
    :type context: :class:`amf0.Context<pyamf.amf0.Context>` or
                   :class:`amf3.Context<pyamf.amf3.Context>`
    :keyword context: Context.

    :rtype: `StringIO`
    :return: File-like object.
    """
    encoding = kwargs.pop('encoding', DEFAULT_ENCODING)

    encoder = _get_encoder_class(encoding)(**kwargs)
    stream = encoder.stream

    for el in args:
        encoder.writeElement(el)

    stream.seek(0)

    return stream


def get_decoder(encoding, *args, **kwargs):
    """
    Returns a subclassed instance of :class:`BaseDecoder`, based on the
    `encoding` param.
    """
    return _get_decoder_class(encoding)(*args, **kwargs)


def _get_decoder_class(encoding):
    """
    Get compatible decoder.

    :type encoding: `int`
    :param encoding: AMF encoding version.
    :raise ValueError: AMF encoding version is unknown.

    :rtype: :class:`amf0.Decoder<pyamf.amf0.Decoder>` or
            :class:`amf3.Decoder<pyamf.amf3.Decoder>`
    :return: AMF0 or AMF3 decoder.
    """
    if encoding == AMF0:
        from pyamf import amf0

        return amf0.Decoder
    elif encoding == AMF3:
        from pyamf import amf3

        return amf3.Decoder

    raise ValueError("Unknown encoding %s" % (encoding,))


def get_encoder(encoding, *args, **kwargs):
    """
    Returns a subclassed instance of :class:`pyamf.BaseEncoder`, based on
    the `encoding` param.
    """
    return _get_encoder_class(encoding)(*args, **kwargs)


def _get_encoder_class(encoding):
    """
    Get compatible encoder.

    :type encoding: `int`
    :param encoding: AMF encoding version.
    :raise ValueError: AMF encoding version is unknown.

    :rtype: :class:`amf0.Encoder<pyamf.amf0.Encoder>` or
            :class:`amf3.Encoder<pyamf.amf3.Encoder>`
    :return: AMF0 or AMF3 encoder.
    """
    if encoding == AMF0:
        from pyamf import amf0

        return amf0.Encoder
    elif encoding == AMF3:
        from pyamf import amf3

        return amf3.Encoder

    raise ValueError("Unknown encoding %s" % (encoding,))


def get_context(encoding, **kwargs):
    return _get_context_class(encoding)(**kwargs)


def _get_context_class(encoding):
    """
    Gets a compatible context class.

    :type encoding: `int`
    :param encoding: AMF encoding version.
    :raise ValueError: AMF encoding version is unknown.

    :rtype: :class:`amf0.Context<pyamf.amf0.Context>` or
            :class:`amf3.Context<pyamf.amf3.Context>`
    :return: AMF0 or AMF3 context class.
    """
    if encoding == AMF0:
        from pyamf import amf0

        return amf0.Context
    elif encoding == AMF3:
        from pyamf import amf3

        return amf3.Context

    raise ValueError("Unknown encoding %s" % (encoding,))


def blaze_loader(alias):
    """
    Loader for BlazeDS framework compatibility classes, specifically
    implementing `ISmallMessage`.

    :see: `BlazeDS (external)<http://opensource.adobe.com/wiki/display/blazeds/BlazeDS>`
    :since: 0.5
    """
    if alias not in ['DSC', 'DSK']:
        return

    import pyamf.flex.messaging

    return CLASS_CACHE[alias]


def flex_loader(alias):
    """
    Loader for :package:`Flex<pyamf.flex>` framework compatibility classes.

    :raise UnknownClassAlias: Trying to load an unknown Flex compatibility class.
    """
    if not alias.startswith('flex.'):
        return

    try:
        if alias.startswith('flex.messaging.messages'):
            import pyamf.flex.messaging
        elif alias.startswith('flex.messaging.io'):
            import pyamf.flex
        elif alias.startswith('flex.data.messages'):
            import pyamf.flex.data

        return CLASS_CACHE[alias]
    except KeyError:
        raise UnknownClassAlias(alias)


def add_type(type_, func=None):
    """
    Adds a custom type to :data:`TYPE_MAP`. A custom type allows fine grain control
    of what to encode to an AMF data stream.

    :raise TypeError: Unable to add as a custom type (expected a class or callable).
    :raise KeyError: Type already exists.
    """
    def _check_type(type_):
        if not (isinstance(type_, (type, types.ClassType)) or callable(type_)):
            raise TypeError(r'Unable to add '%r' as a custom type (expected a '
                'class or callable)' % (type_,))

    if isinstance(type_, list):
        type_ = tuple(type_)

    if type_ in TYPE_MAP:
        raise KeyError('Type %r already exists' % (type_,))

    if isinstance(type_, types.TupleType):
        for x in type_:
            _check_type(x)
    else:
        _check_type(type_)

    TYPE_MAP[type_] = func


def get_type(type_):
    """
    Gets the declaration for the corresponding custom type.

    :raise KeyError: Unknown type.
    """
    if isinstance(type_, list):
        type_ = tuple(type_)

    for (k, v) in TYPE_MAP.iteritems():
        if k == type_:
            return v

    raise KeyError("Unknown type %r" % (type_,))


def remove_type(type_):
    """
    Removes the custom type declaration.

    :return: Custom type declaration.
    """
    declaration = get_type(type_)

    del TYPE_MAP[type_]

    return declaration


def add_error_class(klass, code):
    """
    Maps an exception class to a string code. Used to map remoting `onStatus`
    objects to an exception class so that an exception can be built to
    represent that error.

    :type code: `str`
    :raise TypeError: `klass` must be a `class` type.
    :raise TypeError: Error classes must subclass the `__builtin__.Exception` class.
    :raise ValueError: Code is already registered.
    """
    if not isinstance(code, basestring):
        code = str(code)

    if not isinstance(klass, (type, types.ClassType)):
        raise TypeError("klass must be a class type")

    mro = inspect.getmro(klass)

    if not Exception in mro:
        raise TypeError('Error classes must subclass the __builtin__.Exception class')

    if code in ERROR_CLASS_MAP.keys():
        raise ValueError('Code %s is already registered' % (code,))

    ERROR_CLASS_MAP[code] = klass


def remove_error_class(klass):
    """
    Removes a class from :data:`ERROR_CLASS_MAP`.

    :raise ValueError: Code is not registered.
    :raise ValueError: Class is not registered.
    :raise TypeError: Invalid type, expected `class` or `string`.
    """
    if isinstance(klass, basestring):
        if not klass in ERROR_CLASS_MAP.keys():
            raise ValueError('Code %s is not registered' % (klass,))
    elif isinstance(klass, (type, types.ClassType)):
        classes = ERROR_CLASS_MAP.values()
        if not klass in classes:
            raise ValueError('Class %s is not registered' % (klass,))

        klass = ERROR_CLASS_MAP.keys()[classes.index(klass)]
    else:
        raise TypeError("Invalid type, expected class or string")

    del ERROR_CLASS_MAP[klass]


def register_alias_type(klass, *args):
    """
    This function allows you to map subclasses of :class:`ClassAlias` to classes
    listed in `args`.

    When an object is read/written from/to the AMF stream, a paired
    :class:`ClassAlias` instance is created (or reused), based on the Python class
    of that object. :class:`ClassAlias` provides important metadata for the class
    and can also control how the equivalent Python object is created, how the
    attributes are applied etc.

    Use this function if you need to do something non-standard.

    :see: :class:`pyamf.adapters._google_appengine_ext_db.DataStoreClassAlias` for a
          good example.
    :since: 0.4
    :raise RuntimeError: Type is already registered.
    :raise TypeError: `klass` must be a class.
    :raise ValueError: New aliases must subclass :class:`pyamf.ClassAlias`.
    :raise ValueError: At least one type must be supplied.
    """

    def check_type_registered(arg):
        # FIXME: Create a reverse index of registered types and do a quicker lookup
        for k, v in ALIAS_TYPES.iteritems():
            for kl in v:
                if arg is kl:
                    raise RuntimeError('%r is already registered under %r' % (arg, k))

    if not isinstance(klass, (type, types.ClassType)):
        raise TypeError('klass must be class')

    if not issubclass(klass, ClassAlias):
        raise ValueError('New aliases must subclass pyamf.ClassAlias')

    if len(args) == 0:
        raise ValueError('At least one type must be supplied')

    if len(args) == 1 and callable(args[0]):
        c = args[0]

        check_type_registered(c)
    else:
        for arg in args:
            if not isinstance(arg, (type, types.ClassType)):
                raise TypeError('%r must be class' % (arg,))

            check_type_registered(arg)

    ALIAS_TYPES[klass] = args


def unregister_alias_type(klass):
    """
    Removes the klass from the :data:`ALIAS_TYPE` register.

    :see: :func:`register_alias_type`
    """
    return ALIAS_TYPES.pop(klass, None)


def register_package(module=None, package=None, separator='.', ignore=[],
                     strict=True):
    """
    This is a helper function that takes the concept of Actionscript packages
    and registers all the classes in the supplied Python module under that
    package. It auto-aliased all classes in `module` based on `package`.

    :param module: The Python module that will contain all the classes to
                   auto alias.
    :type module: `module` or `dict`
    :param package: The base package name. e.g. 'com.example.app'. If this
                    is `None` then the value is inferred from `module.__name__`.
    :type package: `str` or `unicode` or `None`
    :param separator: The separator used to append to `package` to form the
                      complete alias.
    :type separator: `str`
    :param ignore: To give fine grain control over what gets aliased and what
                   doesn't, supply a list of classes that you **do not** want to
                   be aliased.
    :type ignore: `iterable`
    :param strict: If this value is `True` then only classes that originate
                   from `module` will be registered, all others will be left
                   in peace.
    :type strict: `bool`

    :raise TypeError: Cannot get list of classes from module
    :return: A collection of all the classes that were registered and their
             respective :class:`ClassAlias` objects.
    :since: 0.5
    """
    if isinstance(module, basestring):
        if module == '':
            raise TypeError('Cannot get list of classes from %r' % (module,))

        package = module
        module = None

    if module is None:
        import inspect

        prev_frame = inspect.stack()[1][0]
        module = prev_frame.f_locals

    if type(module) is dict:
        has = lambda x: x in module.keys()
        get = module.__getitem__
    elif type(module) is list:
        has = lambda x: x in module
        get = module.__getitem__
        strict = False
    else:
        has = lambda x: hasattr(module, x)
        get = lambda x: getattr(module, x)

    if package is None:
        if has('__name__'):
            package = get('__name__')
        else:
            raise TypeError('Cannot get list of classes from %r' % (module,))

    if has('__all__'):
        keys = get('__all__')
    elif hasattr(module, '__dict__'):
        keys = module.__dict__.keys()
    elif hasattr(module, 'keys'):
        keys = module.keys()
    elif isinstance(module, list):
        keys = range(len(module))
    else:
        raise TypeError('Cannot get list of classes from %r' % (module,))

    def check_attr(attr):
        if not isinstance(attr, (types.ClassType, types.TypeType)):
            return False

        if attr.__name__ in ignore:
            return False

        try:
            if strict and attr.__module__ != get('__name__'):
                return False
        except AttributeError:
            return False

        return True

    # gotta love python
    classes = filter(check_attr, [get(x) for x in keys])

    registered = {}

    for klass in classes:
        alias = '%s%s%s' % (package, separator, klass.__name__)

        registered[klass] = register_class(klass, alias)

    return registered


#: setup some some standard class registrations and class loaders.
register_class(ASObject)
register_class_loader(flex_loader)
register_class_loader(blaze_loader)
register_alias_type(TypedObjectClassAlias, TypedObject)
register_alias_type(ErrorAlias, Exception)

register_adapters()
