# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Twisted server implementation.

@see: U{Twisted homepage (external)<http://twistedmatrix.com>}

@author: U{Thijs Triemstra<mailto:info@collab.nl>}
@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

from twisted.internet import defer, threads
from twisted.web import resource, server

import pyamf
from pyamf import remoting
from pyamf.remoting import gateway, amf0, amf3

__all__ = ['TwistedGateway']

class AMF0RequestProcessor(amf0.RequestProcessor):
    """
    A Twisted friendly implementation of
    L{amf0.RequestProcessor<pyamf.remoting.amf0.RequestProcessor>}
    """

    def __call__(self, request, service_wrapper=lambda service_request, *body: service_request(*body)):
        """
        Calls the underlying service method.

        @return: A C{Deferred} that will contain the AMF Response.
        @rtype: C{twisted.internet.defer.Deferred}
        """
        try:
            service_request = self.gateway.getServiceRequest(request, request.target)
        except gateway.UnknownServiceError, e:
            return defer.succeed(self.buildErrorResponse(request))

        response = remoting.Response(None)
        deferred_response = defer.Deferred()

        def eb(failure):
            deferred_response.callback(self.buildErrorResponse(request,
                (failure.type, failure.value, failure.tb)))

            return failure

        def auth_cb(authd):
            if not authd:
                # authentication failed
                response.status = remoting.STATUS_ERROR
                response.body = remoting.ErrorFault(code='AuthenticationError',
                    description='Authentication failed')

                deferred_response.callback(response)

                return

            # authentication was successful
            d = defer.maybeDeferred(self._getBody, request, response,
                service_request, service_wrapper)

            def cb(result):
                response.body = result

                deferred_response.callback(response)

            d.addCallback(cb).addErrback(eb)

        # we have a valid service, now attempt authentication
        d = defer.maybeDeferred(self.authenticateRequest, request, service_request)
        d.addCallback(auth_cb)
        d.addErrback(eb)

        return deferred_response

class AMF3RequestProcessor(amf3.RequestProcessor):
    """
    A Twisted friendly implementation of
    L{amf3.RequestProcessor<pyamf.remoting.amf3.RequestProcessor>}
    """

    def __call__(self, request, **kwargs):
        """
        Calls the underlying service method.

        @return: A deferred that will contain the AMF Response.
        @rtype: C{Deferred<twisted.internet.defer.Deferred>}
        """
        amf_response = remoting.Response(None)
        ro_request = request.body[0]
        deferred_response = defer.Deferred()

        def cb(result):
            amf_response.body = result
            deferred_response.callback(amf_response)

            return result

        def eb(failure):
            deferred_response.callback(self.buildErrorResponse(ro_request,
                (failure.type, failure.value, failure.tb)))

            return failure

        d = defer.maybeDeferred(self._getBody, request, ro_request, kwargs.get('service_wrapper'))
        d.addCallback(cb).addErrback(eb)

        return deferred_response

class TwistedGateway(gateway.BaseGateway, resource.Resource):
    """
    Twisted Remoting gateway for C{twisted.web}.

    @ivar expose_request: Forces the underlying HTTP request to be the first
        argument to any service call.
    @type expose_request: C{bool}
    """

    allowedMethods = ('POST',)

    def __init__(self, *args, **kwargs):
        self.expose_request = kwargs.pop('expose_request', True)

        gateway.BaseGateway.__init__(self, *args, **kwargs)
        resource.Resource.__init__(self)

    def _finaliseRequest(self, request, status, content, mimetype='text/plain'):
        """
        Finalises the request.

        @param request: The HTTP Request.
        @type request: C{http.Request}
        @param status: The HTTP status code.
        @type status: C{int}
        @param content: The content of the response.
        @type content: C{str}
        @param mimetype: The MIME Type of the request.
        @type mimetype: C{str}
        """
        request.setResponseCode(status)

        request.setHeader("Content-Type", mimetype)
        request.setHeader("Content-Length", str(len(content)))

        request.write(content)
        request.finish()

    def render_POST(self, request):
        """
        Read remoting request from client.

        @type request: The HTTP Request.
        @param request: C{twisted.web.http.Request}
        """
        def handleDecodeError(failure):
            """
            Return HTTP 400 Bad Request.
            """
            import traceback
            body = "400 Bad Request\n\nThe request body was unable to " \
                "be successfully decoded.\n\nTraceback:\n\n%s" % (
                    traceback.format_exception(failure.type, failure.value, failure.tb))

            self._finaliseRequest(request, 400, body)

        request.content.seek(0, 0)
        context = pyamf.get_context(pyamf.AMF0)

        d = threads.deferToThread(remoting.decode, request.content.read(), context)

        def eb(failure):
            """
            Return 500 Internal Server Error.
            """
            import traceback
            body = "500 Internal Server Error\n\nThere was an error processing" \
                " the request.\n\nTraceback:\n\n%s" % traceback.format_exception(
                    failure.type, failure.value, failure.tb)

            self._finaliseRequest(request, 500, body)

            return request

        def cb(amf_request):
            x = self.getResponse(request, amf_request)

            x.addCallback(self.sendResponse, request, context).addErrback(eb)

            return amf_request

        # Process the request
        d.addCallback(cb).addErrback(handleDecodeError)

        return server.NOT_DONE_YET

    def sendResponse(self, amf_response, request, context):
        def cb(result):
            self._finaliseRequest(request, 200, result.getvalue(),
                remoting.CONTENT_TYPE)

            return request

        def eb(failure):
            import traceback
            body = "500 Internal Server Error\n\nThere was an error encoding" \
                " the response.\n\nTraceback:\n\n%s" % traceback.format_exception(
                    failure.type, failure.value, failure.tb)

            self._finaliseRequest(request, 500, body)

            return failure

        d = threads.deferToThread(remoting.encode, amf_response, context)

        d.addErrback(eb).addCallback(cb)

    def getProcessor(self, request):
        """
        Returns RequestProcessor.

        @param request: The AMF message.
        @type request: L{Request<pyamf.remoting.Request>}
        """
        if request.target == 'null':
            return AMF3RequestProcessor(self)

        return AMF0RequestProcessor(self)

    def getResponse(self, http_request, amf_request):
        """
        Processes the AMF request, returning an AMF response.
        
        @param http_request: The underlying HTTP Request
        @type http_request: C{twisted.web.http.Request}
        @param amf_request: The AMF Request.
        @type amf_request: L{Envelope<pyamf.remoting.Envelope>}
        """
        response = remoting.Envelope(amf_request.amfVersion, amf_request.clientType)
        dl = []

        def cb(body, name):
            response[name] = body

        kwargs = {}

        if self.expose_request:
            def wrapper(service_request, *body):
                return service_request(http_request, *body)

            kwargs.update({'service_wrapper': wrapper})

        for name, message in amf_request:
            processor = self.getProcessor(message)

            d = defer.maybeDeferred(processor, message, **kwargs)
            d.addCallback(cb, name)

            dl.append(d)

        def cb2(result):
            return response

        d = defer.DeferredList(dl)

        return d.addCallback(cb2)

    def authenticateRequest(self, service_request, username, password):
        """
        Processes an authentication request. If no authenticator is supplied,
        then authentication succeeds.

        @return: C{Deferred}.
        @rtype: C{twisted.internet.defer.Deferred}
        """
        authenticator = self.getAuthenticator(service_request)

        if authenticator is None:
            return defer.succeed(True)

        return defer.mayBeDeferred(authenticator, username, password)
