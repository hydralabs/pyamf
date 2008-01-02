# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
AMF3 RemoteObject support.

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import calendar, time, uuid

from pyamf import remoting
from pyamf.remoting import gateway
from pyamf.flex.messaging import *

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
                # generate an error here
                ro_response = generate_error()
        elif isinstance(ro_request, RemotingMessage):
            try:
                service_request = self.gateway.getServiceRequest(amf_request,
                    ro_request.operation)
            except gateway.UnknownServiceError:
                amf_response.body = generate_error(ro_request)

                return amf_response

            ro_response = generate_acknowledgement(ro_request)
            ro_response.body = service_wrapper(service_request, *ro_request.body)

        amf_response.body = ro_response

        return amf_response
