# -*- encoding: utf8 -*-
#
# Copyright (c) 2007 The PyAMF Project. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
B{PyAMF} is a B{A}ction B{M}essage B{F}ormat
(U{AMF<http://en.wikipedia.org/wiki/Action_Message_Format>}) decoder
and encoder for Python that is compatible with the
U{Flash Player<http://en.wikipedia.org/wiki/Flash_Player>} 6 and newer.

@author: U{Arnar Birgisson<mailto:arnarbi@gmail.com>}
@author: U{Thijs Triemstra<mailto:info@collab.nl>}
@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@copyright: Copyright (c) 2007 The PyAMF Project. All rights reserved.
@contact: U{dev@pyamf.org<mailto:dev@pyamf.org>}
@see: U{http://pyamf.org}

@since: October 2007
@status: Alpha
@version: 0.1.0
"""

import types

import pyamf
from pyamf import util

__all__ = [
    'register_class',
    'register_class_loader',
    'encode',
    'decode']

#: Class mapping support for Flex.
CLASS_CACHE = {}
#: Class loaders.
CLASS_LOADERS = []

#: Specifies that objects are serialized using AMF for ActionScript
#: 1.0 and 2.0.
AMF0 = 0
#: Specifies that objects are serialized using AMF for ActionScript 3.0.
AMF3 = 3
#: Specifies the default (latest) format for the current player.
AMF_DEFAULT = AMF3
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

#:
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
        self.objects = []
        self.rev_objects = {}

    def getObject(self, ref):
        """
        Gets an object based on a reference.

        @type ref: int
        @param ref: The reference to an object.

        @raise TypeError: Bad reference type.
        @raise ReferenceError: The object reference could not
        be found.

        @rtype: mixed
        @return: The object referenced.
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

        @type obj:
        @param obj:
        @raise ReferenceError: Object reference could not be found.

        @rtype:
        @return:
        """
        try:
            return self.rev_objects[id(obj)]
        except KeyError:
            raise ReferenceError

    def _getObjectIndex(self):
        return len(self.objects) - 1

    def addObject(self, obj):
        """
        Adds a reference to C{obj}.

        @type obj: mixed
        @param obj: The object to add to the context.

        @rtype: int
        @return: Reference to C{obj}.
        """
        self.objects.append(obj)
        idx = self._getObjectIndex()
        self.rev_objects[id(obj)] = idx

        return idx

    def __copy__(self):
        raise NotImplementedError

class Bag(object):
    """
    I supply a C{__builtin__.dict} interface to support get/setattr calls.
    """

    def __init__(self, d={}):
        """
        @type d: C{dict}
        @param d: Initial data for the bag.
        """
        for k, v in d.iteritems():
            setattr(self, k, v)

    def __getitem__(self, k):
        return getattr(self, k)

    def __setitem__(self, k, v):
        return setattr(self, k, v)

    def __eq__(self, other):
        if isinstance(other, dict):
            return self.__dict__ == other
        if isinstance(other, Bag):
            return self.__dict__ == other.__dict__

        return False

    def iteritems(self):
        return self.__dict__.iteritems()

    def __repr__(self):
        return dict.__repr__(self.__dict__)

    def __delitem__(self, k):
        del self.__dict__[k]

class ClassMetaData(list):
    """
    I hold a list of tags relating to the class. The idea behind this is
    to emulate the metadata tags you can supply to ActionScript,
    e.g. static/dynamic.

    At the moment, only C{static}, C{dynamic} and C{external} are allowed
    but this may be extended in the future.
    """
    _allowed_tags = (
        ('static', 'dynamic', 'external'),
        ('amf3',),
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

        @param x:
        @type x:

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
    def __init__(self, klass, alias, read_func=None, write_func=None,
                 attrs=None, metadata=[]):
        """
        @type klass: C{class}
        @param klass: The class to alias.
        @type alias: C{str}
        @param alias: The alias to the class e.g. C{org.example.Person}. If the
            value of this is C{None}, then it is worked out based on the C{klass}.
            The anonymous tag is also added to the class.
        @type read_func: callable
        @param read_func: Function that gets called when reading the object
            from the data stream.
        @type write_func: callable
        @param write_func: Function that gets called when writing the object to
                          the data steam.
        @type attrs:
        @param attrs:
        @type metadata:
        @param metadata:

        @raise TypeError: The C{klass} must be a class type.
        @raise TypeError: The C{read_func} must be callable.
        @raise TypeError: The C{write_func} must be callable.
        """
        if not isinstance(klass, (type, types.ClassType)):
            raise TypeError("klass must be a class type")

        # XXX nick: If either read_func or write_func is defined, does the
        # other need to be defined as well?
        if read_func is not None and not callable(read_func):
            raise TypeError("read_func must be callable")

        if write_func is not None and not callable(write_func):
            raise TypeError("write_func must be callable")

        self.metadata = ClassMetaData(metadata)

        if alias is None:
            self.metadata.append('anonymous')
            alias = "%s.%s" % (klass.__module__, klass.__name__,)

        self.klass = klass
        self.alias = alias
        self.read_func = read_func
        self.write_func = write_func
        self.attrs = attrs

        # if both funcs are defined, we add the metadata
        if read_func and write_func:
            self.metadata.append('external')

    def __call__(self, *args, **kwargs):
        """
        Creates an instance of the klass.

        @rtype:
        @return: Instance of C{self.klass}.
        """
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

class BaseDecoder(object):
    """
    Base AMF decoder.

    @ivar context_class: The context for the decoding.
    @type context_class: An instance of C{BaseDecoder.context_class}
    @ivar type_map:
    @type type_map: C{list}
    @ivar stream: The underlying data stream.
    @type stream: L{BufferedByteStream<util.BufferedByteStream>}
    """
    context_class = BaseContext
    type_map = {}

    def __init__(self, data=None, context=None):
        """
        @type   data: L{BufferedByteStream<util.BufferedByteStream>}
        @param  data: Data stream.
        @type   context: L{Context<pyamf.amf0.Context>}
        @param  context: Context.
        @raise TypeError: The C{context} parameter must be of
        type L{Context<amf0.Context>}.
        """
        # coersce data to BufferedByteStream
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
        raise NotImplementedError

    def readElement(self):
        """
        Reads an AMF3 element from the data stream.

        @raise DecodeError: The ActionScript type is unknown
        @raise EOFError: No more data left to decode
        """
        type = self.readType()

        try:
            func = getattr(self, self.type_map[type])
        except KeyError, e:
            raise pyamf.DecodeError(
                "Unsupported ActionScript type 0x%02x" % type)

        return func()

    def __iter__(self):
        try:
            while 1:
                yield self.readElement()
        except EOFError:
            raise StopIteration

class BaseEncoder(object):
    """
    Base AMF encoder.
    
    @ivar type_map: A list of types -> functions. The types is a list of
        possible instances or functions to call (that return a C{bool}) to
        determine the correct function to call to encode the data.
    @type type_map: C{list}
    @ivar context_class: Holds the class that will create context objects for
        the implementing Encoder.
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
        # coersce data to BufferedByteStream
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

    def _writeElementFunc(self, data):
        """
        Gets a function used to encode the data.

        @type   data: C{mixed}
        @param  data: Python data.
        @rtype: callable or C{None}
        @return: The function used to encode data to the stream.
        """
        func = None
        td = type(data)

        for tlist, method in self.type_map:
            for t in tlist:
                try:
                    if isinstance(data, t):
                        return getattr(self, method)
                except TypeError:
                    if callable(t) and t(data):
                        return getattr(self, method)

        return None

    def writeElement(self, data):
        """
        Writes the data.

        @type   data: C{mixed}
        @param  data: The data to be encoded to the data stream.
        """
        raise NotImplementedError

def register_class(klass, alias=None, read_func=None, write_func=None,
    attrs=None, metadata=[]):
    """
    Registers a class to be used in the data streaming.

    @type alias: C{str}
    @param alias: The alias of klass, i.e. C{org.example.Person}.
    @type read_func:
    @param read_func:
    @type write_func:
    @param write_func:
    @param attrs: A list of attributes that will be encoded for the class.
    @type attrs: C{list} or C{None}
    @type metadata:
    @param metadata:

    @raise TypeError: The C{klass} is not callable.
    @raise ValueError: The C{klass} is already registered.
    @raise ValueError: The C{alias} is already registered.

    @rtype:
    @return:
    """
    if not callable(klass):
        raise TypeError, "klass must be callable"

    if klass in CLASS_CACHE:
        raise ValueError, "klass %s already registered" % klass

    if alias is not None and alias in CLASS_CACHE.keys():
        raise ValueError, "alias '%s' already registered" % alias

    x = ClassAlias(klass, alias, read_func=read_func, write_func=write_func,
        attrs=attrs, metadata=metadata)

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
    class, otherwise it should return L{None}.

    @type loader: callable
    @param loader:

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

    @type loader: callable
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
    @rtype:
    @return: Module
    """
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
    @return:
    @rtype:
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
    raise UnknownClassAlias("Unknown alias %s" % alias)

def get_class_alias(klass):
    """
    Finds the alias registered to the class.

    @type klass: C{object} or class
    @raise UnknownClassAlias: Class not found.
    @raise TypeError: Expecting string or class type.

    @rtype: L{ClassAlias}
    @return: The class alias linked to the C{klass}.
    """
    if not isinstance(klass, (type, types.ClassType, basestring)):
        if isinstance(klass, types.ObjectType):
            klass = type(klass)

    if not isinstance(klass, (type, types.ClassType, basestring)):
        raise TypeError, "Expecting string or class type"

    if isinstance(klass, basestring):
        for a, k in CLASS_CACHE.iteritems():
            if klass == a:
                return k
    else:
        for a, k in CLASS_CACHE.iteritems():
            if klass == k.klass:
                return k

    return load_class(klass)

def decode(stream, encoding=AMF0, context=None):
    """
    A generator function to decode a datastream.

    @type   stream: L{BufferedByteStream<util.BufferedByteStream>}
    @param  stream: AMF data.
    @type   encoding: C{int}
    @param  encoding: AMF encoding type.
    @type   context: L{AMF0 Context<pyamf.amf0.Context>} or
    L{AMF3 Context<pyamf.amf3.Context>}
    @param  context: Context.
    @return: Each element in the stream.
    """
    decoder = _get_decoder_class(encoding)(stream, context)

    for el in decoder.readElement():
        yield el

def encode(element, encoding=AMF0, context=None):
    """
    A helper function to encode an element.

    @type   element: C{mixed}
    @param  element: Python data.
    @type   encoding: C{int}
    @param  encoding: AMF encoding type.
    @type   context: L{amf0.Context<pyamf.amf0.Context>} or
    L{amf3.Context<pyamf.amf3.Context>}
    @param  context: Context.

    @rtype: C{StringIO}
    @return: File-like object.
    """
    stream = util.BufferedByteStream()
    encoder = _get_encoder_class(encoding)(stream, context)

    encoder.writeElement(element)

    return stream

def get_decoder(encoding):
    return _get_decoder_class(encoding)()

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
        import amf0

        return amf0.Decoder
    elif encoding == AMF3:
        import amf3

        return amf3.Decoder

    raise ValueError, "Unknown encoding %s" % encoding

def get_encoder(encoding):
    return _get_encoder_class(encoding)()

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
        import amf0

        return amf0.Encoder
    elif encoding == AMF3:
        import amf3

        return amf3.Encoder

    raise ValueError, "Unknown encoding %s" % encoding

def get_context(encoding):
    return _get_context_class(encoding)()

def _get_context_class(encoding):
    """
    Gets a compatible context class.

    @type encoding: C{int}
    @param encoding: AMF encoding version
    @raise ValueError: AMF encoding version is unknown.

    @rtype: L{amf0.Context<pyamf.amf0.Context>} or
    L{amf3.Context<pyamf.amf3.Context>}
    @return: AMF0 or AMF3 context class.
    """
    if encoding == AMF0:
        import amf0

        return amf0.Context
    elif encoding == AMF3:
        import amf3

        return amf3.Context

    raise ValueError, "Unknown encoding %s" % encoding
