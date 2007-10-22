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
# sources:
#   http://www.vanrijkom.org/archives/2005/06/amf_format.html
#   http://osflash.org/documentation/amf/astypes

"""AMF3 Implementation"""

class ASTypes:
    UNDEFINED       =           0x00
    NULL            =           0x01
    BOOL_FALSE      =           0x02
    BOOL_TRUE       =           0x03
    INTEGER         =           0x04
    NUMBER          =           0x05
    STRING          =           0x06
    # TODO: not defined on site, says it's only XML type,
    # so we'll assume it is for the time being..
    XML             =           0x07
    DATE            =           0x08
    ARRAY           =           0x09
    OBJECT          =           0x0a
    XMLSTRING       =           0x0b
    BYTEARRAY       =           0x0c
    # Unkown        =           0x0d   

class AMF3ObjectTypes:
    # Property list encoding.
    # The remaining integer-data represents the number of
    # class members that exist. The property names are read
    # as string-data. The values are then read as AMF3-data.
    PROPERTY = 0x00

    # Externalizable object.
    # What follows is the value of the "inner" object,
    # including type code. This value appears for objects
    # that implement IExternalizable, such as
    # ArrayCollection and ObjectProxy.
    EXTERNALIZABLE = 0x01
    
    # Name-value encoding.
    # The property names and values are encoded as string-data
    # followed by AMF3-data until there is an empty string
    # property name. If there is a class-def reference there
    # are no property names and the number of values is equal
    # to the number of properties in the class-def.
    VALUE = 0x02
    
    # Proxy object
    PROXY = 0x03

    # Flex class mappings.
    flex_mappings = [
        # (RemotingMessage, "flex.messaging.messages.RemotingMessage"),
        # (CommandMessage, "flex.messaging.messages.CommandMessage"),
        # (AcknowledgeMessage, "flex.messaging.messages.AcknowledgeMessage"),
        # (ErrorMessage, "flex.messaging.messages.ErrorMessage"),
        # (ArrayCollection, "flex.messaging.io.ArrayCollection"),
        # (ObjectProxy, "flex.messaging.io.ObjectProxy"),
    ]
    
class Parser(object):

    def __init__(self, data):
        self.obj_refs = list()
        self.str_refs = list()
        self.class_refs = list()
        if isinstance(data, BufferedByteStream):
            self.input = data
        else:
            self.input = BufferedByteStream(data)

    def readElement(self):
        type = self.input.read_uchar()
        if type == ASTypes.UNDEFINED:
            return None
        
        if type == ASTypes.NULL:
            return None
        
        if type == ASTypes.BOOL_FALSE:
            return False
        
        if type == ASTypes.BOOL_TRUE:
            return True
        
        if type == ASTypes.INTEGER:
            return self.readInteger()
        
        if type == ASTypes.NUMBER:
            return self.input.read_double()
        
        if type == ASTypes.STRING:
            return self.readString()
        
        if type == ASTypes.XML:
            return self.readXML()
        
        if type == ASTypes.DATE:
            return self.readDate()
        
        if type == ASTypes.ARRAY:
            return self.readArray()
        
        if type == ASTypes.OBJECT:
            return self.readObject()
        
        if type == ASTypes.XMLSTRING:
            return self.readString(use_references=False)
        
        if type == ASTypes.BYTEARRAY:
            raise self.readByteArray()
        
        else:
            raise ValueError("Unknown AMF3 datatype 0x%02x at %d" % (type, self.input.tell()-1))
    
    def readInteger(self):
        # see http://osflash.org/amf3/parsing_integers for AMF3 integer data format
        n = 0
        b = self.input.read_uchar()
        result = 0
        
        while b & 0x80 and n < 3:
            result <<= 7
            result |= b & 0x7f
            b = self.input.read_uchar()
            n += 1
        if n < 3:
            result <<= 7
            result |= b
        else:
            result <<= 8
            result |= b
        if result & 0x10000000:
            result |= 0xe0000000
            
        # return a converted integer value
        return result
    
    def readString(self, use_references=True):
        length = self.readInteger()
        if use_references and length & 0x01 == 0:
            return self.str_refs[length >> 1]
        
        length >>= 1
        buf = self.input.read(length)
        try:
            # Try decoding as regular utf8 first since that will
            # cover most cases and is more efficient.
            # XXX: I'm not sure if it's ok though.. will it always raise exception?
            result = unicode(buf, "utf8")
        except UnicodeDecodeError:
            result = util.decode_utf8_modified(buf)
        
        if use_references and len(result) != 0:
            self.str_refs.append(result)
        
        return result
    
    def readXML(self):
        data = self.readString(False)
        return ET.fromstring(data)
    
    def readDate(self):
        ref = self.readInteger()
        if ref & 0x01 == 0:
            return self.obj_refs[ref >> 1]
        ms = self.input.read_double()
        result = datetime.datetime.fromtimestamp(ms/1000.0)
        self.obj_refs.append(result)
        return result
    
    def readArray(self):
        size = self.readInteger()
        if size & 0x01 == 0:
            return self.obj_refs[size >> 1]
        size >>= 1
        key = self.readString()
        if key == "":
            # integer indexes only -> python list
            result = []
            self.obj_refs.append(result)
            for i in xrange(size):
                el = self.readElement()
                result.append(el)
        else:
            # key,value pairs -> python dict
            result = {}
            self.obj_refs.append(result)
            while key != "":
                el = self.readElement()
                result[key] = el
                key = self.readString()
            for i in xrange(size):
                el = self.readElement()
                result[i] = el
        
        return result
    
    def readObject(self):
        type = self.readInteger()
        if type & 0x01 == 0:
            return self.obj_refs[type >> 1]
        class_ref = (type >> 1) & 0x01 == 0
        type >>= 2
        if class_ref:
            class_ = self.class_refs[type]
        else:
            class_ = AMF3Class()
            class_.name = self.readString()
            class_.encoding = type & 0x03
            class_.attrs = []
       
        type >>= 2
        if class_.name:
            # TODO : do some class mapping?
            obj = AMF3Object(class_)
        else:
            obj = AMF3Object()
        
        self.obj_refs.append(obj)
        
        if class_.encoding & AMF3ObjectTypes.EXTERNALIZABLE:
            if not class_ref:
                self.class_refs.append(class_)
            # TODO: implement externalizeable interface here
            obj.__amf_externalized_data = self.readElement()
            
        else:
            if class_.encoding & AMF3ObjectTypes.VALUE:
                if not class_ref:
                    self.class_refs.append(class_)
                attr = self.readString()
                while attr != "":
                    class_.attrs.append(attr)
                    setattr(obj, attr, self.readElement())
                    attr = self.readString()
            else:
                if not class_ref:
                    for i in range(type):
                        class_.attrs.append(self.readString())
                    self.class_refs.append(class_)
                for attr in class_.attrs:
                    setattr(obj, attr, self.readElement())
        
        return obj

    def readByteArray(self):
        length = self.readInteger()
        return self.input.read(length >> 1)

class AMF3Class:
    
    def __init__(self, name=None, encoding=None, attrs=None):
        self.name = name
        self.encoding = encoding
        self.attrs = attrs
        
class AMF3Object:
    
    def __init__(self, class_=None):
        self.__amf_class = class_
    
    def __repr__(self):
        return "<AMF3Object [%s] at 0x%08X>" % (
            self.__amf_class and self.__amf_class.name or "no class",
            id(self))

class AbstractMessage:
    
    def __init__(self):
        # The body of the message.
        self.data = None
        # Unique client ID.
        self.clientId = None
        # Destination.
        self.destination = None
        # Message headers.
        self.headers = []
        # Unique message ID 
        self.messageId = None
        # timeToLive
        self.timeToLive = None
        # timestamp
        self.timestamp = None
    
    def __repr__(self):
        return "<AbstractMessage clientId=%s data=%r>" % (self.clientId, self.data)

class AcknowledgeMessage(AbstractMessage):
    
    def __init__(self):
        """
        This is the receipt for any message thats being sent.
        """
        AbstractMessage.__init__(self)
        # The ID of the message where this is a receipt of.
        self.correlationId = None
    
    def __repr__(self):
        return "<AcknowledgeMessage correlationId=%s>" % (self.correlationId)

class CommandMessage(AbstractMessage):
    
    def __init__(self):
        """
        This class is used for service commands, like pinging the server.
        """
        AbstractMessage.__init__(self)
        self.operation = None
        # The ID of the message where this is a receipt of.
        self.correlationId = None
        self.messageRefType = None
    
    def __repr__(self):
        return "<CommandMessage correlationId=%s operation=%r messageRefType=%d>" % (
            self.correlationId, self.operation, self.messageRefType)
        
class ErrorMessage(AbstractMessage):
    
    def __init__(self):
        """
        This is the receipt for Error Messages.
        """
        AbstractMessage.__init__(self)
        # Extended data that the remote destination has chosen to associate with 
        # this error to facilitate custom error processing on the client.
        self.extendedData = {}
        # The fault code for the error. 
        self.faultCode = None
        # Detailed description of what caused the error. 
        self.faultDetail = None
        # A simple description of the error. 
        self.faultString = None
        # Should a root cause exist for the error, this property contains those details.
        self.rootCause = {}
        
    def __repr__(self):
        return "<ErrorMessage faultCode=%s faultString=%r>" % (
            self.faultCode, self.faultString)
                
class RemotingMessage(AbstractMessage):
    
    def __init__(self):
        AbstractMessage.__init__(self)
        self.operation = None
        self.source = None
    
    def __repr__(self):
        return "<RemotingMessage operation=%s source=%r>" % (self.operation, self.source)

