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
AMF0 Remoting support.

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import traceback, sys

from pyamf import remoting
from pyamf.remoting import gateway

class RequestProcessor(object):
    def __init__(self, gateway):
        self.gateway = gateway

    def authenticateRequest(self, service_request, request):
        """
        Authenticates the request against the service.

        @param service_request:
        @type service_request:
        @param request: The AMF request
        @type request: L{Request<remoting.Request>}
        """ 
        username = password = None

        if 'Credentials' in request.headers:
            cred = request.headers['Credentials']

            username = cred['userid']
            password = cred['password']

        return service_request.authenticate(username, password)

    def __call__(self, request):
        """
        Processes an AMF0 request.

        @param request: The request to be processed.
        @type request: L{Request<remoting.Request>}

        @return: The response to the request.
        @rtype: L{Response<remoting.Response>}
        """
        response = remoting.Response(None)

        try:
            service_request = self.gateway.getServiceRequest(request, request.target)
        except gateway.UnknownServiceError, e:
            response.status = remoting.STATUS_ERROR
            response.body = build_fault()

            return response

        # we have a valid service, now attempt authentication
        try:
            authd = self.authenticateRequest(service_request, request)
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            response.status = remoting.STATUS_ERROR
            response.body = build_fault()

            return response

        if not authd:
            # authentication failed
            response.status = remoting.STATUS_ERROR
            response.body = remoting.ErrorFault(code='AuthenticationError',
                description='Authentication failed')

            return response

        try:
            response.body = service_request(*request.body)
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            response.body = build_fault()
            response.status = remoting.STATUS_ERROR

        return response

def build_fault():
    """
    Builds a L{remoting.ErrorFault} object based on the last exception raised.
    """
    cls, e, tb = sys.exc_info()

    if hasattr(cls, '_amf_code'):
        code = cls._amf_code
    else:
        code = cls.__name__

    return remoting.ErrorFault(code=code, description=str(e),
        details=traceback.format_exception(cls, e, tb))
