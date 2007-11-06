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
#

"""
PyAMF is a B{A}ction B{M}essage B{F}ormat (AMF) decoder and encoder
for Python that is compatible with the
U{Flash Player<http://en.wikipedia.org/wiki/Flash_Player>} 6 and newer.
"""

from pyamf import util

__all__ = [
    'register_class',
    'register_class_loader',
    'encode',
    'decode']

#: Class mapping support for Flex.
CLASS_CACHE = {}
CLASS_LOADERS = []

#: Specifies that objects are serialized using AMF
#: for ActionScript 1.0 and 2.0.
AMF0 = 0
#: Specifies that objects are serialized using AMF
#: for ActionScript 3.0.
AMF3 = 3
#:Specifies the default (latest) format for the current player.
AMF_DEFAULT = AMF3
#: Supported AMF encoding types.
ENCODING_TYPES = (AMF0, AMF3)

class ClientTypes:
    """
    Typecodes used to identify AMF clients and servers.
    """
    #: Specifies a Flash Player 6.0 - 8.0 client.
    Flash    = 0
    #: Specifies a FlashCom / Flash Media Server client.
    FlashCom = 1
    #: Specifies a Flash Player 9.0 client.
    Flash9   = 3

CLIENT_TYPES = set(
    ClientTypes.__dict__[x] for x in ClientTypes.__dict__
    if not x.startswith('_'))  

class BaseError(Exception):
    """
    Base AMF Error.

    All AMF related errors should be subclassed from this.
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
    Raised if the element could not be encoded to the stream. This is mainly
    used to pick up the empty key string array bug.
    
    See U{http://www.docuverse.com/blog/donpark/2007/05/14/flash-9-amf3-bug} for
    more info
    """

class UnknownClassAlias(BaseError):
    """
    Raised if the AMF stream specifies a class that does not have an alias.
    See Lregister_class} for more info.
    """

class Context(object):
    """
    I hold the AMF context for en/decoding streams.
    """

    def __init__(self):
        self.clear()

    def clear(self):
        """
        Resets the context.
        """
        self.objects = []
        self.strings = []
        self.classes = []

    def getObject(self, ref):
        """
        Gets an object based on a reference.

        Raises L{pyamf.ReferenceError} if the object could not be found.
        """
        try:
            return self.objects[ref - 1]
        except IndexError:
            raise ReferenceError("Object reference %d not found" % ref)

    def getObjectReference(self, obj):
        try:
            return self.objects.index(obj) + 1
        except ValueError:
            raise ReferenceError("Reference for object %r not found" % str(obj))

    def addObject(self, obj):
        """
        Gets a reference to obj, creating one if necessary.
        """
        try:
            return self.objects.index(obj)
        except ValueError:
            self.objects.append(obj)

            return len(self.objects)

    def getString(self, ref):
        """
        Gets a string based on a reference ref

        Raises L{pyamf.ReferenceError} if the string could not be found.
        """
        try:
            return self.strings[ref]
        except IndexError:
            raise ReferenceError("String reference %d not found" % ref)

    def getStringReference(self, s):
        """
        Return string reference.
        """
        try:
            return self.strings.index(s)
        except ValueError:
            raise ReferenceError("Reference for string %r not found" % s)

    def addString(self, s):
        """
        Creates a reference to s.

        @type s: string
        @param s: Reference
        """
        try:
            return self.strings.index(s)
        except ValueError:
            self.strings.append(s)

            return len(self.strings)

    def getClassDefinition(self, ref):
        """
        @type ref:
        @param ref:
        """
        try:
            return self.classes[ref]
        except IndexError:
            raise ReferenceError("Class reference %d not found" % ref)

    def getClassDefinitionReference(self, class_def):
        """
        @type class_def:
        @param class_def:
        """
        try:
            return self.classes.index(class_def)
        except ValueError:
            raise ReferenceError("Reference for class %r not found" % 
                class_def)

    def addClassDefinition(self, class_def):
        """
        Creates a reference to class_def.
        """
        try:
            return self.classes.index(class_def)
        except ValueError:
            self.classes.append(class_def)

            return len(self.classes)

    def getClass(self, class_def):
        if not class_def.name:
            return Bag

        return load_class(class_def.name)

class Bag(object):
    """
    I supply a thin layer over the __builtin__.dict type to support
    get/setattr calls.
    """

    def __init__(self, d={}):
        for k, v in d.items():
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

def register_class(klass, alias):
    """
    Registers a class to be used in the data streaming.

    @type alias: str
    @param alias: 
    """
    if not callable(klass):
        raise TypeError("klass must be callable")

    if klass in CLASS_CACHE:
        raise ValueError("klass %s already registered" % k)

    alias = str(alias)

    if alias in CLASS_CACHE.keys():
        raise ValueError("alias '%s' already registered" % alias)

    CLASS_CACHE[alias] = klass

def register_class_loader(loader):
    """
    Registers a loader that is called to provide the Class for a specific
    alias. L{loader} is provided with one argument, the Class alias. If the loader
    succeeds in finding a suitable class then it should return that class,
    otherwise it should return L{None}.

    @type loader: callable
    @param loader: 
    """
    if not callable(loader):
        raise TypeError("loader must be callable")

    if loader in CLASS_LOADERS:
        raise ValueError("loader has already been registered")

    CLASS_LOADERS.append(loader)

def get_module(mod_name):
    """
    Load a module based on mod_name.

    @type mod_name: string
    @param mod_name: module name
    """
    mod = __import__(mod_name)
    components = mod_name.split('.')
    
    for comp in components[1:]:
        mod = getattr(mod, comp)

    return mod

def load_class(alias):
    """
    Finds the class registered to the alias. Raises L{LookupError} if not found.

    The search is done in order:
      1. Checks if the class name has been registered via L{register_class}.
      2. Checks all functions registered via L{register_class_loader}.
      3. Attempts to load the class via standard module loading techniques.

    @type alias: string
    @param alias: class name
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

def get_class_alias(obj):
    """
    Finds the alias registered to the class. Raises L{LookupError} if not found.
    
    See L{load_class} for more info.

    @type obj:
    @param obj:
    """
    klass = type(obj)

    # Try the CLASS_CACHE first
    for a, k in CLASS_CACHE.iteritems():
        if klass == k:
            return a

    # All available methods for finding the alias have been exhausted
    raise UnknownClassAlias("Unknown alias for class %s" % klass)

# Register some basic classes
#register_class(Bag, 'flex.messaging.io.ArrayCollection')
#register_class(Bag, 'flex.messaging.io.ObjectProxy')

def decode(stream, encoding=AMF0, context=None):
    """
    A generator function to decode a datastream.
    
    Returns each element in the stream.

    @type   stream: L{BufferedByteStream}
    @param  stream: AMF data
    @type   encoding: int
    @param  encoding: AMF encoding type
    @type   context: L{Context}
    @param  context: Context
    """
    decoder = _get_decoder(encoding)(stream, context)

    for el in decoder.readElement():
        yield el

def encode(element, encoding=AMF0, context=None):
    """
    A helper function to encode an element.

    Returns a file-like object.

    @type   element: 
    @param  element: Python data
    @type   encoding: int
    @param  encoding: AMF encoding type
    @type   context: L{Context}
    @param  context: Context
    """
    stream = util.BufferedByteStream()
    encoder = _get_encoder(encoding)(stream, context)

    encoder.writeElement(element)

    return buf

def _get_decoder(encoding):
    import pyamf

    if encoding == pyamf.AMF0:
        import pyamf.amf0

        return pyamf.amf0.Decoder
    elif encoding == pyamf.AMF3:
        import pyamf.amf3

        return pyamf.amf3.Decoder

    raise ValueError("Unknown encoding")

def _get_encoder(encoding):
    import pyamf

    if encoding == pyamf.AMF0:
        import pyamf.amf0

        return pyamf.amf0.Encoder
    elif encoding == pyamf.AMF3:
        import pyamf.amf3

        return pyamf.amf3.Encoder
        
    raise ValueError("Unknown encoding")
