# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
B{PyAMF} provides B{A}ction B{M}essage B{F}ormat
(U{AMF<http://en.wikipedia.org/wiki/Action_Message_Format>}) support for
Python that is compatible with the
U{Flash Player<http://en.wikipedia.org/wiki/Flash_Player>}.

@copyright: Copyright (c) 2007-2008 The PyAMF Project. All Rights Reserved.
@contact: U{dev@pyamf.org<mailto:dev@pyamf.org>}
@see: U{http://pyamf.org}

@since: October 2007
@version: 0.4
"""

import types

from pyamf import util
from pyamf.adapters import register_adapters

__all__ = [
    'register_class',
    'register_class_loader',
    'encode',
    'decode',
    '__version__']

#: PyAMF version number.
__version__ = (0, 4, 0)

#: Class mapping support.
CLASS_CACHE = {}
#: Class loaders.
CLASS_LOADERS = []
#: Custom type map.
TYPE_MAP = {}
#: Maps error classes to string codes.
ERROR_CLASS_MAP = {}
#: Specifies that objects are serialized using AMF for ActionScript 1.0 and 2.0.
AMF0 = 0
#: Specifies that objects are serialized using AMF for ActionScript 3.0.
AMF3 = 3
#: Supported AMF encoding types.
ENCODING_TYPES = (AMF0, AMF3)

class ClientTypes:
    """
    Typecodes used to identify AMF clients and servers.

    @see: U{Flash Player on WikiPedia (external)
    <http://en.wikipedia.org/wiki/Flash_Player>}
    @see: U{Flash Media Server on WikiPedia (external)
    <http://en.wikipedia.org/wiki/Adobe_Flash_Media_Server>}
    """
    #: Specifies a Flash Player 6.0 - 8.0 client.
    Flash6   = 0
    #: Specifies a FlashCom / Flash Media Server client.
    FlashCom = 1
    #: Specifies a Flash Player 9.0 client.
    Flash9   = 3

#: List of AMF client typecodes.
CLIENT_TYPES = []

for x in ClientTypes.__dict__:
    if not x.startswith('_'):
        CLIENT_TYPES.append(ClientTypes.__dict__[x])
del x

#: Represents the C{undefined} value in a Flash client.
Undefined = object()

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

    @bug: See U{Docuverse blog (external)
    <http://www.docuverse.com/blog/donpark/2007/05/14/flash-9-amf3-bug>}
    for more info about the empty key string array bug.
    """

class UnknownClassAlias(BaseError):
    """
    Raised if the AMF stream specifies a class that does not
    have an alias.

    @see: L{register_class}
    """

class BaseContext(object):
    """
    I hold the AMF context for en/decoding streams.
    """
    def __init__(self):
        self.clear()

    def clear(self):
        """
        Clears the AMF context.
        """
        self.objects = []
        self.rev_objects = {}

        self.class_aliases = {}

    def getObject(self, ref):
        """
        Gets an object based on a reference.

        @raise TypeError: Bad reference type.
        """
        if not isinstance(ref, (int, long)):
            raise TypeError, "Bad reference type"

        try:
            return self.objects[ref]
        except IndexError:
            raise ReferenceError

    def getObjectReference(self, obj):
        """
        Gets a reference for an object.
        """
        try:
            return self.rev_objects[id(obj)]
        except KeyError:
            raise ReferenceError

    def addObject(self, obj):
        """
        Adds a reference to C{obj}.

        @type obj: C{mixed}
        @param obj: The object to add to the context.

        @rtype: C{int}
        @return: Reference to C{obj}.
        """
        self.objects.append(obj)
        idx = len(self.objects) - 1
        self.rev_objects[id(obj)] = idx

        return idx

    def getClassAlias(self, klass):
        """
        Gets a class alias based on the supplied C{klass}.
        """
        if klass not in self.class_aliases:
            try:
                self.class_aliases[klass] = get_class_alias(klass)
            except UnknownClassAlias:
                self.class_aliases[klass] = None

        return self.class_aliases[klass]

    def __copy__(self):
        raise NotImplementedError

class ASObject(dict):
    """
    This class represents a Flash Actionscript Object (typed or untyped).

    I supply a C{__builtin__.dict} interface to support C{get}/C{setattr}
    calls.

    @raise AttributeError: Unknown attribute.
    """
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)

    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError:
            raise AttributeError, 'unknown attribute \'%s\'' % k

    def __setattr__(self, k, v):
        self[k] = v

    def __repr__(self):
        return dict.__repr__(self)

class MixedArray(dict):
    """
    Used to be able to specify the C{mixedarray} type.
    """

class ClassMetaData(list):
    """
    I hold a list of tags relating to the class. The idea behind this is
    to emulate the metadata tags you can supply to ActionScript,
    e.g. C{static}/C{dynamic}.
    """
    _allowed_tags = (
        ('static', 'dynamic', 'external'),
        ('amf3', 'amf0'),
        ('anonymous',),
    )

    def __init__(self, *args):
        if len(args) == 1 and hasattr(args[0], '__iter__'):
            for x in args[0]:
                self.append(x)
        else:
            for x in args:
                self.append(x)

    def _is_tag_allowed(self, x):
        for y in self._allowed_tags:
            if isinstance(y, (types.ListType, types.TupleType)):
                if x in y:
                    return (True, y)
            else:
                if x == y:
                    return (True, None)

        return (False, None)

    def append(self, x):
        """
        Adds a tag to the metadata.

        @param x: Tag.

        @raise ValueError: Unknown tag.
        """
        x = str(x).lower()

        allowed, tags = self._is_tag_allowed(x)

        if not allowed:
            raise ValueError("Unknown tag %s" % x)

        if tags is not None:
            # check to see if a tag in the list is about to be clobbered if so,
            # raise a warning
            for y in tags:
                if y in self:
                    if x != y:
                        import warnings

                        warnings.warn(
                            "Previously defined tag %s superceded by %s" % (
                                y, x))

                    list.pop(self, self.index(y))
                    break

        list.append(self, x)

    def __contains__(self, other):
        return list.__contains__(self, str(other).lower())

    # TODO nick: deal with slices

class ClassAlias(object):
    """
    Class alias.

    All classes are initially set to a dynamic state.

    @ivar attrs: A list of attributes to encode for this class.
    @type attrs: C{list}
    @ivar metadata: A list of metadata tags similar to ActionScript tags.
    @type metadata: C{list}
    """
    def __init__(self, klass, alias, attrs=None, attr_func=None, metadata=[]):
        """
        @type klass: C{class}
        @param klass: The class to alias.
        @type alias: C{str}
        @param alias: The alias to the class e.g. C{org.example.Person}. If the
            value of this is C{None}, then it is worked out based on the C{klass}.
            The anonymous tag is also added to the class.
        @type attrs: A list of attributes to encode for this class.
        @param attrs: C{list}
        @type metadata: A list of metadata tags similar to ActionScript tags.
        @param metadata: C{list}

        @raise TypeError: The C{klass} must be a class type.
        @raise TypeError: The C{attr_func} must be callable.
        @raise TypeError: C{__readamf__} must be callable.
        @raise TypeError: C{__writeamf__} must be callable.
        @raise AttributeError: An externalised class was specified, but no
            C{__readamf__} attribute was found.
        @raise AttributeError: An externalised class was specified, but no
            C{__writeamf__} attribute was found.
        @raise ValueError: The C{attrs} keyword must be specified for static
            classes.
        """
        if not isinstance(klass, (type, types.ClassType)):
            raise TypeError, "klass must be a class type"

        self.metadata = ClassMetaData(metadata)

        if alias is None:
            self.metadata.append('anonymous')
            alias = "%s.%s" % (klass.__module__, klass.__name__,)

        self.klass = klass
        self.alias = alias
        self.attr_func = attr_func
        self.attrs = attrs

        if 'external' in self.metadata:
            # class is declared as external, lets check
            if not hasattr(klass, '__readamf__'):
                raise AttributeError("An externalised class was specified, but"
                    " no __readamf__ attribute was found for class %s" % (
                        klass.__name__))

            if not hasattr(klass, '__writeamf__'):
                raise AttributeError("An externalised class was specified, but"
                    " no __writeamf__ attribute was found for class %s" % (
                        klass.__name__))

            if not isinstance(klass.__readamf__, types.UnboundMethodType):
                raise TypeError, "%s.__readamf__ must be callable" % (
                    klass.__name__)

            if not isinstance(klass.__writeamf__, types.UnboundMethodType):
                raise TypeError, "%s.__writeamf__ must be callable" % (
                    klass.__name__)

        if 'dynamic' in self.metadata:
            if attr_func is not None and not callable(attr_func):
                raise TypeError, "attr_func must be callable"

        if 'static' in self.metadata:
            if attrs is None:
                raise ValueError, "attrs keyword must be specified for static classes"

    def __call__(self, *args, **kwargs):
        """
        Creates an instance of the klass.

        @raise TypeError: Invalid class type.
        @return: Instance of C{self.klass}.
        """
        if hasattr(self.klass, '__setstate__') or hasattr(self.klass, '__getstate__'):
            if type(self.klass) is types.TypeType:  # new-style class
                return self.klass.__new__(self.klass)
            elif type(self.klass) is types.ClassType: # classic class
                return util.make_classic_instance(self.klass)
            raise TypeError, 'invalid class type %r' % self.klass
        
        return self.klass(*args, **kwargs)

    def __str__(self):
        return self.alias

    def __repr__(self):
        return '<ClassAlias alias=%s klass=%s @ %s>' % (
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

    def getAttrs(self, obj, attrs=None, traverse=True):
        if attrs is None:
            attrs = []

        did_something = False

        if self.attrs is not None:
            did_something = True
            attrs += self.attrs

        if 'dynamic' in self.metadata and self.attr_func is not None:
            did_something = True
            extra_attrs = self.attr_func(obj)

            attrs += [key for key in extra_attrs if key not in attrs]

        if traverse is True:
            for base in util.get_mro(obj.__class__):
                try:
                    alias = get_class_alias(base)
                except UnknownClassAlias:
                    continue

                x = alias.getAttrs(obj, attrs, False)

                if x is not None:
                    attrs += x
                    did_something = True

        if did_something is False:
            return None

        a = []

        for x in attrs:
            if x not in a:
                a.append(x)

        return a

class BaseDecoder(object):
    """
    Base AMF decoder.

    @ivar context_class: The context for the decoding.
    @type context_class: An instance of C{BaseDecoder.context_class}
    @ivar type_map:
    @type type_map: C{list}
    @ivar stream: The underlying data stream.
    @type stream: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
    """
    context_class = BaseContext
    type_map = {}

    def __init__(self, data=None, context=None):
        """
        @type   data: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
        @param  data: Data stream.
        @type   context: L{Context<pyamf.amf0.Context>}
        @param  context: Context.
        @raise TypeError: The C{context} parameter must be of
        type L{Context<pyamf.amf0.Context>}.
        """
        # coerce data to BufferedByteStream
        if isinstance(data, util.BufferedByteStream):
            self.stream = data
        else:
            self.stream = util.BufferedByteStream(data)

        if context == None:
            self.context = self.context_class()
        elif isinstance(context, self.context_class):
            self.context = context
        else:
            raise TypeError, "context must be of type %s.%s" % (
                self.context_class.__module__, self.context_class.__name__)

    def readType(self):
        """
        Override in a subclass.
        """
        raise NotImplementedError

    def readElement(self):
        """
        Reads an AMF3 element from the data stream.

        @raise DecodeError: The ActionScript type is unsupported.
        @raise EOStream: No more data left to decode.
        """
        try:
            type = self.readType()
        except EOFError:
            raise EOStream

        try:
            func = getattr(self, self.type_map[type])
        except KeyError:
            raise DecodeError, "Unsupported ActionScript type 0x%02x" % type

        return func()

    def __iter__(self):
        """
        @raise StopIteration:
        """
        try:
            while 1:
                yield self.readElement()
        except EOFError:
            raise StopIteration

class CustomTypeFunc(object):
    """
    Custom type mappings.
    """
    def __init__(self, encoder, func):
        self.encoder = encoder
        self.func = func

    def __call__(self, data):
        self.encoder.writeElement(self.func(data))

class BaseEncoder(object):
    """
    Base AMF encoder.

    @ivar type_map: A list of types -> functions. The types is a list of
        possible instances or functions to call (that return a C{bool}) to
        determine the correct function to call to encode the data.
    @type type_map: C{list}
    @ivar context_class: Holds the class that will create context objects for
        the implementing C{Encoder}.
    @type context_class: C{type} or C{types.ClassType}
    @ivar stream: The underlying data stream.
    @type stream: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
    @ivar context: The context for the encoding.
    @type context: An instance of C{BaseEncoder.context_class}
    """
    context_class = BaseContext
    type_map = []

    def __init__(self, data=None, context=None):
        """
        @type   data: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
        @param  data: Data stream.
        @type   context: L{Context<pyamf.amf0.Context>}
        @param  context: Context.
        @raise TypeError: The C{context} parameter must be of type
            L{Context<pyamf.amf0.Context>}.
        """
        # coerce data to BufferedByteStream
        if isinstance(data, util.BufferedByteStream):
            self.stream = data
        else:
            self.stream = util.BufferedByteStream(data)

        if context == None:
            self.context = self.context_class()
        elif isinstance(context, self.context_class):
            self.context = context
        else:
            raise TypeError, "context must be of type %s.%s" % (
                self.context_class.__module__, self.context_class.__name__)

        self._write_elem_func_cache = {}

    def writeFunc(self, obj):
        """
        Not possible to encode functions.

        @raise EncodeError: Unable to encode function/methods.
        """
        raise EncodeError("Unable to encode function/methods")

    def _getWriteElementFunc(self, data):
        """
        Gets a function used to encode the data.

        @type   data: C{mixed}
        @param  data: Python data.
        @rtype: callable or C{None}.
        @return: The function used to encode data to the stream.
        """
        for type_, func in TYPE_MAP.iteritems():
            try:
                if isinstance(data, type_):
                    return CustomTypeFunc(self, func)
            except TypeError:
                if callable(type_) and type_(data):
                    return CustomTypeFunc(self, func)

        for tlist, method in self.type_map:
            for t in tlist:
                try:
                    if isinstance(data, t):
                        return getattr(self, method)
                except TypeError:
                    if callable(t) and t(data):
                        return getattr(self, method)

        return None

    def _writeElementFunc(self, data):
        """
        Gets a function used to encode the data.

        @type   data: C{mixed}
        @param  data: Python data.
        @rtype: callable or C{None}.
        @return: The function used to encode data to the stream.
        """
        try:
            key = data.__class__
        except AttributeError:
            return self._getWriteElementFunc(data)

        if key not in self._write_elem_func_cache:
            self._write_elem_func_cache[key] =  self._getWriteElementFunc(data)

        return self._write_elem_func_cache[key]

    def writeElement(self, data):
        """
        Writes the data. Override in subclass.

        @type   data: C{mixed}
        @param  data: The data to be encoded to the data stream.
        """
        raise NotImplementedError

def register_class(klass, alias=None, attrs=None, attr_func=None, metadata=[]):
    """
    Registers a class to be used in the data streaming.

    @type alias: C{str}
    @param alias: The alias of klass, i.e. C{org.example.Person}.
    @param attrs: A list of attributes that will be encoded for the class.
    @type attrs: C{list} or C{None}
    @type attr_func:
    @param attr_func:
    @type metadata:
    @param metadata:
    @raise TypeError: PyAMF doesn't support required init arguments.
    @raise TypeError: The C{klass} is not callable.
    @raise ValueError: The C{klass} or C{alias} is already registered.
    @return: The registered L{ClassAlias}.
    """
    if not callable(klass):
        raise TypeError, "klass must be callable"

    if klass in CLASS_CACHE:
        raise ValueError, "klass %s already registered" % klass

    if alias is not None and alias in CLASS_CACHE.keys():
        raise ValueError, "alias '%s' already registered" % alias

    # Check that the constructor of the class doesn't require any additonal
    # arguments.
    if hasattr(klass, '__init__') and hasattr(klass.__init__, 'im_func'):
        klass_func = klass.__init__.im_func
        # built-in classes don't have func_code
	# required arguments = Number of arguments - number of default values
	if hasattr(klass_func, 'func_code') and (
	   klass_func.func_code.co_argcount - len(klass_func.func_defaults or []) > 1):
            raise TypeError("PyAMF doesn't support required init arguments")

    x = ClassAlias(klass, alias, attr_func=attr_func, attrs=attrs,
        metadata=metadata)

    if alias is None:
        alias = "%s.%s" % (klass.__module__, klass.__name__,)

    CLASS_CACHE[alias] = x

    return x

def unregister_class(alias):
    """
    Deletes a class from the cache.

    If C{alias} is a class, the matching alias is found.

    @type alias: C{class} or C{str}
    @param alias: Alias for class to delete.
    @raise UnknownClassAlias: Unknown alias.
    """
    if isinstance(alias, (type, types.ClassType)):
        for s, a in CLASS_CACHE.iteritems():
            if a.klass == alias:
                alias = s
                break
    try:
        del CLASS_CACHE[alias]
    except KeyError:
        raise UnknownClassAlias, "Unknown alias %s" % alias

def register_class_loader(loader):
    """
    Registers a loader that is called to provide the C{Class} for a specific
    alias.

    The L{loader} is provided with one argument, the C{Class} alias. If the
    loader succeeds in finding a suitable class then it should return that
    class, otherwise it should return C{None}.

    @type loader: C{callable}
    @raise TypeError: The C{loader} is not callable.
    @raise ValueError: The C{loader} is already registered.
    """
    if not callable(loader):
        raise TypeError, "loader must be callable"

    if loader in CLASS_LOADERS:
        raise ValueError, "loader has already been registered"

    CLASS_LOADERS.append(loader)

def unregister_class_loader(loader):
    """
    Unregisters a class loader.

    @type loader: C{callable}
    @param loader: The object to be unregistered

    @raise LookupError: The C{loader} was not registered.
    """
    if loader not in CLASS_LOADERS:
        raise LookupError, "loader not found"

    del CLASS_LOADERS[CLASS_LOADERS.index(loader)]

def get_module(mod_name):
    """
    Load a module based on C{mod_name}.

    @type mod_name: C{str}
    @param mod_name: The module name.
    @return: Module.

    @raise ImportError: Unable to import an empty module.
    """
    if mod_name is '':
        raise ImportError, "Unable to import empty module"

    mod = __import__(mod_name)
    components = mod_name.split('.')

    for comp in components[1:]:
        mod = getattr(mod, comp)

    return mod

def load_class(alias):
    """
    Finds the class registered to the alias.

    The search is done in order:
      1. Checks if the class name has been registered via L{register_class}.
      2. Checks all functions registered via L{register_class_loader}.
      3. Attempts to load the class via standard module loading techniques.

    @type alias: C{str}
    @param alias: The class name.
    @raise UnknownClassAlias: The C{alias} was not found.
    @raise TypeError: Expecting class type or L{ClassAlias} from loader.
    @return: Class registered to the alias.
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
        else:
            raise TypeError, "Expecting class type or ClassAlias from loader"

        return klass

    # XXX nick: Are there security concerns for loading classes this way?
    mod_class = alias.split('.')

    if mod_class:
        module = '.'.join(mod_class[:-1])
        klass = mod_class[-1]

        try:
            module = get_module(module)
        except ImportError, AttributeError:
            # XXX What to do here?
            pass
        else:
            klass = getattr(module, klass)

            if callable(klass):
                CLASS_CACHE[alias] = klass

                return klass

    # All available methods for finding the class have been exhausted
    raise UnknownClassAlias, "Unknown alias %s" % alias

def get_class_alias(klass):
    """
    Finds the alias registered to the class.

    @type klass: C{object} or class
    @rtype: L{ClassAlias}
    @return: The class alias linked to the C{klass}.
    @raise UnknownClassAlias: Class not found.
    @raise TypeError: Expecting C{string} or C{class} type.
    """
    if not isinstance(klass, (type, types.ClassType, basestring)):
        if isinstance(klass, types.InstanceType):
            klass = klass.__class__
        elif isinstance(klass, types.ObjectType):
            klass = type(klass)

    if isinstance(klass, basestring):
        for a, k in CLASS_CACHE.iteritems():
            if klass == a:
                return k
    else:
        for a, k in CLASS_CACHE.iteritems():
            if klass == k.klass:
                return k

    if isinstance(klass, basestring):
        return load_class(klass)

    raise UnknownClassAlias, "Unknown alias %s" % klass

def has_alias(obj):
    """
    @rtype: C{bool}
    @return: Alias is available.
    """
    try:
        alias = get_class_alias(obj)
        return True
    except UnknownClassAlias:
        return False

def decode(stream, encoding=AMF0, context=None):
    """
    A generator function to decode a datastream.

    @type   stream: L{BufferedByteStream<pyamf.util.BufferedByteStream>}
    @param  stream: AMF data.
    @type   encoding: C{int}
    @param  encoding: AMF encoding type.
    @type   context: L{AMF0 Context<pyamf.amf0.Context>} or
    L{AMF3 Context<pyamf.amf3.Context>}
    @param  context: Context.
    @return: Each element in the stream.
    """
    decoder = _get_decoder_class(encoding)(stream, context)

    while 1:
        try:
            yield decoder.readElement()
        except EOStream:
            break

def encode(*args, **kwargs):
    """
    A helper function to encode an element.

    @type element: C{mixed}
    @keyword element: Python data.
    @type encoding: C{int}
    @keyword encoding: AMF encoding type.
    @type context: L{amf0.Context<pyamf.amf0.Context>} or
    L{amf3.Context<pyamf.amf3.Context>}
    @keyword context: Context.

    @rtype: C{StringIO}
    @return: File-like object.
    """
    encoding = kwargs.get('encoding', AMF0)
    context = kwargs.get('context', None)

    stream = util.BufferedByteStream()
    encoder = _get_encoder_class(encoding)(stream, context)

    for el in args:
        encoder.writeElement(el)

    stream.seek(0)

    return stream

def get_decoder(encoding, data=None, context=None):
    return _get_decoder_class(encoding)(data=data, context=context)

def _get_decoder_class(encoding):
    """
    Get compatible decoder.

    @type encoding: C{int}
    @param encoding: AMF encoding version.
    @raise ValueError: AMF encoding version is unknown.

    @rtype: L{amf0.Decoder<pyamf.amf0.Decoder>} or
    L{amf3.Decoder<pyamf.amf3.Decoder>}
    @return: AMF0 or AMF3 decoder.
    """
    if encoding == AMF0:
        from pyamf import amf0

        return amf0.Decoder
    elif encoding == AMF3:
        from pyamf import amf3

        return amf3.Decoder

    raise ValueError, "Unknown encoding %s" % encoding

def get_encoder(encoding, data=None, context=None):
    return _get_encoder_class(encoding)(data=data, context=context)

def _get_encoder_class(encoding):
    """
    Get compatible encoder.

    @type encoding: C{int}
    @param encoding: AMF encoding version.
    @raise ValueError: AMF encoding version is unknown.

    @rtype: L{amf0.Encoder<pyamf.amf0.Encoder>} or
    L{amf3.Encoder<pyamf.amf3.Encoder>}
    @return: AMF0 or AMF3 encoder.
    """
    if encoding == AMF0:
        from pyamf import amf0

        return amf0.Encoder
    elif encoding == AMF3:
        from pyamf import amf3

        return amf3.Encoder

    raise ValueError, "Unknown encoding %s" % encoding

def get_context(encoding):
    return _get_context_class(encoding)()

def _get_context_class(encoding):
    """
    Gets a compatible context class.

    @type encoding: C{int}
    @param encoding: AMF encoding version.
    @raise ValueError: AMF encoding version is unknown.

    @rtype: L{amf0.Context<pyamf.amf0.Context>} or
    L{amf3.Context<pyamf.amf3.Context>}
    @return: AMF0 or AMF3 context class.
    """
    if encoding == AMF0:
        from pyamf import amf0

        return amf0.Context
    elif encoding == AMF3:
        from pyamf import amf3

        return amf3.Context

    raise ValueError, "Unknown encoding %s" % encoding

def flex_loader(alias):
    """
    Loader for L{Flex<pyamf.flex>} framework compatibility classes.

    @raise UnknownClassAlias: Trying to load unknown Flex compatibility class.
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
        raise UnknownClassAlias, alias

register_class_loader(flex_loader)

def add_type(type_, func=None):
    """
    Adds a custom type to L{TYPE_MAP}. A custom type allows fine grain control
    of what to encode to an AMF data stream.

    @raise TypeError: Unable to add as a custom type (expected a class or callable).
    @raise KeyError: Type already exists.
    """
    def _check_type(type_):
        if not (isinstance(type_, (type, types.ClassType)) or callable(type_)):
            raise TypeError, "Unable to add '%r' as a custom type (expected a class or callable)" % type_

    if isinstance(type_, list):
        type_ = tuple(type_)

    if type_ in TYPE_MAP:
        raise KeyError, 'Type %r already exists' % type_

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

    for (k, v) in TYPE_MAP.iteritems():
        if k == type_:
            return v

    raise KeyError, "Unknown type %r" % type_

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
    represent that error::

        class AuthenticationError(Exception):
            pass

    An example: C{add_error_class(AuthenticationError, 'Auth.Failed')}

    @type code: C{str}

    @raise TypeError: C{klass} must be a C{class} type.
    @raise TypeError: Error classes must subclass the C{__builtin__.Exception} class.
    @raise ValueError: Code is already registered.
    """
    if not isinstance(code, basestring):
        code = str(code)

    if not isinstance(klass, (type, types.ClassType)):
        raise TypeError, "klass must be a class type"

    mro = util.get_mro(klass)

    if not Exception in mro:
        raise TypeError, 'error classes must subclass the __builtin__.Exception class'

    if code in ERROR_CLASS_MAP.keys():
        raise ValueError, 'Code %s is already registered' % code

    ERROR_CLASS_MAP[code] = klass

def remove_error_class(klass):
    """
    Removes a class from C{ERROR_CLASS_MAP}.

    @raise ValueError: Code is not registered.
    @raise ValueError: Class is not registered.
    @raise TypeError: Invalid type, expected C{class} or C{string}.
    """
    if isinstance(klass, basestring):
        if not klass in ERROR_CLASS_MAP.keys():
            raise ValueError, 'Code %s is not registered' % klass
    elif isinstance(klass, (type, types.ClassType)):
        classes = ERROR_CLASS_MAP.values()
        if not klass in classes:
            raise ValueError, 'Class %s is not registered' % klass

        klass = ERROR_CLASS_MAP.keys()[classes.index(klass)]
    else:
        raise TypeError, "Invalid type, expected class or string"

    del ERROR_CLASS_MAP[klass]

register_adapters()
