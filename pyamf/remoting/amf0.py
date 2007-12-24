# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

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

    def authenticateRequest(self, request):
        """
        Authenticates the request against the service.

        @param request: The AMF request
        @type request: L{Request<pyamf.remoting.Request>}
        """ 
        username = password = None

        if 'Credentials' in request.headers:
            cred = request.headers['Credentials']

            username = cred['userid']
            password = cred['password']

        return self.gateway.authenticateRequest(username, password)

    def __call__(self, request):
        """
        Processes an AMF0 request.

        @param request: The request to be processed.
        @type request: L{Request<pyamf.remoting.Request>}

        @return: The response to the request.
        @rtype: L{Response<pyamf.remoting.Response>}
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
            authd = self.authenticateRequest(request)
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

        if 'DescribeService' in request.headers:
            response.body = service_request.service.description

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
        details=str(traceback.format_exception(cls, e, tb)).replace("\n", ''))
