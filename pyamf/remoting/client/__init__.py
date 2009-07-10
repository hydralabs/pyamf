# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.

"""
Remoting client implementation.

@since: 0.1.0
"""

import httplib
import urlparse

import pyamf
from pyamf import remoting

#: Default AMF client type.
#: @see: L{ClientTypes<pyamf.ClientTypes>}
DEFAULT_CLIENT_TYPE = pyamf.ClientTypes.Flash6

#: Default user agent is C{PyAMF/x.x.x}.
DEFAULT_USER_AGENT = 'PyAMF/%s' % '.'.join(map(lambda x: str(x),
    pyamf.__version__))

HTTP_OK = 200


def convert_args(args):
    if args == (tuple(),):
        return []
    else:
        return [x for x in args]


class ServiceMethodProxy(object):
    """
    Serves as a proxy for calling a service method.

    @ivar service: The parent service.
    @type service: L{ServiceProxy}
    @ivar name: The name of the method.
    @type name: C{str} or C{None}

    @see: L{ServiceProxy.__getattr__}
    """

    def __init__(self, service, name):
        self.service = service
        self.name = name

    def __call__(self, *args):
        """
        Inform the proxied service that this function has been called.
        """

        return self.service._call(self, *args)

    def __str__(self):
        """
        Returns the full service name, including the method name if there is
        one.
        """
        service_name = str(self.service)

        if self.name is not None:
            service_name = '%s.%s' % (service_name, self.name)

        return service_name


class ServiceProxy(object):
    """
    Serves as a service object proxy for RPC calls. Generates
    L{ServiceMethodProxy} objects for method calls.

    @see: L{RequestWrapper} for more info.

    @ivar _gw: The parent gateway
    @type _gw: L{RemotingService}
    @ivar _name: The name of the service
    @type _name: C{str}
    @ivar _auto_execute: If set to C{True}, when a service method is called,
        the AMF request is immediately sent to the remote gateway and a
        response is returned. If set to C{False}, a L{RequestWrapper} is
        returned, waiting for the underlying gateway to fire the
        L{execute<RemotingService.execute>} method.
    """

    def __init__(self, gw, name, auto_execute=True):
        self._gw = gw
        self._name = name
        self._auto_execute = auto_execute

    def __getattr__(self, name):
        return ServiceMethodProxy(self, name)

    def _call(self, method_proxy, *args):
        """
        Executed when a L{ServiceMethodProxy} is called. Adds a request to the
        underlying gateway. If C{_auto_execute} is set to C{True}, then the
        request is immediately called on the remote gateway.
        """
        request = self._gw.addRequest(method_proxy, *args)

        if self._auto_execute:
            response = self._gw.execute_single(request)

            # XXX nick: What to do about Fault objects here?
            return response.body

        return request

    def __call__(self, *args):
        """
        This allows services to be 'called' without a method name.
        """
        return self._call(ServiceMethodProxy(self, None), *args)

    def __str__(self):
        """
        Returns a string representation of the name of the service.
        """
        return self._name


class RequestWrapper(object):
    """
    A container object that wraps a service method request.

    @ivar gw: The underlying gateway.
    @type gw: L{RemotingService}
    @ivar id: The id of the request.
    @type id: C{str}
    @ivar service: The service proxy.
    @type service: L{ServiceProxy}
    @ivar args: The args used to invoke the call.
    @type args: C{list}
    """

    def __init__(self, gw, id_, service, *args):
        self.gw = gw
        self.id = id_
        self.service = service
        self.args = args

    def __str__(self):
        return str(self.id)

    def setResponse(self, response):
        """
        A response has been received by the gateway
        """
        # XXX nick: What to do about Fault objects here?
        self.response = response
        self.result = self.response.body

        if isinstance(self.result, remoting.ErrorFault):
            self.result.raiseException()

    def _get_result(self):
        """
        Returns the result of the called remote request. If the request has not
        yet been called, an C{AttributeError} exception is raised.
        """
        if not hasattr(self, '_result'):
            raise AttributeError("'RequestWrapper' object has no attribute 'result'")

        return self._result

    def _set_result(self, result):
        self._result = result

    result = property(_get_result, _set_result)


class RemotingService(object):
    """
    Acts as a client for AMF calls.

    @ivar url: The url of the remote gateway. Accepts C{http} or C{https}
        as valid schemes.
    @type url: C{str}
    @ivar requests: The list of pending requests to process.
    @type requests: C{list}
    @ivar request_number: A unique identifier for tracking the number of
        requests.
    @ivar amf_version: The AMF version to use.
        See L{ENCODING_TYPES<pyamf.ENCODING_TYPES>}.
    @type amf_version: C{int}
    @ivar referer: The referer, or HTTP referer, identifies the address of the
        client. Ignored by default.
    @type referer: C{str}
    @ivar client_type: The client type. See L{ClientTypes<pyamf.ClientTypes>}.
    @type client_type: C{int}
    @ivar user_agent: Contains information about the user agent (client)
        originating the request. See L{DEFAULT_USER_AGENT}.
    @type user_agent: C{str}
    @ivar connection: The underlying connection to the remoting server.
    @type connection: C{httplib.HTTPConnection} or C{httplib.HTTPSConnection}
    @ivar headers: A list of persistent headers to send with each request.
    @type headers: L{HeaderCollection<pyamf.remoting.HeaderCollection>}
    @ivar http_headers: A dict of HTTP headers to apply to the underlying
        HTTP connection.
    @type http_headers: L{dict}
    @ivar strict: Whether to use strict AMF en/decoding or not.
    @type strict: C{bool}
    """

    def __init__(self, url, amf_version=pyamf.AMF0, client_type=DEFAULT_CLIENT_TYPE,
                 referer=None, user_agent=DEFAULT_USER_AGENT, strict=False,
                 logger=None):
        self.logger = logger
        self.original_url = url
        self.requests = []
        self.request_number = 1

        self.user_agent = user_agent
        self.referer = referer
        self.amf_version = amf_version
        self.client_type = client_type
        self.headers = remoting.HeaderCollection()
        self.http_headers = {}
        self.strict = strict

        self._setUrl(url)

    def _setUrl(self, url):
        """
        @param url: Gateway URL.
        @type url: C{str}
        @raise ValueError: Unknown scheme.
        """
        self.url = urlparse.urlparse(url)
        self._root_url = urlparse.urlunparse(['', ''] + list(self.url[2:]))

        port = None
        hostname = None

        if hasattr(self.url, 'port'):
            if self.url.port is not None:
                port = self.url.port
        else:
            if ':' not in self.url[1]:
                hostname = self.url[1]
                port = None
            else:
                sp = self.url[1].split(':')

                hostname, port = sp[0], sp[1]
                port = int(port)

        if hostname is None:
            if hasattr(self.url, 'hostname'):
                hostname = self.url.hostname

        if self.url[0] == 'http':
            if port is None:
                port = httplib.HTTP_PORT

            self.connection = httplib.HTTPConnection(hostname, port)
        elif self.url[0] == 'https':
            if port is None:
                port = httplib.HTTPS_PORT

            self.connection = httplib.HTTPSConnection(hostname, port)
        else:
            raise ValueError('Unknown scheme')

        location = '%s://%s:%s%s' % (self.url[0], hostname, port, self.url[2])

        if self.logger:
            self.logger.info('Connecting to %s' % location)
            self.logger.debug('Referer: %s' % self.referer)
            self.logger.debug('User-Agent: %s' % self.user_agent)

    def addHeader(self, name, value, must_understand=False):
        """
        Sets a persistent header to send with each request.

        @param name: Header name.
        @type name: C{str}
        @param must_understand: Default is C{False}.
        @type must_understand: C{bool}
        """
        self.headers[name] = value
        self.headers.set_required(name, must_understand)

    def addHTTPHeader(self, name, value):
        """
        Adds a header to the underlying HTTP connection.
        """
        self.http_headers[name] = value

    def removeHTTPHeader(self, name):
        """
        Deletes an HTTP header.
        """
        del self.http_headers[name]

    def getService(self, name, auto_execute=True):
        """
        Returns a L{ServiceProxy} for the supplied name. Sets up an object that
        can have method calls made to it that build the AMF requests.

        @param auto_execute: Default is C{True}.
        @type auto_execute: C{bool}
        @raise TypeError: C{string} type required for C{name}.
        @rtype: L{ServiceProxy}
        """
        if not isinstance(name, basestring):
            raise TypeError('string type required')

        return ServiceProxy(self, name, auto_execute)

    def getRequest(self, id_):
        """
        Gets a request based on the id.

        @raise LookupError: Request not found.
        """
        for request in self.requests:
            if request.id == id_:
                return request

        raise LookupError("Request %s not found" % id_)

    def addRequest(self, service, *args):
        """
        Adds a request to be sent to the remoting gateway.
        """
        wrapper = RequestWrapper(self, '/%d' % self.request_number,
            service, *args)

        self.request_number += 1
        self.requests.append(wrapper)

        if self.logger:
            self.logger.debug('Adding request %s%r' % (wrapper.service, args))

        return wrapper

    def removeRequest(self, service, *args):
        """
        Removes a request from the pending request list.

        @raise LookupError: Request not found.
        """
        if isinstance(service, RequestWrapper):
            if self.logger:
                self.logger.debug('Removing request: %s' % (
                    self.requests[self.requests.index(service)]))
            del self.requests[self.requests.index(service)]

            return

        for request in self.requests:
            if request.service == service and request.args == args:
                if self.logger:
                    self.logger.debug('Removing request: %s' % (
                        self.requests[self.requests.index(request)]))
                del self.requests[self.requests.index(request)]

                return

        raise LookupError("Request not found")

    def getAMFRequest(self, requests):
        """
        Builds an AMF request L{Envelope<pyamf.remoting.Envelope>} from a
        supplied list of requests.

        @param requests: List of requests
        @type requests: C{list}
        @rtype: L{Envelope<pyamf.remoting.Envelope>}
        """
        envelope = remoting.Envelope(self.amf_version, self.client_type)

        if self.logger:
            self.logger.debug('AMF version: %s' % self.amf_version)
            self.logger.debug('Client type: %s' % self.client_type)

        for request in requests:
            service = request.service
            args = list(request.args)

            envelope[request.id] = remoting.Request(str(service), args)

        envelope.headers = self.headers

        return envelope

    def _get_execute_headers(self):
        headers = self.http_headers.copy()

        headers.update({
            'Content-Type': remoting.CONTENT_TYPE,
            'User-Agent': self.user_agent
        })

        if self.referer is not None:
            headers['Referer'] = self.referer

        return headers

    def execute_single(self, request):
        """
        Builds, sends and handles the response to a single request, returning
        the response.

        @param request:
        @type request:
        @rtype:
        """
        if self.logger:
            self.logger.debug('Executing single request: %s' % request)
        body = remoting.encode(self.getAMFRequest([request]), strict=self.strict)

        if self.logger:
            self.logger.debug('Sending POST request to %s' % self._root_url)
        self.connection.request('POST', self._root_url,
            body.getvalue(),
            self._get_execute_headers()
        )

        envelope = self._getResponse()
        self.removeRequest(request)

        return envelope[request.id]

    def execute(self):
        """
        Builds, sends and handles the responses to all requests listed in
        C{self.requests}.
        """
        body = remoting.encode(self.getAMFRequest(self.requests), strict=self.strict)

        if self.logger:
            self.logger.debug('Sending POST request to %s' % self._root_url)

        self.connection.request('POST', self._root_url,
            body.getvalue(),
            self._get_execute_headers()
        )

        envelope = self._getResponse()

        for response in envelope:
            request = self.getRequest(response[0])
            response = response[1]

            request.setResponse(response)

            self.removeRequest(request)

    def _getResponse(self):
        """
        Gets and handles the HTTP response from the remote gateway.

        @raise RemotingError: HTTP Gateway reported error status.
        @raise RemotingError: Incorrect MIME type received.
        """
        if self.logger:
            self.logger.debug('Waiting for response...')

        http_response = self.connection.getresponse()

        if self.logger:
            self.logger.debug('Got response status: %s' % http_response.status)
            self.logger.debug('Content-Type: %s' % http_response.getheader('Content-Type'))

        if http_response.status != HTTP_OK:
            if self.logger:
                self.logger.debug('Body: %s' % http_response.read())

            if hasattr(httplib, 'responses'):
                raise remoting.RemotingError("HTTP Gateway reported status %d %s" % (
                    http_response.status, httplib.responses[http_response.status]))

            raise remoting.RemotingError("HTTP Gateway reported status %d" % (
                http_response.status,))

        content_type = http_response.getheader('Content-Type')

        if content_type != remoting.CONTENT_TYPE:
            if self.logger:
                self.logger.debug('Body = %s' % http_response.read())

            raise remoting.RemotingError("Incorrect MIME type received. (got: %s)" % content_type)

        content_length = http_response.getheader('Content-Length')
        bytes = ''

        if self.logger:
            self.logger.debug('Content-Length: %s' % content_length)
            self.logger.debug('Server: %s' % http_response.getheader('Server'))

        if content_length in (None, ''):
            bytes = http_response.read()
        else:
            bytes = http_response.read(int(content_length))

        if self.logger:
            self.logger.debug('Read %d bytes for the response' % len(bytes))

        response = remoting.decode(bytes, strict=self.strict)

        if self.logger:
            self.logger.debug('Response: %s' % response)

        if remoting.APPEND_TO_GATEWAY_URL in response.headers:
            self.original_url += response.headers[remoting.APPEND_TO_GATEWAY_URL]

            self._setUrl(self.original_url)
        elif remoting.REPLACE_GATEWAY_URL in response.headers:
            self.original_url = response.headers[remoting.REPLACE_GATEWAY_URL]

            self._setUrl(self.original_url)

        if remoting.REQUEST_PERSISTENT_HEADER in response.headers:
            data = response.headers[remoting.REQUEST_PERSISTENT_HEADER]

            for k, v in data.iteritems():
                self.headers[k] = v

        http_response.close()

        return response

    def setCredentials(self, username, password):
        """
        Sets authentication credentials for accessing the remote gateway.
        """
        self.addHeader('Credentials', dict(userid=unicode(username),
            password=unicode(password)), True)
