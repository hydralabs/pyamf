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
Flex Messaging Implementation
"""

import pyamf

class AbstractMessage(object):
    """
    Base class for all Flex compatibility messages.
    """
    data = None
    #: Unique client ID 
    clientId = None
    #: Message destination
    destination = None
    #: Message headers
    headers = []
    #: Unique message ID
    messageId = None
    timeToLive = None
    timestamp = None
    
    def __repr__(self):
        m = '<%s ' % self.__class__.__name__

        for k, v in self.__dict__.iteritems():
            m += ' %s=%s' % (k, v)

        return m + " />"

class AsyncMessage(AbstractMessage):
    """
    Base class for for asynchronous Flex compatibility messages.
    """
    correlationId = None

class AcknowledgeMessage(AsyncMessage):
    """
    Flex compatibility message that is returned to the client.

    This is the receipt for any message thats being sent.
    """
    pass

class CommandMessage(AsyncMessage):
    """
    Command message as sent by the C{<mx:RemoteObject>} MXML tag.

    This class is used for service commands, like pinging the server

    Reference: U{http://livedocs.adobe.com/flex/2/langref/mx/rpc/remoting/mxml/RemoteObject.html}
    """
    operation = None
    messageRefType = None

class ErrorMessage(AbstractMessage):
    """
    Flex error message to be returned to the client.
    """
    #: Extended data that the remote destination has chosen to associate with 
    #: this error to facilitate custom error processing on the client. 
    extendedData = {}
    #: The fault code for the error. 
    faultCode = None
    #: Detailed description of what caused the error. 
    faultDetail = None
    #: A simple description of the error. 
    faultString = None
    #: Should a root cause exist for the error, this property contains those
    #: (traceback) details.
    rootCause = {}

class RemotingMessage(AbstractMessage):
    """
    Flex compatibility message that is sent by the C{<mx:RemoteObject>} MXML tag.

    Reference: U{http://livedocs.adobe.com/flex/2/langref/mx/rpc/remoting/mxml/RemoteObject.html}
    """
    #: Name of the method to be called.
    operation = None
    #: Name of the service to be called
    #: including package name.
    source = None

pyamf.register_class(RemotingMessage, 'flex.messaging.messages.RemotingMessage')
pyamf.register_class(ErrorMessage, 'flex.messaging.messages.ErrorMessage')
pyamf.register_class(CommandMessage, 'flex.messaging.messages.CommandMessage')
pyamf.register_class(AcknowledgeMessage, 'flex.messaging.messages.AcknowledgeMessage')
