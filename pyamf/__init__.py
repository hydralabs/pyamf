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
I am a Action Message Format (AMF) decoder and encoder.
"""

from pyamf import util, amf0, amf3

CLASS_CACHE = {}
CLASS_LOADERS = []

class GeneralTypes:
    """
    PyAMF global constants.
    """
    #: Specifies a Flash Player 6.0 - 8.0 client.
    AC_Flash           = 0
    #: Specifies a FlashCom / Flash Media Server client.
    AC_FlashCom        = 1
    #: Specifies a Flash Player 9.0 client.
    AC_Flash9          = 3
    #: Normal result to a methodcall.
    REMOTING_RESULT    = 1
    #: Faulty result.
    REMOTING_STATUS    = 2
    #: Result to a debug-header.
    REMOTING_DEBUG     = 3
    #: AMF0 Encoding
    AMF0               = 0
    #: AMF3 Encoding
    AMF3               = 3
    #: AMF mimetype
    AMF_MIMETYPE       = 'application/x-amf'

class BaseError(Exception):
    """
    Base AMF Error. All AMF related errors should be subclassed from this.
    """

class ParseError(BaseError):
    """
    Raised if there is an error in parsing an AMF data stream.
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
    
    See http://www.docuverse.com/blog/donpark/2007/05/14/flash-9-amf3-bug for
    more info
    """

class Context(object):
    """

    """
    objects = []
    strings = []
    classes = []

    def clear(self):
        """
        Resets the context
        """
        self.objects = []
        self.strings = []
        self.classes = []

    def getObject(self, ref):
        """
        Gets an object based on a reference ref

        Raises L{pyamf.ReferenceError} if the object could not be found
        """
        try:
            return self.objects[ref]
        except IndexError:
            raise ReferenceError("Object reference %d not found" % ref)

    def getObjectReference(self, obj):
        try:
            return self.objects.index(obj)
        except ValueError:
            raise ReferenceError("Reference for object %r not found" % obj)

    def addObject(self, obj):
        """
        Gets a reference to obj, creating one if necessary
        """
        try:
            return self.objects.index(obj)
        except ValueError:
            self.objects.append(obj)

            return len(self.objects)

    def getString(self, ref):
        """
        Gets a string based on a reference ref

        Raises L{pyamf.ReferenceError} if the string could not be found
        """
        try:
            return self.strings[ref]
        except IndexError:
            raise ReferenceError("String reference %d not found" % ref)

    def getStringReference(self, s):
        try:
            return self.strings.index(s)
        except ValueError:
            raise ReferenceError("Reference for string %r not found" % s)

    def addString(self, s):
        """
        Creates a reference to s
        """
        try:
            return self.strings.index(s)
        except ValueError:
            self.strings.append(s)

            return len(self.strings)

    def getClassDefinition(self, ref):
        try:
            return self.classes[ref]
        except IndexError:
            raise ReferenceError("Class reference %d not found" % ref)

    def getClassDefinitionReference(self, class_def):
        try:
            return self.classes.index(class_def)
        except ValueError:
            raise ReferenceError("Reference for class %r not found" % 
                class_def)

    def addClassDefinition(self, class_def):
        """
        Creates a reference to class_def
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

class Bag(dict):
    """
    I supply a thin layer over the __builtin__.dict type to support
    get/setattr calls.
    """

    def __init__(self, d={}):
        for k, v in d.items():
            self[k] = v

    def __setattr__(self, name, value):
        self[name] = value

    def __getattr__(self, name):
        return self[name]

def register_class(klass, alias):
    """
    Registers a class to be used in the data streaming. 
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
    alias. loader is provided with one argument, the class alias. If the loader
    succeeds in finding a suitable class then it should return that class,
    otherwise it should return None.
    """
    if not callable(loader):
        raise TypeError("loader must be callable")

    if loader in CLASS_LOADERS:
        raise ValueError("loader has already been registered")

    CLASS_LOADERS.append(loader)

def get_module(mod_name):
    """
    Load a module based on mod_name
    """
    mod = __import__(mod_name)
    components = mod_name.split('.')
    
    for comp in components[1:]:
        mod = getattr(mod, comp)

    return mod

def load_class(alias):
    """
    Finds the class registered to the alias. Raises LookupError if not found.

    The search is done in order:
      1. Checks if the class name has been registered via pyamf.register_class
      2. Checks all functions registered via register_class_loader
      3. Attempts to load the class via standard module loading techniques
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
    raise LookupError("Unknown alias %s" % alias)

def get_class_alias(obj):
    """
    Finds the alias registered to the class. Raises LookupError if not found.
    
    See L{load_class} for more info
    """
    klass = obj.__class__

    # Try the CLASS_CACHE first
    for a, k in CLASS_CACHE.iteritems():
        if klass == k:
            return a

    # All available methods for finding the alias have been exhausted
    raise LookupError("Unknown alias for class %s" % klass)

# Register some basic classes
register_class(Bag, 'flex.messaging.io.ArrayCollection')
register_class(Bag, 'flex.messaging.io.ObjectProxy')

class AMFMessageDecoder:
    """
    Decodes AMF data into Python data.
    """
    
    def __init__(self, data):
        self.input = util.BufferedByteStream(data)
        self.msg = AMFMessage()
        
    def decode(self):
        """
        Start decoding.
        """
        # The first byte of the AMF file/stream is the AMF type.
        self.msg.amfVersion = self.input.read_uchar()
        if self.msg.amfVersion == GeneralTypes.AMF0:
            parser_class = amf0.Parser
        elif self.msg.amfVersion == GeneralTypes.AMF3:
            parser_class = amf3.Parser
        else:
            raise Exception("Invalid AMF version: " + str(self.msg.amfVersion))
        # The second byte is the client type.
        self.msg.clientType = self.input.read_uchar()
        # The third and fourth bytes form an integer value that specifies
        # the number of headers.
        header_count = self.input.read_short()
        # Headers are used to request debugging information, send 
        # authentication info, tag transactions, etc.
        for i in range(header_count):
            header = AMFMessageHeader()
            # UTF string (including length bytes) - header name.
            name_len = self.input.read_ushort()
            header.name = self.input.read_utf8_string(name_len)
            # Specifies if understanding the header is "required".
            header.required = bool(self.input.read_uchar())
            # Long - Length in bytes of header.
            header.length = self.input.read_ulong()
            # Variable - Actual self.input (including a type code).
            header.data = parser_class(self.input).readElement()
            self.msg.headers.append(header)
        # Between the headers and the start of the bodies is a int 
        # specifying the number of bodies.
        bodies_count = self.input.read_short()
        # A single AMF envelope can contain several requests/bodies; 
        # AMF supports batching out of the box.
        for i in range(bodies_count):
            body = AMFMessageBody()
            # The target may be one of the following:
            # - An http or https URL. In that case the gateway should respond 
            #   by sending a SOAP request to that URL with the specified data. 
            #   In that case the data will be an Array and the first key 
            #   (data[0]) contains the parameters to be sent.
            # - A string with at least one period (.). The value to the right 
            #   of the right-most period is the method to be called. The value 
            #   to the left of that is the service to be invoked including package 
            #   name. In that case data will be an Array of arguments to be sent 
            #   to the method.
            target_len = self.input.read_ushort()
            body.target = self.input.read_utf8_string(target_len)
            # The response is a string that gives the body an id so it can be 
            # tracked by the client.
            response_len = self.input.read_ushort()
            body.response = self.input.read_utf8_string(response_len)
            # Body length in bytes.            from pyamf import amf0

            body.length = self.input.read_ulong()
            # Actual data (including a type code).
            body.data = parser_class(self.input).readElement()
            # Bodies contain actual Remoting requests and responses.
            self.msg.bodies.append(body)

        return self.msg

class AMFMessageEncoder:
    """
    Encodes Python data into AMF data.
    """
    
    def __init__(self, msg):
        self.output = util.BufferedByteStream()
        self.msg = msg
        
    def encode(self):
        """
        Start encoding.
        """
        encoder_class = amf0.Encoder
        # Write AMF version.
        self.output.write_uchar(self.msg.amfVersion)
        # Client type.
        self.output.write_uchar(self.msg.clientType)
        # Header length.
        header_count = len(self.msg.headers)
        self.output.write_short(header_count)
        # Write headers.
        for header in self.msg.headers:
            # Write header name.
            self.output.write_utf8_string(header.name)
            # Write header requirement.
            self.output.write_uchar(header.required)
            # Write length in bytes of header.
            self.output.write_ulong(-1)
            # Header data.
            encoder_class(self.output).writeElement(header.data)
        # Write bodies length.
        bodies_count = len(self.msg.bodies)
        self.output.write_short(bodies_count)
        # Write bodies.
        for body in self.msg.bodies:
            # Target (/1/onResult).
            self.output.write_utf8_string(body.target)
            # Response (null).
            self.output.write_utf8_string(body.response)
            # Body length in bytes.
            self.output.write_ulong(-1)
            # Actual Python result data.
            encoder_class(self.output).writeElement(body.data)
        
        return self.output
    
class AMFMessage:
    
    def __init__(self):
        self.amfVersion = GeneralTypes.AMF0
        self.clientType = GeneralTypes.AC_Flash
        self.headers = []
        self.bodies = []
    
    def __repr__(self):
        r = "<AMFMessage amfVersion=" + str(self.amfVersion) + " clientType=" + str(self.clientType) + "\n"
        for h in self.headers:
            r += "   " + repr(h) + "\n"
        for b in self.bodies:
            r += "   " + repr(b) + "\n"
        r += ">"
        return r

class AMFMessageHeader:
    
    def __init__(self):
        self.name = None
        self.required = None
        self.length = None
        self.data = None
    
    def __repr__(self):
        return "<AMFMessageHeader name=%s data=%r>" % (self.name, self.data)

class AMFMessageBody:
    
    def __init__(self):
        self.target = None
        self.response = None
        self.length = None
        self.data = None

    def __repr__(self):
        return "<AMFMessageBody target=%s data=%r>" % (self.target, self.data)

class Server:
    def __init__(self, data):
        if data:
            self.request = AMFMessageDecoder(data).decode()
            self.response = AMFMessage()
        else:
            raise Exception("Invalid AMF request received")
    
    def __repr__(self):
        return "<Server request=%s response=%d>" % (self.request, self.response)
    
    def setResponse(self, target, type, data):
        """
        Set a response based on a request you received through getRequests.
        """
        if type == GeneralTypes.REMOTING_RESULT:
            target += '/onResult'

        elif type == GeneralTypes.REMOTING_STATUS:
            target += '/onStatus'

        elif type == GeneralTypes.REMOTING_DEBUG:
            target += '/onDebugEvents'
        
        body = AMFMessageBody()
        body.target = target
        body.response = ''
        body.data = data

        return self.response.bodies.append(body)

    def getResponse(self):
        """
        Get all responses for the client. Call this after you answered all
        the requests with setResponse.
        """
        self.response.clientType = self.request.clientType
        data = AMFMessageEncoder(self.response).encode()
        return data

    def addHeader(self, name, required, data):
            """
            Add a header to the server response.
            """
            self.response.addHeader(name, required, data)

    def getRequests(self):
        """
        Returns the requests that are made to the gateway.
        """
        return self.request.bodies
    
    def getHeaders(self):
        """
        Returns the request headers.
        """
        return self.request.headers

class Client:
    def __init__(self):
        self.request = AMFMessage()
        self.response = AMFMessage()
    
    def __repr__(self):
        return "<Client endpoint=%s>" % (self.endpoint)
    
    def setRequest(self, servicePath, data):
        """
        setRequest creates the encoded AMF request for the server. It expects  
        the servicepath and methodname, and the parameters of the methodcall.
        """
        body = AMFMessageBody()
        body.target = servicePath
        body.response = '/1'
        body.data = data
        self.request.bodies.append(body)
        data = AMFMessageEncoder(self.request).encode()
        return data.getvalue()
    
    def getResponse(self, data):
        self.response = AMFMessageDecoder(data).decode()
        return self.response.bodies
