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

#: AMF mimetype.
CONTENT_TYPE = 'application/x-amf'

fault_alias = pyamf.get_class_alias(remoting.ErrorFault)

class BaseServiceError(pyamf.BaseError):
    """
    Base service error.
    """

class UnknownServiceError(BaseServiceError):
    """
    Client made a request for an unknown service.
    """

    _amf_code = 'Service.ResourceNotFound'

pyamf.register_class(UnknownServiceError, attrs=fault_alias.attrs)

class UnknownServiceMethodError(BaseServiceError):
    """
    Client made a request for an unknown method.
    """

    _amf_code = 'Service.MethodNotFound'

pyamf.register_class(UnknownServiceMethodError, attrs=fault_alias.attrs)

class InvalidServiceMethodError(BaseServiceError):
    """
    Client made a request for an invalid methodname.
    """

    _amf_code = 'Service.MethodInvalid'

pyamf.register_class(InvalidServiceMethodError, attrs=fault_alias.attrs)

del fault_alias

class ServiceWrapper(object):
    """
    Wraps a supplied service with extra functionality.

    @ivar service: The original service.
    @type service: C{callable}
    @ivar description: A description of the service.
    @type description: C{str}
    """

    def __init__(self, service, description=None):
        self.service = service
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

    def __init__(self, services={}, authenticator=None):
        self.services = ServiceCollection()
        self.authenticator = authenticator

        if not hasattr(services, 'iteritems'):
            raise TypeError, "dict type required for services"

        for name, service in services.iteritems():
            self.addService(service, name)

    def addService(self, service, name=None, description=None):
        """
        Adds a service to the gateway.

        @param service: The service to add to the gateway.
        @type service: callable, class instance, or a module
        @param name: The name of the service.
        @type name: C{str}
        @raise RemotingError: Service already exists.
        @raise TypeError: C{service} must be callable or a module.
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

        self.services[name] = ServiceWrapper(service, description)

    def removeService(self, service):
        """
        Removes a service from the gateway.

        @param service: The service to remove from the gateway.
        @type service: callable or a class instance
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
        @type request: L{Request<remoting.Request>}
        @rtype: L{ServiceRequest}
        """
        try:
            return self._request_class(
                request.envelope, self.services[target], None)
        except KeyError:
            pass

        try:
            name, meth = target.split('.')[-2:]
            return self._request_class(
                request.envelope, self.services[name], meth)
        except (ValueError, KeyError):
            pass

        raise UnknownServiceError, "Unknown service %s" % target

    def getProcessor(self, request):
        """
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

        @param request: The AMF request.
        @type request: L{Envelope<remoting.Envelope>}

        @return: The AMF response.
        @rtype: L{Envelope<remoting.Envelope>}
        """
        raise NotImplementedError

    def authenticateRequest(self, username, password):
        """
        Processes an authentication request. If no authenticator is supplied,
        then authentication succeeds.

        @return: Returns a C{bool} based on the result of authorisation.
        @rtype: C{bool}
        """
        if self.authenticator is None:
            return True

        return self.authenticator(username, password) == True

from glob import glob
import sys, types, os.path

thismodule = None

for name, mod in sys.modules.iteritems():
    if not isinstance(mod, types.ModuleType):
        continue

    if not hasattr(mod, '__file__'):
        continue

    if mod.__file__ == __file__:
        thismodule = (name, mod)

        break

class LazyImporter(object):
    module = '.'.join(thismodule[0].split('.')[:-1])

    def __init__(self, module_name):
        self.__name__ = module_name

    def __getattr__(self, name):
        full_import_name = '%s.%s' % (LazyImporter.module, self.__name__)
        __import__(full_import_name)
        mod = sys.modules[full_import_name]
        setattr(sys.modules[LazyImporter.module], self.__name__, mod)

        self.__dict__.update(mod.__dict__)

        return getattr(mod, name)

for f in glob(os.path.join(os.path.dirname(thismodule[1].__file__), '*gateway.py')):
    name = f.split('/')[-1].split('.py')[0]
    localname = name.split('gateway', 1)[0]

    if localname == '':
        continue

    importer = LazyImporter(name)
    sys.modules['%s.%s' % (thismodule[0], localname)] = importer
    setattr(sys.modules[thismodule[0]], localname, importer)

del thismodule, f, importer, localname, name
