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
AMF3 Remote Object support.

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

    def __call__(self, amf_request):
        """
        Processes an AMF3 Remote Object request.

        @param amf_request: The request to be processed.
        @type amf_request: L{Request<remoting.Request>}

        @return: The response to the request.
        @rtype: L{Response<remoting.Response>}
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
            ro_response.body = service_request(*ro_request.body)

        amf_response.body = ro_response

        return amf_response
