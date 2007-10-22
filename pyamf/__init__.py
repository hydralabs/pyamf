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
#
# AMF parser
# Resources:
#   http://www.vanrijkom.org/archives/2005/06/amf_format.html
#   http://osflash.org/documentation/amf/astypes

import datetime
from types import *

try:
    import xml.etree.ElementTree as ET
except ImportError:
    try:
        import cElementTree as ET
    except ImportError:
        import elementtree.ElementTree as ET

from pyamf import util, amf0, amf3
from pyamf.util import BufferedByteStream

class GeneralTypes:
    """
    PyAMF global constants
    """
    # Specifies aFlash Player 6.0 - 8.0 client.
    AC_Flash           = 0
    # Specifies a FlashCom / Flash Media Server client.
    AC_FlashCom        = 1
    # Specifies a Flash Player 9.0 client.
    AC_Flash9          = 3
    # Normal result to a methodcall.
    REMOTING_RESULT    = 1
    # Faulty result.
    REMOTING_STATUS    = 2
    # Result to a debug-header.
    REMOTING_DEBUG     = 3
    # AMF0 Encoding
    AMF0               = 0
    # AMF3 Encoding
    AMF3               = 3
    # AMF mimetype
    AMF_MIMETYPE       = 'application/x-amf'
    
class AMFMessageDecoder:
    
    def __init__(self, data):
        self.input = BufferedByteStream(data)
        self.msg = AMFMessage()
        
    def decode(self):
        # The first byte of the AMF file/stream is the AMF type.
        self.msg.amfVersion = self.input.read_uchar()
        if self.msg.amfVersion == GeneralTypes.AMF0:
            # AMF0
            decoder_class = amf0.Decoder
        elif self.msg.amfVersion == GeneralTypes.AMF3:
            # AMF3
            decoder_class = amf3.Decoder
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
            header.data = decoder_class(self.input).readElement()
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
            # Body length in bytes.
            body.length = self.input.read_ulong()
            # Actual data (including a type code).
            body.data = decoder_class(self.input).readElement()
            # Bodies contain actual Remoting requests and responses.
            self.msg.bodies.append(body)

        return self.msg

class AMFMessageEncoder:

    def __init__(self, msg):
        self.output = BufferedByteStream()
        self.msg = msg
        
    def encode(self):
        #
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
        
if __name__ == "__main__":
    import sys, glob
    debug = False
    print "\nStarting AMF parser...\n"
    for arg in sys.argv[1:]:
        if arg == 'debug':
            debug = True
        for fname in glob.glob(arg):
            f = file(fname, "r")
            data = f.read()
            size = str(f.tell())
            f.close()
            p = AMFMessageDecoder(data)
            if debug:
                print "=" * 120
            print " Parsing file:", fname.rsplit("\\",1)[-1], 
            try:
                obj = p.decode()
            except:
                raise
                print "   ---> FAILED"
            else:
                print "   ---> OK"
                if debug:
                    print repr(obj)

