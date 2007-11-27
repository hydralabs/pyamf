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
Server/client implementations for PyAMF.

@author: U{Thijs Triemstra<mailto:info@collab.nl>}
@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import sys, traceback, types

import pyamf
from pyamf import remoting

CONTENT_TYPE = 'application/x-amf'

class Fault(object):
    """
    I represent a Fault message (mx.rpc.Fault).

    @ivar code: A simple code describing the fault.
    @type code: C{str}
    @ivar detail: Any extra details of the fault.
    @type detail: C{str}
    @ivar description: Text description of the fault.
    @type description: C{str}
    @ivar root_cause: The root cause of the fault.
    @type root_cause: object or None
    """

    def __init__(self, code=None, detail=None, description=None, root_cause=None):
        self.code = code
        self.detail = detail
        self.description = description
        self.root_cause = root_cause

    def _get_faultCode(self):
        if self.code is None:
            return 'null'

        return str(self.code)

    def _set_faultCode(self, val):
        if val is 'null':
            self.code = None
        else:
            self.code = str(val)

    def _get_faultDetail(self):
        if self.detail is None:
            return 'null'

        return str(self.detail)

    def _set_faultDetail(self, val):
        if val is 'null':
            self.detail = None
        else:
            self.detail = str(val)

    def _get_faultDescription(self):
        if self.description is None:
            return 'null'

        return str(self.description)

    def _set_faultDescription(self, val):
        if val is 'null':
            self.description = None
        else:
            self.description = str(val)

    def _get_rootCause(self):
        return self.root_cause

    def _set_rootCause(self, val):
        self.root_cause = val

    faultCode = property(_get_faultCode, _set_faultCode)
    faultDetail = property(_get_faultDetail, _set_faultDetail)
    faultString = property(_get_faultDescription, _set_faultDescription)
    rootCause = property(_get_rootCause, _set_rootCause)

try:
    pyamf.register_class(Fault, 'mx.rpc.Fault',
        attrs=['faultCode', 'faultDetail', 'faultString', 'rootCause'])
except ValueError:
    pass

class ServiceWrapper(object):
    """
    Wraps a supplied service with extra functionality.

    @ivar service: The original service
    @type service: callable
    @ivar authenticator: Will be called before the service is called to check
        that the supplied credentials (if any) can access the service.
    @type authenticator: callable with two args, username and password. Returns
        a bool based on the success of authentication.
    @ivar description: A description of the service
    @type description: str
    """

    def __init__(self, service, authenticator=None, description=None):
        """
        Initialises the service wrapper
        """
        self.service = service
        self.authenticator = authenticator
        self.description = description

    def __cmp__(self, other):
        if isinstance(other, ServiceWrapper):
            return cmp(self.__dict__, other.__dict__)

        return cmp(self.service, other)

    def _get_service_func(self, method, params):
        service = None

        if isinstance(self.service, (type, types.ClassType)):
            service = self.service()
        else:
            service = self.service

        if method is not None:
            method = str(method)

            if method.startswith('_'):
                raise NameError, "Calls to private methods is not allowed"

            try:
                func = getattr(service, method)
            except AttributeError:
                raise NameError, "Unknown method %s" % method

            if not callable(func):
                raise TypeError, "Service method %s must be callable" % method

            return func

        if not callable(service):
            raise TypeError, "Service %s must be callable" % self.service

        return service

    def __call__(self, method, params):
        """
        Executes the service. If the service is a class, it will be
        instantiated

        @param method: The method to call on the service
        @type method: None or mixed
        @param params: The params to pass to the service
        @type params: list or tuple
        @return: The result of the execution
        @rtype: mixed
        """
        func = self._get_service_func(method, params)

        return func(*params)

class ServiceRequest(object):
    """
    Remoting service request.

    @ivar request: The request to service.
    @type request: L{pyamf.remoting.Envelope}
    @ivar service: Facilitates the request.
    @type service: L{ServiceWrapper}
    @ivar method: The method to call on the service. A value of None means that
        the service will be called directly.
    @type method: None or str
    """

    def __init__(self, request, service, method):
        """
        Initialises the service request
        """
        self.request = request
        self.service = service
        self.method = method

    def __call__(self, *args):
        return self.service(self.method, args)

    def authenticate(self, username, password):
        """
        Authenticates the supplied credentials for the service. The default is
        to allow anything through.

        @return: Boolean determining whether the supplied credentials can
            access the service.
        @rtype: bool
        """
        if self.service.authenticator is None:
            # The default is to allow anything through
            return True

        return self.service.authenticator(username, password)

class ServiceCollection(dict):
    """
    I hold a collection of services, mapping names to objects.
    """

    def __contains__(self, value):
        if isinstance(value, basestring):
            return value in self.keys()

        return value in self.values()

class BaseGateway(object):
    """
    Generic Remoting gateway.

    @ivar services: A map of service names to callables
    @type services: L{ServiceCollection}
    """

    _request_class = ServiceRequest

    def __init__(self, services={}):
        """
        @param services: Initial services.
        @type services: dict
        """
        self.services = ServiceCollection()

        if not hasattr(services, 'iteritems'):
            raise TypeError, "dict type required for services"

        for name, service in services.iteritems():
            self.addService(service, name)

    def addService(self, service, name=None, authenticator=None, description=None):
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
        if not callable(service):
            raise TypeError, "service must be callable"

        if name is None:
            # TODO: include the module in the name
            if isinstance(service, (type, types.ClassType)):
                name = service.__name__
            elif isinstance(service, (type, types.FunctionType)):
                name = service.func_name
            else:
                name = str(service)

        if name in self.services:
            raise remoting.RemotingError, "Service %s already exists" % name

        self.services[name] = ServiceWrapper(service, authenticator,
            description)

    def removeService(self, service):
        """
        Removes a service from the gateway.

        @param service: The service to remove from the gateway
        @type service: callable or a class instance
        """
        if service not in self.services:
            raise NameError, "Service %s not found" % str(service)

        for name, wrapper in self.services.iteritems():
            if isinstance(service, basestring) and service == name:
                del self.services[name]

                return
            elif isinstance(service, ServiceWrapper) and wrapper == service:
                del self.services[name]

                return
            elif isinstance(service, (type, types.ClassType,
                types.FunctionType)) and wrapper.service == service:
                del self.services[name]

                return

        # shouldn't ever get here
        raise RuntimeError, "Something went wrong ..."

    def getServiceRequest(self, message):
        """
        Returns a service based on the message

        @raise RemotingError: Unknown service
        @param message: The AMF message
        @type message: L{Message<remoting.Message>}
        @rtype: L{ServiceRequest}
        """
        target = message.target

        try:
            return self._request_class(
                message.envelope, self.services[target], None)
        except KeyError:
            pass

        try:
            name, meth = target.rsplit('.', 1)
            return self._request_class(
                message.envelope, self.services[name], meth)
        except (ValueError, KeyError):
            pass

        # All methods exhausted
        raise NameError, "Unknown service %s" % target

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

    def authenticateRequest(self, service_request, request):
        """
        Authenticates the request against the service.
        """ 
        username = password = None

        if 'Credentials' in request.headers:
            cred = request.headers['Credentials']

            try:
                username = cred['userid']
                password = cred['password']
            except KeyError:
                raise remoting.RemotingError, "Invalid credentials object"

        return service_request.authenticate(username, password)

    def processRequest(self, request):
        """
        Processes a request.

        @param request: The request to be processed
        @type request: L{Message<remoting.Message>}
        @return: The response to the request
        @rtype: L{Message<remoting.Message>}
        """
        response = remoting.Message(None, request.target,
            # everything is OK, until it isn't
            remoting.STATUS_OK, None)

        try:
            service_request = self.getServiceRequest(request)
        except NameError, e:
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
            response.body = Fault(code='AuthenticationError',
                description='Authentication failed')

            return response

        # process the request
        try:
            response.body = service_request(*request.body)
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            response.body = build_fault()
            response.status = remoting.STATUS_ERROR

        return response

    def getResponse(self, request):
        """
        Returns the response to the request. Any implementing gateway must
        define this function.

        @param request: The AMF request
        @type request: L{Envelope<remoting.Envelope>}

        @return: The AMF response
        @rtype: L{Envelope<remoting.Envelope>}
        """
        raise NotImplementedError

def build_fault():
    """
    Builds a L{Fault} object based on the last exception raised.
    """
    cls, e, tb = sys.exc_info()

    return Fault(code=cls.__name__, description=str(e),
        detail=traceback.format_exception(cls, e, tb), 
        root_cause=traceback.extract_tb(tb))
