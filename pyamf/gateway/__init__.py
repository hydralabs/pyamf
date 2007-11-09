# -*- encoding: utf8 -*-
#
# Copyright (c) 2007 The PyAMF Project. All rights reserved.
# 
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
Server/client implementations for PyAMF.

@author: Thijs Triemstra
@author: Nick Joyce

@since: 0.1.0
"""

import sys, traceback

from pyamf import remoting

class ServiceWrapper(object):
    """
    """

    def __init__(self, service, authenticator=None):
        self.service = service
        self.authenticator = authenticator

    def __cmp__(self, other):
        if isinstance(other, ServiceWrapper):
            return cmp(self.__dict__, other.__dict__)

        return cmp(self.service, other)

    def __call__(self, method, params):
        if method is not None:
            return getattr(self.service, method)(*params)

        if callable(self.service):
            return self.service(*params)

class ServiceRequest(object):
    """
    """

    def __init__(self, request, service, method):
        self.request = request
        self.service = service
        self.method = method

    def __call__(self, *args):
        return self.service(self.method, args)

    def authenticate(self, username, password):
        """
        
        @return: Boolean determining whether the supplied credentials can
                 access the service
        @rettype: bool
        """
        if self.service.authenticator is None:
            # The default is to allow anything through
            return True

        return self.service.authenticator(username, password)

class BaseGateway(object):
    """
    Generic remoting gateway class.
    """

    def __init__(self, services):
        """
        @param services: Initial services
        @type services: dict
        """
        self.services = {}

        for name, service in services.iteritems():
            self.addService(service, name)

    def addService(self, service, name=None, authenticator=None):
        """
        Adds a service to the gateway.

        @param service: The service to add to the gateway
        @type service: callable or a class instance
        @param name: The name of the service
        @type name: str
        @param authenticator: A callable that will check the credentials of
                              the request before allowing access to the service
        @type authenticator: Callable
        """
        if name is None:
            # TODO: include the module in the name
            name = service.__class__.__name__

        if name in self.services.keys():
            raise remoting.RemotingError("Service %s already exists" % name)

        self.services[name] = ServiceWrapper(service, authenticator)

    def removeService(self, service):
        """
        Removes a service from the gateway.

        @param service: The service to remove from the gateway
        @type service: callable or a class instance
        """
        self.services.popitem(service)

    def getServiceRequest(self, message):
        """
        Returns a service based on the message

        @param message: The AMF message
        @type target: L{remoting.Message}
        @return A tuple containing the service and the method requested
        @rettype tuple
        """
        target = message.target

        try:
            try:
                name, meth = target.rsplit('.', 1)
                return ServiceRequest(message.envelope, self.services[name], meth)
            except ValueError:
                pass

            return ServiceRequest(message.envelope, self.services[target], None)
        except KeyError:
            raise remoting.RemotingError("Unknown service %s" % target)

    def save_request(self, body, stream):
        """
        Write AMF request to disk.
        """
        x = open('request_' + str(self.request_number) + ".in.amf", 'wb')
        x.write(body)
        x.close()

        if hasattr(stream, 'getvalue'):
            x = open('request_' + str(self.request_number) + ".out.amf", 'wb')
            x.write(stream.getvalue())
            x.close()

    def getErrorResponse(self, (cls, e, tb)):
        """
        Call traceback and error details.

        @param cls: Class
        @type cls: callable or a class instance
        @param e: 
        @type e: 
        @param tb: 
        @type tb:
        """
        details = traceback.format_exception(cls, e, tb)

        return dict(
            code='SERVER.PROCESSING',
            level='Error',
            description='%s: %s' % (cls.__name__, e),
            type=cls.__name__,
            details=''.join(details),
        )

    def getProcessor(self, request):
        """
        
        """
        if 'DescribeService' in request.headers:
            return NotImplementedError

        return self.processRequest

    def _authenticate(self, service_request, request):
        username = password = None

        if 'Credentials' in request.headers:
            cred = request.headers['Credentials']
            username = cred['userid']
            password = cred['password']

        return service_request.authenticate(username, password)

    def processRequest(self, request):
        """
        Processes a request.

        @param request: The request to be processed
        @type request: L{remoting.Message}
        @return The response to the request
        @rettype L{remoting.Message}
        """
        response = remoting.Message(None, None, None, None)

        service_request = self.getServiceRequest(request)
        
        # we have a valid service, now attempt authentication
        if not self._authenticate(service_request, request):
            # FIXME: what error to return here?
            response.status = remoting.STATUS_ERROR
            response.body = dict(
                code='SERVER.AUTHENTICATION',
                level='Auth'
            )

            return response

        try:
            response.body = service_request(*request.body)
            response.status = remoting.STATUS_OK
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            response.body = self.getErrorResponse(sys.exc_info())
            response.status = remoting.STATUS_ERROR

        return response

    def getResponse(self, request):
        """
        Returns the response to the request. Any implementing gateway must 
        define this function

        @param request: The AMF request
        @type request: L{remoting.Envelope}
        @return: The AMF response
        @rettype: L{remoting.Envelope}
        """
        raise NotImplementedError
