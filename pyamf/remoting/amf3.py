# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
AMF3 RemoteObject support.

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import calendar, time, uuid

import pyamf
from pyamf import remoting
from pyamf.remoting import gateway
from pyamf.flex.messaging import *

error_alias = pyamf.get_class_alias(ErrorMessage)

class BaseServerError(pyamf.BaseError):
    """
    Base server errror
    """

class ServerCallFailed(BaseServerError):
    """
    A catchall error.
    """

    _amf_code = 'Server.Call.Failed'

pyamf.register_class(ServerCallFailed, attrs=error_alias.attrs)

del error_alias

def generate_random_id():
    return str(uuid.uuid4())

def generate_acknowledgement(request=None):
    ack = AcknowledgeMessage()

    ack.messageId = generate_random_id()
    ack.clientId = generate_random_id()
    ack.timestamp = calendar.timegm(time.gmtime())

    if request:
        ack.correlationId = request.messageId

    return ack

def generate_error(request):
    """
    Builds an L{pyamf.flex.messaging.ErrorMessage} based on the last traceback
    and the request that was sent
    """
    import sys, traceback
    cls, e, tb = sys.exc_info()

    if hasattr(cls, '_amf_code'):
        code = cls._amf_code
    else:
        code = cls.__name__

    detail = []

    for x in traceback.format_exception(cls, e, tb):
        detail.append(x.replace("\\n", ''))

    return ErrorMessage(messageId=generate_random_id(), clientId=generate_random_id(),
        timestamp=calendar.timegm(time.gmtime()), correlationId = request.messageId,
        faultCode=code, faultString=str(e), faultDetail=str(detail), extendedData=detail)

class RequestProcessor(object):
    def __init__(self, gateway):
        self.gateway = gateway

    def __call__(self, amf_request, service_wrapper=lambda service_request, *body: service_request(*body)):
        """
        Processes an AMF3 Remote Object request.

        @param amf_request: The request to be processed.
        @type amf_request: L{Request<pyamf.remoting.Request>}

        @return: The response to the request.
        @rtype: L{Response<pyamf.remoting.Response>}
        """
        amf_response = remoting.Response(None)
        ro_request = amf_request.body[0]
        ro_response = None

        if isinstance(ro_request, CommandMessage):
            if ro_request.operation == CommandMessage.PING_OPERATION:
                ro_response = generate_acknowledgement(ro_request)
                ro_response.body = True
            elif ro_request.operation == CommandMessage.LOGIN_OPERATION:
                # authentication here
                pass
            else:
                try:
                    raise ServerCallFailed, "Unknown command operation %s" % ro_request.operation
                except:
                    ro_response = generate_error(ro_request)
                    amf_response.status = remoting.STATUS_ERROR
        elif isinstance(ro_request, RemotingMessage):
            try:
                service_request = self.gateway.getServiceRequest(amf_request,
                    ro_request.operation)

                ro_response = generate_acknowledgement(ro_request)
                ro_response.body = service_wrapper(service_request, *ro_request.body)
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                amf_response.body = generate_error(ro_request)
                amf_response.status = remoting.STATUS_ERROR

                return amf_response

        amf_response.body = ro_response

        return amf_response
