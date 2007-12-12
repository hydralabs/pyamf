# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.


"""
Twisted server implementation.

@see: U{Twisted homepage (external)<http://twistedmatrix.com>}

@author: U{Thijs Triemstra<mailto:info@collab.nl>}
@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

from twisted.internet import defer, threads, reactor
from twisted.web import resource, server, client

import pyamf
from pyamf import remoting
from pyamf.remoting import gateway

__all__ = ['TwistedGateway', 'TwistedClient']

class ServiceRequest(gateway.ServiceRequest):
    """
    Remoting service request.
    """

    def authenticate(self, username, password):
        """
        Twisted implementation of L{ServiceRequest<gateway.ServiceRequest>}.

        @param username: Username.
        @type username: C{str}
        @param password: Password.
        @type password: C{str}

        @return: A Deferred which fires a callback containing the result
                 (a C{bool}) of the authentication.
        @rtype: Deferred
        """
        if self.service.authenticator is None:
            # The default is to allow anything through
            return defer.succeed(True)

        return defer.mayBeDeferred(
            self.service.authenticator, (username, password))

    def __call__(self, *args):
        return defer.maybeDeferred(self.service, self.method, args)

class TwistedGateway(gateway.BaseGateway, resource.Resource):
    """
    Twisted Remoting gateway.
    """
    _request_class = ServiceRequest

    def __init__(self, services):
        gateway.BaseGateway.__init__(self, services)
        resource.Resource.__init__(self)

    def getResponse(self, request):
        """
        @param request:
        @type request:
        """
        self.response = remoting.Envelope(request.amfVersion, request.clientType)

        processor = self.getProcessor(request)
        dl = []

        for name, message in request:
            def addToResponse(body):
                self.response[name] = body

            d = defer.maybeDeferred(processor, message
                ).addCallback(addToResponse)
            dl.append(d)

        return defer.DeferredList(dl)

    def processRequest(self, request):
        """
        @param request:
        @type request:
        """
        response = remoting.Message(None, None, None, None)

        service_request = self.getServiceRequest(request)
        # we have a valid service, now attempt authentication

        #self._authenticate(service_request, request).addCallback(handleAuth)
        # FIXME: what error to return here?

        def cb(result):
            """
            Create response to remoting request.

            @rtype:
            @return: Response
            """
            response.body = result
            response.status = remoting.STATUS_OK

            return response

        def eb(failure):
            """
            Create error response to remoting request.
            """
            response.body = self.getErrorResponse(failure)
            response.status = remoting.STATUS_ERROR

        return service_request(*request.body).addErrback(eb).addCallback(cb)

    def render_POST(self, request):
        """
        Read remoting request from client.

        @type request:
        @param request:
        @rtype:
        @return:
        """
        request.content.seek(0, 0)

        self.body = request.content.read()
        self.stream = None

        self.context = pyamf.get_context(pyamf.AMF0)

        threads.deferToThread(remoting.decode, self.body, self.context
            ).addCallback(self.getResponse
            ).addErrback(self._ebRender
            ).addCallback(self._cbRender, request)

        return server.NOT_DONE_YET

    def _cbRender(self, result, request):
        def finishRequest(result):
            request.setHeader("Content-Length", str(len(result)))
            request.write(result.getvalue())
            request.finish()

        threads.deferToThread(remoting.encode, self.response, self.context
            ).addErrback(self._ebRender).addCallback(finishRequest)

    def _ebRender(self, failure):
        print failure

class TwistedClient(client.HTTPPageGetter):
    """
    Twisted Remoting client.
    """

    def __init__(self, host, port, service, result_func, fault_func):
        """
        @param service:
        @type service:
        @param result_func:
        @type result_func:
        @param fault_func:
        @type fault_func:
        """
        self.host = host
        self.port = port
        self.service = service
        self.resultHandler = result_func
        self.faultHandler = fault_func

    def send(self, data):
        """
        """
        response = pyamf.remoting.Message(None, None, None, None)
        response.body = {'echo':data}
        response.status = pyamf.remoting.STATUS_OK

        env = pyamf.remoting.Envelope(pyamf.AMF0, pyamf.ClientTypes.FlashCom)
        env[self.service] = response

        print "Sending AMF request:", data

        data = pyamf.remoting.encode(env).getvalue()

        endPoint = 'http://' + self.host + ":" + str(self.port)

        postRequest = client.getPage(
            endPoint,
            method='POST',
            headers={'Content-Type': pyamf.remoting.CONTENT_TYPE,
                     'Content-Length': len(data)},
            postdata=data)

        postRequest.addCallback(self.getResult).addErrback(self.getError)

        reactor.run()

    def getResult(self, data):
        """
        """
        result = remoting.decode(data)
        self.resultHandler(result)
        reactor.stop()

    def getError(self, failure):
        """
        """
        self.faultHandler(failure)
        reactor.stop()

