# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Flex Messaging implementation.

This module contains the message classes used with Flex Data Services.

@see: U{RemoteObject on OSFlash (external)
<http://osflash.org/documentation/amf3#remoteobject>}

@since: 0.1.0
"""

import pyamf

__all__ = [
    'RemotingMessage',
    'CommandMessage',
    'AcknowledgeMessage',
    'ErrorMessage'
]

class AbstractMessage(object):
    """
    Abstract base class for all Flex messages.

    Messages have two customizable sections; headers and data. The headers
    property provides access to specialized meta information for a specific
    message instance. The data property contains the instance specific data
    that needs to be delivered and processed by the decoder.

    @see: U{AbstractMessage on Livedocs (external)
    <http://livedocs.adobe.com/flex/201/langref/mx/messaging/messages/AbstractMessage.html>}

    @ivar body: Specific data that needs to be delivered to the remote
        destination.
    @type body: C{mixed}
    @ivar clientId: Indicates which client sent the message.
    @type clientId: C{str}
    @ivar destination: Message destination.
    @type destination: C{str}
    @ivar headers: Message headers. Core header names start with DS.
    @type headers: C{dict}
    @ivar messageId: Unique Message ID.
    @type messageId: C{str}
    @ivar timeToLive: How long the message should be considered valid and
        deliverable.
    @type timeToLive: C{int}
    @ivar timestamp: Timestamp when the message was generated.
    @type timestamp: C{int}
    """

    #: Each message pushed from the server will contain this header identifying
    #: the client that will receive the message.
    DESTINATION_CLIENT_ID_HEADER = "DSDstClientId"
    #: Messages are tagged with the endpoint id for the channel they are sent
    #: over.
    ENDPOINT_HEADER = "DSEndpoint"
    #: Messages that need to set remote credentials for a destination carry the
    #: C{Base64} encoded credentials in this header.
    REMOTE_CREDENTIALS_HEADER = "DSRemoteCredentials"
    #: The request timeout value is set on outbound messages by services or
    #: channels and the value controls how long the responder will wait for an
    #: acknowledgement, result or fault response for the message before timing
    #: out the request.
    REQUEST_TIMEOUT_HEADER = "DSRequestTimeout"

    def __init__(self, *args, **kwargs):
        self.body = kwargs.get('body', None)
        self.clientId = kwargs.get('clientId', None)
        self.destination = kwargs.get('destination', None)
        self.headers = kwargs.get('headers', {})
        self.messageId = kwargs.get('messageId', None)
        self.timeToLive = kwargs.get('timeToLive', 0)
        self.timestamp = kwargs.get('timestamp', 0)

    def __repr__(self):
        m = '<%s ' % self.__class__.__name__

        for k, v in self.__dict__.iteritems():
            m += ' %s=%r' % (k, v)

        return m + " />"

class AsyncMessage(AbstractMessage):
    """
    I am the base class for all asynchronous Flex messages.

    @see: U{AsyncMessage on Livedocs (external)
    <http://livedocs.adobe.com/flex/201/langref/mx/messaging/messages/AsyncMessage.html>}

    @ivar correlationId: Correlation id of the message.
    @type correlationId: C{str}
    """

    #: Messages that were sent with a defined subtopic property indicate their
    #: target subtopic in this header.
    SUBTOPIC_HEADER = "DSSubtopic"

    def __init__(self, *args, **kwargs):
        AbstractMessage.__init__(self, *args, **kwargs)

        self.correlationId = kwargs.get('correlationId', None)

class AcknowledgeMessage(AsyncMessage):
    """
    I acknowledge the receipt of a message that was sent previously.

    Every message sent within the messaging system must receive an
    acknowledgement.

    @see: U{AcknowledgeMessage on Livedocs (external)
    <http://livedocs.adobe.com/flex/201/langref/mx/messaging/messages/AcknowledgeMessage.html>}
    """

    #: Used to indicate that the acknowledgement is for a message that
    #: generated an error.
    ERROR_HINT_HEADER = "DSErrorHint"

class CommandMessage(AsyncMessage):
    """
    Provides a mechanism for sending commands related to publish/subscribe
    messaging, ping, and cluster operations.

    @see: U{CommandMessage on Livedocs (external)
    <http://livedocs.adobe.com/flex/201/langref/mx/messaging/messages/CommandMessage.html>}

    @ivar operation: The command
    @type operation: C{int}
    @ivar messageRefType: hmm, not sure about this one.
    @type messageRefType: C{str}
    """

    #: The server message type for authentication commands.
    AUTHENTICATION_MESSAGE_REF_TYPE = "flex.messaging.messages.AuthenticationMessage"
    #: This is used to test connectivity over the current channel to the remote
    #: endpoint.
    PING_OPERATION = 5
    #: This is used by a remote destination to sync missed or cached messages
    #: back to a client as a result of a client issued poll command.
    SYNC_OPERATION = 4
    #: This is used to request a list of failover endpoint URIs for the remote
    #: destination based on cluster membership.
    CLUSTER_REQUEST_OPERATION = 7
    #: This is used to send credentials to the endpoint so that the user can be
    #: logged in over the current channel. The credentials need to be C{Base64}
    #: encoded and stored in the body of the message.
    LOGIN_OPERATION = 8
    #: This is used to log the user out of the current channel, and will
    #: invalidate the server session if the channel is HTTP based.
    LOGOUT_OPERATION = 9
    #: This is used to poll a remote destination for pending, undelivered
    #: messages.
    POLL_OPERATION = 2
    #: Subscribe commands issued by a consumer pass the consumer's C{selector}
    #: expression in this header.
    SELECTOR_HEADER = "DSSelector"
    #: This is used to indicate that the client's session with a remote
    #: destination has timed out.
    SESSION_INVALIDATE_OPERATION = 10
    #: This is used to subscribe to a remote destination.
    SUBSCRIBE_OPERATION = 0
    #: This is the default operation for new L{CommandMessage} instances.
    UNKNOWN_OPERATION = 1000
    #: This is used to unsubscribe from a remote destination.
    UNSUBSCRIBE_OPERATION = 1
    #: This operation is used to indicate that a channel has disconnected.
    DISCONNECT_OPERATION = 12

    def __init__(self, *args, **kwargs):
        AsyncMessage.__init__(self, *args, **kwargs)

        self.operation = kwargs.get('operation', None)
        #: Remote destination belonging to a specific service, based upon
        #: whether this message type matches the message type the service
        #: handles.
        self.messageRefType = kwargs.get('messageRefType', None)

class ErrorMessage(AcknowledgeMessage):
    """
    I am the Flex error message to be returned to the client.

    This class is used to report errors within the messaging system.

    @see: U{ErrorMessage on Livedocs (external)
    <http://livedocs.adobe.com/flex/201/langref/mx/messaging/messages/ErrorMessage.html>}
    """

    #: If a message may not have been delivered, the faultCode will contain
    #: this constant.
    MESSAGE_DELIVERY_IN_DOUBT = "Client.Error.DeliveryInDoubt"
    #: Header name for the retryable hint header.
    #:
    #: This is used to indicate that the operation that generated the error may
    #: be retryable rather than fatal.
    RETRYABLE_HINT_HEADER = "DSRetryableErrorHint"

    def __init__(self, *args, **kwargs):
        AcknowledgeMessage.__init__(self, *args, **kwargs)
        #: Extended data that the remote destination has chosen to associate
        #: with this error to facilitate custom error processing on the client.
        self.extendedData = kwargs.get('extendedData', {})
        #: Fault code for the error.
        self.faultCode = kwargs.get('faultCode', None)
        #: Detailed description of what caused the error.
        self.faultDetail = kwargs.get('faultDetail', None)
        #: A simple description of the error.
        self.faultString = kwargs.get('faultString', None)
        #: Should a traceback exist for the error, this property contains the
        #: message.
        self.rootCause = kwargs.get('rootCause', {})

class RemotingMessage(AbstractMessage):
    """
    I am used to send RPC requests to a remote endpoint.

    @see: U{RemotingMessage on Livedocs (external)
    <http://livedocs.adobe.com/flex/201/langref/mx/messaging/messages/RemotingMessage.html>}
    """

    def __init__(self, *args, **kwargs):
        AbstractMessage.__init__(self, *args, **kwargs)
        #: Name of the remote method/operation that should be called.
        self.operation = kwargs.get('operation', None)
        #: Name of the service to be called including package name.
        #: This property is provided for backwards compatibility.
        self.source = kwargs.get('source', None)

for x in (RemotingMessage, ErrorMessage, CommandMessage, AcknowledgeMessage, AsyncMessage):
    pyamf.register_class(x, 'flex.messaging.messages.%s' % x.__name__, metadata=['amf3'])
del x
