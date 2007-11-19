# -*- encoding: utf8 -*-
#
# Copyright (c) 2007 The PyAMF Project. All rights reserved.
# 
# Arnar Birgisson
# Thijs Triemstra
# Nick Joyce
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
(U{AMF<http://osflash.org/documentation/amf>}) decoder and
encoder for Python that is compatible with the
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

#: Specifies that objects are serialized using AMF
#: for ActionScript 1.0 and 2.0.
AMF0 = 0
#: Specifies that objects are serialized using AMF
#: for ActionScript 3.0.
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
    Raised if an AMF data stream refers to a non-existant object or string
    reference.
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
    Raised if the AMF stream specifies a class that does not have an alias.

    @see: L{register_class} for more info.
    """

class BaseContext(object):
    """
    I am a hold the AMF context for en/decoding streams.
    """

    def __init__(self):
        """
        L{clear} context.
        """
        self.clear()

    def clear(self):
        """
        Resets the context.
        """
        self.objects = []

    def getObject(self, ref):
        """
        Gets an object based on a reference.

        @type ref: int
        @param ref: The reference to an object.

        @raise TypeError: Bad reference type.
        @raise ReferenceError: The object reference could not be found.

        @rtype: mixed
        @return: The object referenced.
        """
        if not isinstance(ref, (int, long)):
            raise TypeError, "Bad reference type"

        try:
            return self.objects[ref]
        except IndexError:
            raise ReferenceError, "Object reference %d not found" % ref

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
            return self.objects.index(obj) 
        except ValueError:
            raise ReferenceError("Reference for object %r not found" % str(obj))

    def addObject(self, obj):
        """
        Gets a reference to C{obj}, creating one if necessary.

        @type obj: mixed
        @param obj: The object to add to the context.

        @rtype: int
        @return: Reference to C{obj}.
        """
        try:
            return self.objects.index(obj) - 1
        except ValueError:
            self.objects.append(obj)

        return len(self.objects) - 1

    def __copy__(self):
        pass

class Bag(object):
    """
    I supply a C{__builtin__.dict} interface to support get/setattr calls.
    """

    def __init__(self, d={}):
        """
        @type d: dict
        @param d: Initial data for the bag.
        """
        for k, v in d.iteritems():
            setattr(self, k, v)

    def __getitem__(self, k):
        """
        @type k:
        @param k:
        @rtype:
        @return:
        """
        return getattr(self, k)

    def __setitem__(self, k, v):
        """
        @type k:
        @param k:
        @type v:
        @param v:
        @rtype:
        @return: 
        """
        return setattr(self, k, v)

    def __eq__(self, other):
        """
        @type other:
        @param other:
        @rtype: bool
        @return:
        """
        if isinstance(other, dict):
            return self.__dict__ == other
        if isinstance(other, Bag):
            return self.__dict__ == other.__dict__

        return False

    def iteritems(self):
        """
        """
        return self.__dict__.iteritems()

    def __repr__(self):
        return dict.__repr__(self.__dict__)

    def __delitem__(self, k):
        del self.__dict__[k]

class ClassMetaData(list):
    """
    I hold a list of tags relating to the class. The idea behind this is to
    emulate the metadata tags you can supply ActionScript, e.g. static/dynamic.
    
    At the moment, only static, dynamic and external are allowed but this may
    be extended in the future. 
    """
    _allowed_tags = (
        ('static', 'dynamic', 'external'),
        ('amf3',),
    )

    def __init__(self, *args):
        """
        @type args:
        @param args:
        """
        if len(args) == 1 and hasattr(args[0], '__iter__'):  
            for x in args[0]:
                self.append(x)
        else:
            for x in args:
                self.append(x)

    def _is_tag_allowed(self, x):
        """
        @param x:
        @type x:
        @rtype: tuple
        @return:
        """
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
            # check to see if a tag that is in the list is about to be clobbered
            # if so, raise a warning
            for y in tags:
                if y in self:
                    if x != y:
                        import warnings, traceback

                        warnings.warn(
                            "Previously defined tag %s superceded by %s" % (y, x))

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
    @type attrs: list
    @ivar metadata: A list of metadata tags similar to ActionScript tags.
    @type metadata: list
    """
    def __init__(self, klass, alias, read_func=None, write_func=None,
                 attrs=None, metadata=[]):
        """
        @type klass: class
        @param klass: The class to alias.
        @type alias: str
        @param alias: The alias to the class e.g. C{org.example.Person}.
        @type read_func: callable
        @param read_func: Function that gets called when reading the object from
                          the data stream.
        @type write_func: callable
        @param write_func: Function that gets called when writing the object to
                          the data steam.
                          
        @raise TypeError: The C{klass} must be a class type.
        @raise TypeError: The C{read_func} must be callable.
        @raise TypeError: The C{write_func} must be callable.
        """
        if not isinstance(klass, (type, types.ClassType)):
            raise TypeError("klass must be a class type")

        # XXX nick: If either read_func or write_func is defined, does the other
        # need to be defined as well?
        if read_func is not None and not callable(read_func):
            raise TypeError("read_func must be callable")

        if write_func is not None and not callable(write_func):
            raise TypeError("write_func must be callable")

        self.klass = klass
        self.alias = str(alias)
        self.read_func = read_func
        self.write_func = write_func
        self.attrs = attrs
        self.metadata = ClassMetaData(metadata)

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
        else:
            return False

def register_class(klass, alias, read_func=None, write_func=None,
    attrs=None, metadata=[]):
    """
    Registers a class to be used in the data streaming.
    
    @type alias: str
    @param alias: The alias of klass, i.e. C{org.example.Person}.
    @type read_func:
    @param read_func:
    @type write_func:
    @param write_func:
    @param attrs: A list of attributes that will be encoded for the class.
    @type attrs: C{list} or C{None}

    @raise TypeError: The C{klass} is not callable.
    @raise ValueError: The C{klass} is already registered.
    @raise ValueError: The C{alias} is already registered.

    @rtype:
    @return:
    """
    if not callable(klass):
        raise TypeError("klass must be callable")

    if klass in CLASS_CACHE:
        raise ValueError("klass %s already registered" % k)

    alias = str(alias)

    if alias in CLASS_CACHE.keys():
        raise ValueError("alias '%s' already registered" % alias)

    x = ClassAlias(klass, alias, read_func=read_func, write_func=write_func,
        attrs=attrs, metadata=metadata)
    CLASS_CACHE[alias] = x

    return x

def unregister_class(alias):
    """
    Deletes a class from the cache.

    If C{alias} is a class, the matching alias is found.

    @type alias: class or str
    @param alias: Alias for class to delete.
    """
    if isinstance(alias, (type, types.ClassType)):
        for s, a in CLASS_CACHE.iteritems():
            if a.klass == alias:
                alias = s

                break

    del CLASS_CACHE[alias]

def register_class_loader(loader):
    """
    Registers a loader that is called to provide the Class for a specific
    alias.

    The L{loader} is provided with one argument, the Class alias. If the
    loader succeeds in finding a suitable class then it should return that
    class, otherwise it should return L{None}.

    @type loader: callable
    @param loader:

    @raise TypeError: The C{loader} is not callable.
    @raise ValueError: The C{loader} is already registered.
    """
    if not callable(loader):
        raise TypeError("loader must be callable")

    if loader in CLASS_LOADERS:
        raise ValueError("loader has already been registered")

    CLASS_LOADERS.append(loader)

def get_module(mod_name):
    """
    Load a module based on C{mod_name}.

    @type mod_name: str
    @param mod_name: The module name.
    @rtype:
    @return:
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

    @type alias: str
    @param alias: The class name.
    @raise UnknownClassAlias: The C{alias} was not found.
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

        if callable(ret):
            # Cache the result
            CLASS_CACHE[str(alias)] = klass

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

    @type klass: object or class
    @param klass:
    @raise UnknownClassAlias: Class not found.

    @rtype: L{ClassAlias}
    @return: The class alias linked to the C{klass}.
    """
    if isinstance(klass, basestring):
        for a, k in CLASS_CACHE.iteritems():
            if klass == a:
                return k
    elif isinstance(klass, (types.InstanceType, types.ObjectType)):
        for a, k in CLASS_CACHE.iteritems():
            if klass.__class__ == k.klass:
                return k

    # All available methods for finding the alias have been exhausted
    raise UnknownClassAlias("Unknown alias for class %s" % klass)

def decode(stream, encoding=AMF0, context=None):
    """
    A generator function to decode a datastream.

    @type   stream: L{BufferedByteStream}
    @param  stream: AMF data.
    @type   encoding: int
    @param  encoding: AMF encoding type.
    @type   context: L{AMF0 Context<pyamf.amf0.Context>} or
    L{AMF3 Context<pyamf.amf3.Context>}
    @param  context: Context.
    @return: Each element in the stream.
    """
    decoder = _get_decoder(encoding)(stream, context)

    for el in decoder.readElement():
        yield el

def encode(element, encoding=AMF0, context=None):
    """
    A helper function to encode an element.

    @type   element: mixed
    @param  element: Python data.
    @type   encoding: int
    @param  encoding: AMF encoding type.
    @type   context: L{amf0.Context<pyamf.amf0.Context>} or
    L{amf3.Context<pyamf.amf3.Context>}
    @param  context: Context.
    
    @rtype:
    @return: File-like object.
    """
    stream = util.BufferedByteStream()
    encoder = _get_encoder(encoding)(stream, context)

    encoder.writeElement(element)

    return buf

def _get_decoder(encoding):
    """
    Get compatible decoder.

    @type encoding: int
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

def _get_encoder(encoding):
    """
    Get compatible encoder.

    @type encoding: int
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

def _get_context(encoding):
    """
    Gets a compatible context class.

    @type encoding: int
    @param encoding: AMF encoding version
    @raise ValueError: AMF encoding version is unknown.
    
    @rtype: L{amf0.Context<pyamf.amf0.Context>} or
    L{amf3.Context<pyamf.amf3.Context>}
    @return: AMF0 or AMF3 context.
    """
    if encoding == AMF0:
        import amf0

        return amf0.Context
    elif encoding == AMF3:
        import amf3

        return amf3.Context

    raise ValueError, "Unknown encoding %s" % encoding

def _adapt_context_amf0_to_amf3(amf3_context):
    """
    @type amf3_context: L{amf3.Context<pyamf.amf3.Context>}
    @param amf3_context: AMF3 context.
    @rtype: L{amf0.Context<pyamf.amf0.Context>}
    @return: AMF0 context.
    """
    import amf0

    context = amf0.Context()
    context.objects = amf3_context.objects

    return context

def _adapt_context_amf3_to_amf0(amf0_context):
    """
    @type amf0_context: L{amf0.Context<pyamf.amf0.Context>}
    @param amf0_context: AMF0 context.
    @rtype: L{amf3.Context<pyamf.amf3.Context>}
    @return: AMF3 context.
    """
    import amf3

    context = amf3.Context()
    context.objects = amf0_context.objects

    return context
