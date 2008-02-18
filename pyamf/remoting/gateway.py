# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Remoting server implementations.

@author: U{Thijs Triemstra<mailto:info@collab.nl>}
@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import types

import pyamf
from pyamf import remoting

fault_alias = pyamf.get_class_alias(remoting.ErrorFault)

class BaseServiceError(pyamf.BaseError):
    """
    Base service error.
    """

pyamf.register_class(BaseServiceError, attrs=fault_alias.attrs)
del fault_alias

class UnknownServiceError(BaseServiceError):
    """
    Client made a request for an unknown service.
    """

    _amf_code = 'Service.ResourceNotFound'

class UnknownServiceMethodError(BaseServiceError):
    """
    Client made a request for an unknown method.
    """

    _amf_code = 'Service.MethodNotFound'

class InvalidServiceMethodError(BaseServiceError):
    """
    Client made a request for an invalid methodname.
    """

    _amf_code = 'Service.MethodInvalid'

class ServiceWrapper(object):
    """
    Wraps a supplied service with extra functionality.

    @ivar service: The original service.
    @type service: C{callable}
    @ivar description: A description of the service.
    @type description: C{str}
    """

    def __init__(self, service, description=None,
        authenticator=None, expose_request=None):
        self.service = service
        self.description = description
        self.authenticator = authenticator
        self.expose_request = expose_request

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
                raise InvalidServiceMethodError, "Calls to private methods are not allowed"

            try:
                func = getattr(service, method)
            except AttributeError:
                raise UnknownServiceMethodError, "Unknown method %s" % str(method)

            if not callable(func):
                raise InvalidServiceMethodError, "Service method %s must be callable" % str(method)

            return func

        if not callable(service):
            raise UnknownServiceMethodError, "Unknown method %s" % str(self.service)

        return service

    def __call__(self, method, params):
        """
        Executes the service.

        If the service is a class, it will be instantiated.

        @param method: The method to call on the service.
        @type method: C{None} or C{mixed}
        @param params: The params to pass to the service.
        @type params: C{list} or C{tuple}
        @return: The result of the execution.
        @rtype: C{mixed}
        """
        func = self._get_service_func(method, params)

        return func(*params)

    def getMethods(self):
        """
        Gets a dict of valid method callables for the underlying service object
        """
        callables = {}

        for name in dir(self.service):
            method = getattr(self.service, name)

            if name.startswith('_') or not callable(method):
                continue

            callables[name] = method

        return callables

    def getAuthenticator(self, service_request=None):
        if service_request == None:
            return self.authenticator

        methods = self.getMethods()

        if service_request.method is None:
            if hasattr(self.service, '_pyamf_authenticator'):
                return self.service._pyamf_authenticator

        if service_request.method not in methods:
            return self.authenticator

        method = methods[service_request.method]

        if hasattr(method, '_pyamf_authenticator'):
            return method._pyamf_authenticator

        return self.authenticator

    def mustExposeRequest(self, service_request=None):
        if service_request == None:
            return self.expose_request

        methods = self.getMethods()

        if service_request.method is None:
            if hasattr(self.service, '_pyamf_expose_request'):
                return self.service._pyamf_expose_request

            return self.expose_request

        if service_request.method not in methods:
            return self.expose_request

        method = methods[service_request.method]

        if hasattr(method, '_pyamf_expose_request'):
            return method._pyamf_expose_request

        return self.expose_request

class ServiceRequest(object):
    """
    Remoting service request.

    @ivar request: The request to service.
    @type request: L{Envelope<pyamf.remoting.Envelope>}
    @ivar service: Facilitates the request.
    @type service: L{ServiceWrapper}
    @ivar method: The method to call on the service. A value of C{None}
        means that the service will be called directly.
    @type method: C{None} or C{str}
    """

    def __init__(self, amf_request, service, method):
        self.request = amf_request
        self.service = service
        self.method = method

    def __call__(self, *args):
        return self.service(self.method, args)

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

    @ivar services: A map of service names to callables.
    @type services: L{ServiceCollection}
    @ivar authenticator: A callable that will check the credentials of
        the request before allowing access to the service. Will return a
        C{bool} value.
    @type authenticator: C{Callable} or C{None}
    """

    _request_class = ServiceRequest

    def __init__(self, services={}, authenticator=None, expose_request=False):
        self.services = ServiceCollection()
        self.authenticator = authenticator
        self.expose_request = expose_request

        if not hasattr(services, 'iteritems'):
            raise TypeError, "dict type required for services"

        for name, service in services.iteritems():
            self.addService(service, name)

    def addService(self, service, name=None, description=None,
        authenticator=None, expose_request=None):
        """
        Adds a service to the gateway.

        @param service: The service to add to the gateway.
        @type service: C{callable}, class instance, or a module
        @param name: The name of the service.
        @type name: C{str}
        @raise RemotingError: Service already exists.
        @raise TypeError: C{service} must be C{callable} or a module.
        """
        if isinstance(service, (int, long, float, basestring)):
            raise TypeError, "service cannot be a scalar value"

        allowed_types = (types.ModuleType, types.FunctionType, types.DictType,
            types.MethodType, types.InstanceType, types.ObjectType)

        if not callable(service) and not isinstance(service, allowed_types):
            raise TypeError, "service must be callable, a module, or an object"

        if name is None:
            # TODO: include the module in the name
            if isinstance(service, (type, types.ClassType)):
                name = service.__name__
            elif isinstance(service, (types.FunctionType)):
                name = service.func_name
            elif isinstance(service, (types.ModuleType)):
                name = service.__name__
            else:
                name = str(service)

        if name in self.services:
            raise remoting.RemotingError, "Service %s already exists" % name

        self.services[name] = ServiceWrapper(service, description,
            authenticator, expose_request)

    def removeService(self, service):
        """
        Removes a service from the gateway.

        @param service: The service to remove from the gateway.
        @type service: C{callable} or a class instance
        @raise NameError: Service not found.
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

    def getServiceRequest(self, request, target):
        """
        Returns a service based on the message.

        @raise RemotingError: Unknown service.
        @param request: The AMF request.
        @type request: L{Request<pyamf.remoting.Request>}
        @rtype: L{ServiceRequest}
        """
        try:
            return self._request_class(
                request.envelope, self.services[target], None)
        except KeyError:
            pass

        try:
            sp = target.split('.')
            name, meth = '.'.join(sp[:1]), sp[-1]

            return self._request_class(
                request.envelope, self.services[name], meth)
        except (ValueError, KeyError):
            pass

        raise UnknownServiceError, "Unknown service %s" % target

    def getProcessor(self, request):
        """
        Returns request processor.

        @param request: The AMF message.
        @type request: L{Request<remoting.Request>}
        """
        if request.target == 'null':
            from pyamf.remoting import amf3

            return amf3.RequestProcessor(self)
        else:
            from pyamf.remoting import amf0

            return amf0.RequestProcessor(self)

    def getResponse(self, amf_request):
        """
        Returns the response to the request.

        Any implementing gateway must define this function.

        @param amf_request: The AMF request.
        @type amf_request: L{Envelope<pyamf.remoting.Envelope>}

        @return: The AMF response.
        @rtype: L{Envelope<pyamf.remoting.Envelope>}
        """
        raise NotImplementedError

    def mustExposeRequest(self, service_request):
        """
        Decides whether the underlying http request should be exposed as the
        first argument to the method call. This is
        granular, looking at the service method first, then at the service
        level and finally checking the gateway.

        @rtype: C{bool}
        """
        expose_request = service_request.service.mustExposeRequest(service_request)

        if expose_request is None:
            if self.expose_request is None:
                return False

            return self.expose_request

        return expose_request

    def getAuthenticator(self, service_request):
        """
        Gets an authenticator callable based on the service_request. This is
        granular, looking at the service method first, then at the service
        level and finally to see if there is a global authenticator function
        for the gateway. Returns C{None} if one could not be found.
        """
        auth = service_request.service.getAuthenticator(service_request)

        if auth is None:
            return self.authenticator

        return auth

    def authenticateRequest(self, service_request, username, password):
        """
        Processes an authentication request. If no authenticator is supplied,
        then authentication succeeds.

        @return: Returns a C{bool} based on the result of authorization.
        @rtype: C{bool}
        """
        authenticator = self.getAuthenticator(service_request)

        if authenticator is None:
            return True

        return authenticator(username, password) == True

    def callServiceRequest(self, service_request, *args, **kwargs):
        """
        Executes the service_request call
        """
        if self.mustExposeRequest(service_request):
            http_request = kwargs.get('http_request', None)
            args = (http_request,) + args

        return service_request(*args)

def authenticate(func, c):
    """
    A decorator that facilitates authentication per method.
    """
    if not callable(func):
        raise TypeError, "func must be callable"

    if not callable(c):
        raise TypeError, "authenticator must be callable"

    if isinstance(func, types.UnboundMethodType):
        setattr(func.im_func, '_pyamf_authenticator', c)
    else:
        setattr(func, '_pyamf_authenticator', c)

    return func

def expose_request(func):
    """
    A decorator that adds an expose_request flag to the underlying callable
    """
    if not callable(func):
        raise TypeError, "func must be callable"

    if isinstance(func, types.UnboundMethodType):
        setattr(func.im_func, '_pyamf_expose_request', True)
    else:
        setattr(func, '_pyamf_expose_request', True)

    return func

from glob import glob
import sys, os.path

class LazyImporter(object):
    """
    Lazily import modules, such that they don't actually get loaded until
    you use them.

    @ivar module: Module name.
    @type module: C{str}
    """
    module = 'pyamf.remoting'

    def __init__(self, module_name):
        self.__name__ = module_name
        self.__file__ = None

    def __getattr__(self, name):
        full_import_name = '%s.%s' % (LazyImporter.module, self.__name__)
        __import__(full_import_name)
        mod = sys.modules[full_import_name]
        setattr(sys.modules[LazyImporter.module], self.__name__, mod)

        self.__dict__.update(mod.__dict__)

        return getattr(mod, name)

try: 
    import pkg_resources
    packageDir = pkg_resources.resource_filename('pyamf', 'remoting')
except:
    pass
else:
    packageDir = os.path.dirname(__file__)

for f in glob(os.path.join(packageDir, '*gateway.py')):
    name = f.split(os.path.sep)[-1].split('.py')[0]
    localname = name.split('gateway')[0]

    if localname == '':
        continue

    importer = LazyImporter(name)
    sys.modules['%s.%s' % ('pyamf.remoting.gateway', localname)] = importer
    setattr(sys.modules['pyamf.remoting.gateway'], localname, importer)

del f
del glob, os
