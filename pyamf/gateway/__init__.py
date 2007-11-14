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

@author: U{Thijs Triemstra<mailto:info@collab.nl>}
@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import sys, traceback, types

from pyamf import remoting

class ServiceWrapper(object):
    """
    Remoting service.
    """

    def __init__(self, service, authenticator=None):
        """
        @param service:
        @type service:
        @param authenticator:
        @type authenticator:
        @rtype:
        @return:
        """
        self.service = service
        self.authenticator = authenticator

    def __cmp__(self, other):
        """
        @param other:
        @type other:
        @rtype:
        @return:
        """
        if isinstance(other, ServiceWrapper):
            return cmp(self.__dict__, other.__dict__)

        return cmp(self.service, other)

    def __call__(self, method, params):
        """
        Executes the service. If the service is a class, it will be instantiated

        @param method: The method to call on the service
        @type method: None or mixed
        @param params: The params to pass to the service
        @type params: list or tuple
        @return: The result of the execution
        @rtype: mixed
        """
        if isinstance(self.service, (type, types.ClassType)):
            service = self.service()
        else:
            service = self.service

        if method is not None:
            return getattr(self.service, method)(*params)

        if callable(self.service):
            return self.service(*params)

class ServiceRequest(object):
    """
    Remoting service request.
    """

    def __init__(self, request, service, method):
        """
        @param request:
        @type request:
        @param service:
        @type service:
        @param method:
        @type method:
        """
        self.request = request
        self.service = service
        self.method = method

    def __call__(self, *args):
        return self.service(self.method, args)

    def authenticate(self, username, password):
        """
        Authenticates the supplied credentials for the service.

        The default is to allow anything through.

        @param username:
        @type username:
        @param password:
        @type password:
        @return: Boolean determining whether the supplied credentials can
                 access the service.
        @rtype: bool
        """
        if self.service.authenticator is None:
            # The default is to allow anything through
            return True

        return self.service.authenticator(username, password)

class BaseGateway(object):
    """
    Generic Remoting gateway.
    """
    _request_class = ServiceRequest

    def __init__(self, services, debug=False):
        """
        @param services: Initial services.
        @type services: dict
        @param debug: Enable debugging.
        @type debug: bool
        """
        #:
        self.services = {}
        #: Number of requests from clients.
        self.request_number = 0
        #:
        self.debug = debug

        for name, service in services.iteritems():
            self.addService(service, name)

    def addService(self, service, name=None, authenticator=None):
        """
        Adds a service to the gateway.

        @raise RemotingError: Service already exists.
        @param service: The service to add to the gateway.
        @type service: callable or a class instance
        @param name: The name of the service.
        @type name: str
        @param authenticator: A callable that will check the credentials of
                              the request before allowing access to the service.
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

        @raise RemotingError: Unknow service
        @param message: The AMF message
        @type message: L{Message<remoting.Message>}
        @return: A tuple containing the service and the method requested
        @rtype: tuple      
        """
        target = message.target

        try:
            try:
                name, meth = target.rsplit('.', 1)
                return self._request_class(message.envelope, self.services[name], meth)
            except ValueError:
                pass

            return self._request_class(message.envelope, self.services[target], None)
        except KeyError:
            raise remoting.RemotingError("Unknown service %s" % target)

    def save_request(self, body, stream):
        """
        Write AMF request to disk.

        @param body: Body/contents of AMF request from the client.
        @type body:
        @param stream: Encoded output AMF message.
        @type stream:
        """
        fname = 'request_' + str(self.request_number)
        x = open(fname + ".in.amf", 'wb')
        x.write(body)
        x.close()

        if hasattr(stream, 'getvalue'):
            x = open(fname + ".out.amf", 'wb')
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
        @param request:
        @type request:

        @see: U{AMF remoting headers on OSFlash (external)
        <http://osflash.org/documentation/amf/envelopes/remoting/headers>}
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
        @type request: L{Message<remoting.Message>}
        @return: The response to the request
        @rtype: L{Message<remoting.Message>}
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
        Returns the response to the request.

        Any implementing gateway must define this function.

        @param request: The AMF request
        @type request: L{Envelope<remoting.Envelope>}

        @raise NotImplementedError:
        @return: The AMF response
        @rtype: L{Envelope<remoting.Envelope>}
        """
        raise NotImplementedError
