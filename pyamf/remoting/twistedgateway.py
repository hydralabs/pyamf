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
from twisted.web import resource, server, client, http

import pyamf
from pyamf import remoting
from pyamf.remoting import gateway

__all__ = ['TwistedGateway']

class TwistedGateway(gateway.BaseGateway, resource.Resource):
    """
    Twisted Remoting gateway for C{twisted.web}
    """

    def _finaliseRequest(self, request, status, content, mimetype='text/plain'):
        """
        Finalizes the request
        """
        request.code = http.BAD_REQUEST
        request.code_message = http.RESPONSES[request.code]

        request.setHeader("Content-Type", mimetype)
        request.setHeader("Content-Length", str(len(content)))

        request.write(content)
        request.finish()

    def render_POST(self, request):
        """
        Read remoting request from client.

        @type request: The HTTP Request
        @param request: C{twisted.web.http.Request}
        """
        def handleDecodeError(failure):
            import sys, traceback

            body = "400 Bad Request\n\nThe request body was unable to " \
                "be successfully decoded.\n\nTraceback:\n\n%s" % (
                    traceback.format_exception(*sys.exc_info()))

            self._finaliseRequest(request, 400, body)

        def handleProcessError(failure):
            import sys, traceback

            body = "500 Internal Server Error\n\nThe request was unable to " \
                "be successfully processed.\n\nTraceback:\n\n%s" % (
                    traceback.format_exception(*sys.exc_info()))

            self._finaliseRequest(request, 500, body)

        request.content.seek(0, 0)

        context = pyamf.get_context(pyamf.AMF0)
        d = threads.deferToThread(remoting.decode,
            request.content.read(), context)

        # The request was unable to be decoded
        d.addErrback(handleDecodeError)

        def process_request(amf_request):
            d = self.getResponse(request, amf_request)

            # Something went wrong processing the request
            d.addErrback(handleProcessError)
            d.addCallback(self.sendResponse, request, context)

        # Process the request
        d.addCallback(process_request)

        return server.NOT_DONE_YET

    def sendResponse(self, amf_response, request, context):
        def cb(result):
            self._finaliseRequest(request, 200,
                result.getvalue(), remoting.CONTENT_TYPE)

        def eb(failure):
            body = "500 Internal Server Error\n\nThere was an error encoding" \
                " the response.\n\nTraceback:\n\n%s" % (
            self._finaliseRequest(request, 500, body)

        d = threads.deferToThread(remoting.encode, amf_response, context)

        d.addErrback(eb).addCallback(cb)

    def getResponse(self, http_request, amf_request):
        """
        @param http_request: The underlying HTTP Request
        @type http_request: C{twisted.web.http.Request}
        @param amf_request: The AMF Request
        @type amf_request: L{remoting.Envelope}
        """
        response = remoting.Envelope(request.amfVersion, request.clientType)
        dl = []

        def cb(body):
            response[name] = body

        for name, message in request:
            processor = self.getProcessor(message)

            d = threads.deferToThread(processor, message).addCallback(cb)
            dl.append(d)

        def cb2(result):
            return response

        d = defer.DeferredList(dl)
        
        return d.addCallback(cb2)
