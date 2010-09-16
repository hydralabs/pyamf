# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
U{PyAMF<http://pyamf.org>} provides Action Message Format (U{AMF
<http://en.wikipedia.org/wiki/Action_Message_Format>}) support for Python that
is compatible with the Adobe U{Flash Player
<http://en.wikipedia.org/wiki/Flash_Player>}.

@since: October 2007
@status: Production/Stable
"""

import types
import inspect

from pyamf import util, versions as v
from pyamf.adapters import register_adapters
from pyamf import python


__all__ = [
    'register_class',
    'register_class_loader',
    'encode',
    'decode',
    '__version__',
    'version'
]

#: PyAMF version number.
__version__ = version = v.Version(0, 6, 0, 'b2')

#: Class alias mapping support. Contains two types of keys: The string alias
#: related to the class and the class object itself. Both point to the linked
#: L{ClassAlias} object.
CLASS_CACHE = {}
#: Class loaders. An iterable of callables that are handed a string alias and
#: return a class object or C{None} it not handled.
CLASS_LOADERS = set()
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

#: Represents the C{undefined} value in the Adobe Flash Player client.
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
    Raised if an AMF data stream refers to a non-existent object or string
    reference (in the case of AMF3).
    """


class EncodeError(BaseError):
    """
    Raised if the element could not be encoded to AMF.
    """


class UnknownClassAlias(BaseError):
    """
    Raised if the AMF stream specifies an Actionscript class that does not
    have a Python class alias.

    @see: L{register_class}
    """


class ASObject(dict):
    """
    This class represents a Flash Actionscript Object (typed or untyped).

    I supply a C{dict} interface to support C{getattr}/C{setattr} calls.
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
    Used to be able to specify the C{mixedarray} type.
    """


class ClassAlias(object):
    """
    Class alias. Provides class/instance meta data to the En/Decoder to allow
    fine grain control and some performance increases.
    """

    def __init__(self, klass, alias=None, **kwargs):
        if not isinstance(klass, python.class_types):
            raise TypeError('klass must be a class type, got %r' % type(klass))

        self.checkClass(klass)

        self.klass = klass
        self.alias = alias

        if hasattr(self.alias, 'decode'):
            self.alias = self.alias.decode('utf-8')

        self.static_attrs = kwargs.pop('static_attrs', None)
        self.exclude_attrs = kwargs.pop('exclude_attrs', None)
        self.readonly_attrs = kwargs.pop('readonly_attrs', None)
        self.proxy_attrs = kwargs.pop('proxy_attrs', None)
        self.amf3 = kwargs.pop('amf3', None)
        self.external = kwargs.pop('external', None)
        self.dynamic = kwargs.pop('dynamic', None)
        self.synonym_attrs = kwargs.pop('synonym_attrs', {})

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
        k = self.klass

        if not hasattr(k, '__readamf__'):
            raise AttributeError("An externalised class was specified, but"
                " no __readamf__ attribute was found for %r" % (k,))

        if not hasattr(k, '__writeamf__'):
            raise AttributeError("An externalised class was specified, but"
                " no __writeamf__ attribute was found for %r" % (k,))

        if not hasattr(k.__readamf__, '__call__'):
            raise TypeError("%s.__readamf__ must be callable" % (k.__name__,))

        if not hasattr(k.__writeamf__, '__call__'):
            raise TypeError("%s.__writeamf__ must be callable" % (k.__name__,))

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
        self.static_attrs = list(self.static_attrs or [])
        self.static_attrs_set = set(self.static_attrs)
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
            self.static_attrs_set.update(alias.static_attrs)

            for a in alias.static_attrs:
                if a not in self.static_attrs:
                    self.static_attrs.insert(0, a)

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

        if alias.synonym_attrs:
            self.synonym_attrs, x = alias.synonym_attrs.copy(), self.synonym_attrs
            self.synonym_attrs.update(x)

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
                self.static_attrs_set.difference_update(self.exclude_attrs)

            for a in self.static_attrs_set:
                if a not in self.static_attrs:
                    self.static_attrs.remove(a)

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

        if (self.encodable_properties or self.static_attrs or
                self.exclude_attrs or self.proxy_attrs or self.external or
                self.synonym_attrs):
            self.shortcut_encode = False

        if (self.decodable_properties or self.static_attrs or
                self.exclude_attrs or self.readonly_attrs or
                not self.dynamic or self.external or self.synonym_attrs):
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
        k = self.__class__

        return '<%s.%s alias=%r class=%r @ 0x%x>' % (k.__module__, k.__name__,
            self.alias, self.klass, id(self))

    def __eq__(self, other):
        if isinstance(other, basestring):
            return self.alias == other
        elif isinstance(other, self.__class__):
            return self.klass == other.klass
        elif isinstance(other, python.class_types):
            return self.klass == other
        else:
            return False

    def __hash__(self):
        return id(self)

    def checkClass(self, klass):
        """
        This function is used to check if the class being aliased fits certain
        criteria. The default is to check that C{__new__} is available or the
        C{__init__} constructor does not need additional arguments. If this is
        the case then L{TypeError} will be raised.

        @since: 0.4
        """
        # Check for __new__ support.
        if hasattr(klass, '__new__') and hasattr(klass.__new__, '__call__'):
            # Should be good to go.
            return

        # Check that the constructor of the class doesn't require any additonal
        # arguments.
        if not (hasattr(klass, '__init__') and hasattr(klass.__init__, '__call__')):
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
        Must return a C{dict} of attributes to be encoded, even if its empty.

        @param codec: An optional argument that will contain the encoder
            instance calling this function.
        @since: 0.5
        """
        if not self._compiled:
            self.compile()

        if self.is_dict:
            return dict(obj)

        if self.shortcut_encode and self.dynamic:
            return obj.__dict__.copy()

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

        for attr in dynamic_props:
            attrs[attr] = getattr(obj, attr)

        if self.proxy_attrs is not None and attrs and codec:
            context = codec.context

            for k, v in attrs.copy().iteritems():
                if k in self.proxy_attrs:
                    attrs[k] = context.getProxyForObject(v)

        if self.synonym_attrs:
            missing = object()

            for k, v in self.synonym_attrs.iteritems():
                value = attrs.pop(k, missing)

                if value is missing:
                    continue

                attrs[v] = value

        return attrs

    def getDecodableAttributes(self, obj, attrs, codec=None):
        """
        Returns a dictionary of attributes for C{obj} that has been filtered,
        based on the supplied C{attrs}. This allows for fine grain control
        over what will finally end up on the object or not.

        @param obj: The object that will recieve the attributes.
        @param attrs: The C{attrs} dictionary that has been decoded.
        @param codec: An optional argument that will contain the decoder
            instance calling this function.
        @return: A dictionary of attributes that can be applied to C{obj}
        @since: 0.5
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

        if self.synonym_attrs:
            missing = object()

            for k, v in self.synonym_attrs.iteritems():
                value = attrs.pop(k, missing)

                if value is missing:
                    continue

                attrs[v] = value

        if not changed:
            return attrs

        a = {}

        [a.__setitem__(p, attrs[p]) for p in props]

        return a

    def applyAttributes(self, obj, attrs, codec=None):
        """
        Applies the collection of attributes C{attrs} to aliased object C{obj}.
        Called when decoding reading aliased objects from an AMF byte stream.

        Override this to provide fine grain control of application of
        attributes to C{obj}.

        @param codec: An optional argument that will contain the en/decoder
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

        @since: 0.5
        """

    def createInstance(self, codec=None):
        """
        Creates an instance of the klass.

        @return: Instance of C{self.klass}.
        """
        if type(self.klass) is type:
            return self.klass.__new__(self.klass)

        return self.klass()


class TypedObject(dict):
    """
    This class is used when a strongly typed object is decoded but there is no
    registered class to apply it to.

    This object can only be used for standard streams - i.e. not externalized
    data. If encountered, a L{DecodeError} will be raised.

    @ivar alias: The alias of the typed object.
    @type alias: C{string}
    @since: 0.4
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
            'the alias and a corresponding __writeamf__ method will be '
            'required.' % (self.alias,))


class TypedObjectClassAlias(ClassAlias):
    """
    The meta class for L{TypedObject} used to adapt PyAMF.

    @since: 0.4
    """

    klass = TypedObject

    def __init__(self, *args, **kwargs):
        ClassAlias.__init__(self, self.klass, kwargs.pop('alias', args[0]))

    def createInstance(self, codec=None):
        return self.klass(self.alias)

    def checkClass(kls, klass):
        pass


class ErrorAlias(ClassAlias):
    """
    Adapts Python exception objects to Adobe Flash Player error objects.

    @since: 0.5
    """

    def getCustomProperties(self):
        self.exclude_attrs.update(['args'])

    def getEncodableAttributes(self, obj, **kwargs):
        attrs = ClassAlias.getEncodableAttributes(self, obj, **kwargs)

        attrs['message'] = str(obj)
        attrs['name'] = obj.__class__.__name__

        return attrs


def register_class(klass, alias=None):
    """
    Registers a class to be used in the data streaming. This is the equivalent
    to the C{[RemoteClass(alias="foobar")]} AS3 metatag.

    @return: The registered L{ClassAlias} instance.
    """
    meta = util.get_class_meta(klass)

    if alias is not None:
        meta['alias'] = alias

    alias_klass = util.get_class_alias(klass) or ClassAlias

    x = alias_klass(klass, defer=True, **meta)

    if not x.anonymous:
        CLASS_CACHE[x.alias] = x

    CLASS_CACHE[klass] = x

    return x


def unregister_class(alias):
    """
    Opposite of L{register_class}.

    @raise UnknownClassAlias: Unknown alias.
    """
    try:
        x = CLASS_CACHE[alias]
    except KeyError:
        raise UnknownClassAlias('Unknown alias %r' % (alias,))

    if not x.anonymous:
        del CLASS_CACHE[x.alias]

    del CLASS_CACHE[x.klass]

    return x


def get_class_alias(klass_or_alias):
    """
    Finds the L{ClassAlias} that is registered to C{klass_or_alias}.

    If a string is supplied and no related L{ClassAlias} is found, the alias is
    loaded via L{load_class}.

    @raise UnknownClassAlias: Unknown alias
    """
    if isinstance(klass_or_alias, python.str_types):
        try:
            return CLASS_CACHE[klass_or_alias]
        except KeyError:
            return load_class(klass_or_alias)

    try:
        return CLASS_CACHE[klass_or_alias]
    except KeyError:
        raise UnknownClassAlias('Unknown alias for %r' % (klass_or_alias,))


def register_class_loader(loader):
    """
    Registers a loader that is called to provide the C{class} for a specific
    alias.

    The C{loader} is provided with one argument, the class alias (as a string).
    If the loader succeeds in finding a suitable class then it should return
    that class, otherwise it should return C{None}.

    An example::

        def lazy_load_from_my_module(alias):
            if not alias.startswith('foo.bar.'):
                return None

            from foo import bar

            if alias == 'foo.bar.Spam':
                return bar.Spam
            elif alias == 'foo.bar.Eggs':
                return bar.Eggs

        pyamf.register_class_loader(lazy_load_from_my_module)
    """
    if not hasattr(loader, '__call__'):
        raise TypeError("loader must be callable")

    CLASS_LOADERS.update([loader])


def unregister_class_loader(loader):
    """
    Unregisters a class loader.

    @param loader: The class loader to be unregistered.
    @raise LookupError: The {loader} was not registered.
    """
    try:
        CLASS_LOADERS.remove(loader)
    except KeyError:
        raise LookupError("loader not found")


def load_class(alias):
    """
    Finds the class registered to the alias.

    The search is done in order:
      1. Checks if the class name has been registered via L{register_class}
         or L{register_package}.
      2. Checks all functions registered via L{register_class_loader}.
      3. Attempts to load the class via standard module loading techniques.

    @param alias: The class name.
    @type alias: C{string}
    @raise UnknownClassAlias: The C{alias} was not found.
    @raise TypeError: Expecting class type or L{ClassAlias} from loader.
    @return: Class registered to the alias.
    @rtype: C{classobj}
    """
    # Try the CLASS_CACHE first
    try:
        return CLASS_CACHE[alias]
    except KeyError:
        pass

    for loader in CLASS_LOADERS:
        klass = loader(alias)

        if klass is None:
            continue

        if isinstance(klass, python.class_types):
            return register_class(klass, alias)
        elif isinstance(klass, ClassAlias):
            CLASS_CACHE[klass.alias] = klass
            CLASS_CACHE[klass.klass] = klass

            return klass

        raise TypeError("Expecting class object or ClassAlias from loader")

    mod_class = alias.split('.')

    if mod_class:
        module = '.'.join(mod_class[:-1])
        klass = mod_class[-1]

        try:
            module = util.get_module(module)
        except (ImportError, AttributeError):
            pass
        else:
            klass = getattr(module, klass)

            if isinstance(klass, python.class_types):
                return register_class(klass, alias)
            elif isinstance(klass, ClassAlias):
                CLASS_CACHE[klass.alias] = klass
                CLASS_CACHE[klass.klass] = klass

                return klass.klass
            else:
                raise TypeError("Expecting class type or ClassAlias from loader")

    # All available methods for finding the class have been exhausted
    raise UnknownClassAlias("Unknown alias for %r" % (alias,))


def decode(stream, *args, **kwargs):
    """
    A generator function to decode a datastream.

    @param stream: AMF data to be decoded.
    @type stream: byte data.
    @kwarg encoding: AMF encoding type. One of L{ENCODING_TYPES}.
    @return: A generator that will decode each element in the stream.
    """
    encoding = kwargs.pop('encoding', DEFAULT_ENCODING)
    decoder = get_decoder(encoding, stream, *args, **kwargs)

    while True:
        try:
            yield decoder.readElement()
        except EOStream:
            break


def encode(*args, **kwargs):
    """
    A helper function to encode an element.

    @param args: The python data to be encoded.
    @kwarg encoding: AMF encoding type. One of L{ENCODING_TYPES}.
    @return: A L{util.BufferedByteStream} object that contains the data.
    """
    encoding = kwargs.pop('encoding', DEFAULT_ENCODING)
    encoder = get_encoder(encoding, **kwargs)

    [encoder.writeElement(el) for el in args]

    stream = encoder.stream
    stream.seek(0)

    return stream


def get_decoder(encoding, *args, **kwargs):
    """
    Returns a L{codec.Decoder} capable of decoding AMF[C{encoding}] streams.

    @raise ValueError: Unknown C{encoding}.
    """
    def _get_decoder_class():
        if encoding == AMF0:
            try:
                from cpyamf import amf0
            except ImportError:
                from pyamf import amf0

            return amf0.Decoder
        elif encoding == AMF3:
            try:
                from cpyamf import amf3
            except ImportError:
                from pyamf import amf3

            return amf3.Decoder

        raise ValueError("Unknown encoding %r" % (encoding,))

    return _get_decoder_class()(*args, **kwargs)


def get_encoder(encoding, *args, **kwargs):
    """
    Returns a L{codec.Encoder} capable of encoding AMF[C{encoding}] streams.

    @raise ValueError: Unknown C{encoding}.
    """
    def _get_encoder_class():
        if encoding == AMF0:
            try:
                from cpyamf import amf0
            except ImportError:
                from pyamf import amf0

            return amf0.Encoder
        elif encoding == AMF3:
            try:
                from cpyamf import amf3
            except ImportError:
                from pyamf import amf3

            return amf3.Encoder

        raise ValueError("Unknown encoding %r" % (encoding,))

    return _get_encoder_class()(*args, **kwargs)


def blaze_loader(alias):
    """
    Loader for BlazeDS framework compatibility classes, specifically
    implementing C{ISmallMessage}.

    @see: U{BlazeDS<http://opensource.adobe.com/wiki/display/blazeds/BlazeDS>}
    @since: 0.5
    """
    if alias not in ['DSC', 'DSK']:
        return

    import pyamf.flex.messaging

    return CLASS_CACHE[alias]


def flex_loader(alias):
    """
    Loader for L{Flex<pyamf.flex>} framework compatibility classes.

    @raise UnknownClassAlias: Trying to load an unknown Flex compatibility class.
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
    Adds a custom type to L{TYPE_MAP}. A custom type allows fine grain control
    of what to encode to an AMF data stream.

    @raise TypeError: Unable to add as a custom type (expected a class or callable).
    @raise KeyError: Type already exists.
    """
    def _check_type(type_):
        if not (isinstance(type_, python.class_types) or
                hasattr(type_, '__call__')):
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

    @raise KeyError: Unknown type.
    """
    if isinstance(type_, list):
        type_ = tuple(type_)

    for k, v in TYPE_MAP.iteritems():
        if k == type_:
            return v

    raise KeyError("Unknown type %r" % (type_,))


def remove_type(type_):
    """
    Removes the custom type declaration.

    @return: Custom type declaration.
    """
    declaration = get_type(type_)

    del TYPE_MAP[type_]

    return declaration


def add_error_class(klass, code):
    """
    Maps an exception class to a string code. Used to map remoting C{onStatus}
    objects to an exception class so that an exception can be built to
    represent that error.
    """
    if not isinstance(code, python.str_types):
        code = code.decode('utf-8')

    if not isinstance(klass, python.class_types):
        raise TypeError("klass must be a class type")

    mro = inspect.getmro(klass)

    if not Exception in mro:
        raise TypeError(
            'Error classes must subclass the __builtin__.Exception class')

    if code in ERROR_CLASS_MAP:
        raise ValueError('Code %s is already registered' % (code,))

    ERROR_CLASS_MAP[code] = klass


def remove_error_class(klass):
    """
    Removes a class from L{ERROR_CLASS_MAP}.
    """
    if isinstance(klass, python.str_types):
        if klass not in ERROR_CLASS_MAP:
            raise ValueError('Code %s is not registered' % (klass,))
    elif isinstance(klass, python.class_types):
        classes = ERROR_CLASS_MAP.values()
        if klass not in classes:
            raise ValueError('Class %s is not registered' % (klass,))

        klass = ERROR_CLASS_MAP.keys()[classes.index(klass)]
    else:
        raise TypeError("Invalid type, expected class or string")

    del ERROR_CLASS_MAP[klass]


def register_alias_type(klass, *args):
    """
    This function allows you to map subclasses of L{ClassAlias} to classes
    listed in C{args}.

    When an object is read/written from/to the AMF stream, a paired L{ClassAlias}
    instance is created (or reused), based on the Python class of that object.
    L{ClassAlias} provides important metadata for the class and can also control
    how the equivalent Python object is created, how the attributes are applied
    etc.

    Use this function if you need to do something non-standard.

    @see: L{pyamf.adapters._google_appengine_ext_db.DataStoreClassAlias} for a
        good example.
    @since: 0.4
    """

    def check_type_registered(arg):
        for k, v in ALIAS_TYPES.iteritems():
            for kl in v:
                if arg is kl:
                    raise RuntimeError('%r is already registered under %r' % (
                        arg, k))

    if not isinstance(klass, python.class_types):
        raise TypeError('klass must be class')

    if not issubclass(klass, ClassAlias):
        raise ValueError('New aliases must subclass pyamf.ClassAlias')

    if len(args) == 0:
        raise ValueError('At least one type must be supplied')

    if len(args) == 1 and hasattr(args[0], '__call__'):
        c = args[0]

        check_type_registered(c)
    else:
        for arg in args:
            if not isinstance(arg, python.class_types):
                raise TypeError('%r must be class' % (arg,))

            check_type_registered(arg)

    ALIAS_TYPES[klass] = args

    for k, v in CLASS_CACHE.copy().iteritems():
        new_alias = util.get_class_alias(v.klass)

        if new_alias is klass:
            meta = util.get_class_meta(v.klass)
            meta['alias'] = v.alias

            alias_klass = klass(v.klass, **meta)

            CLASS_CACHE[k] = alias_klass
            CLASS_CACHE[v.klass] = alias_klass


def unregister_alias_type(klass):
    """
    Removes the klass from the L{ALIAS_TYPES} register.

    @see: L{register_alias_type}
    """
    return ALIAS_TYPES.pop(klass, None)


def register_package(module=None, package=None, separator='.', ignore=[],
                     strict=True):
    """
    This is a helper function that takes the concept of Actionscript packages
    and registers all the classes in the supplied Python module under that
    package. It auto-aliased all classes in C{module} based on the parent
    C{package}.

    @param module: The Python module that will contain all the classes to
        auto alias.
    @type module: C{module} or C{dict}
    @param package: The base package name. e.g. 'com.example.app'. If this
        is C{None} then the value is inferred from C{module.__name__}.
    @type package: C{string} or C{None}
    @param separator: The separator used to append to C{package} to form the
        complete alias.
    @param ignore: To give fine grain control over what gets aliased and what
        doesn't, supply a list of classes that you B{do not} want to be aliased.
    @type ignore: C{iterable}
    @param strict: Whether only classes that originate from C{module} will be
        registered.

    @return: A dict of all the classes that were registered and their respective
        L{ClassAlias} counterparts.
    @since: 0.5
    """
    if isinstance(module, python.str_types):
        if module == '':
            raise TypeError('Cannot get list of classes from %r' % (module,))

        package = module
        module = None

    if module is None:
        import inspect

        prev_frame = inspect.stack()[1][0]
        module = prev_frame.f_locals

    if type(module) is dict:
        has = lambda x: x in module
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
        if not isinstance(attr, python.class_types):
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


def set_default_etree(etree):
    """
    Sets the default interface that will called apon to both de/serialise XML
    entities. This means providing both C{tostring} and C{fromstring} functions.

    For testing purposes, will return the previous value for this (if any).
    """
    from pyamf import xml

    return xml.set_default_interface(etree)


#: setup some some standard class registrations and class loaders.
register_class(ASObject)
register_class_loader(flex_loader)
register_class_loader(blaze_loader)
register_alias_type(TypedObjectClassAlias, TypedObject)
register_alias_type(ErrorAlias, Exception)

register_adapters()
