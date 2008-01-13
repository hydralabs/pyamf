# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
WSGI server implementation.

@see: U{WSGI homepage (external)<http://wsgi.org>}

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}
@since: 0.1.0
"""

import pyamf
from pyamf import remoting
from pyamf.remoting import gateway

__all__ = ['WSGIGateway']

class WSGIGateway(gateway.BaseGateway):
    """
    WSGI Remoting Gateway.
    """

    def __init__(self, *args, **kwargs):
        self.expose_environ = kwargs.pop('expose_environ', False)

        gateway.BaseGateway.__init__(self, *args, **kwargs)

    def getResponse(self, request, environ):
        """
        Processes the AMF request, returning an AMF response.

        @param request: The AMF Request.
        @type request: L{Envelope<pyamf.remoting.Envelope>}
        @rtype: L{Envelope<pyamf.remoting.Envelope>}
        @return: The AMF Response.
        """
        response = remoting.Envelope(request.amfVersion, request.clientType)

        kwargs = {}

        if self.expose_environ:
            def wrapper(service_request, *body):
                return service_request(environ, *body)

            kwargs.update({'service_wrapper': wrapper})

        for name, message in request:
            processor = self.getProcessor(message)
            response[name] = processor(message, **kwargs)

        return response

    def badRequestMethod(self, environ, start_response):
        """
        Return HTTP 400 Bad Request
        """
        response = "400 Bad Request\n\nTo access this PyAMF gateway you " \
            "must use POST requests (%s received)" % environ['REQUEST_METHOD']

        start_response('400 Bad Request', [
            ('Content-Type', 'text/plain'),
            ('Content-Length', str(len(response))),
        ])

        return [response]

    def __call__(self, environ, start_response):
        """
        @type environ:
        @param environ:
        @type start_response:
        @param start_response:

        @rtype: C{StringIO}
        @return: File-like object.
        """
        if environ['REQUEST_METHOD'] != 'POST':
            return self.badRequestMethod(environ, start_response)

        body = environ['wsgi.input'].read(int(environ['CONTENT_LENGTH']))
        stream = None

        context = pyamf.get_context(pyamf.AMF0)

        # Decode the request
        try:
            request = remoting.decode(body, context)
        except pyamf.DecodeError:
            import sys, traceback

            response = "400 Bad Request\n\nThe request body was unable to " \
                "be successfully decoded.\n\nTraceback:\n\n%s" % (
                    traceback.format_exception(*sys.exc_info()))

            start_response('400 Bad Request', [
                ('Content-Type', 'text/plain'),
                ('Content-Length', str(len(response))),
            ])

            return [response]

        # Process the request
        try:
            response = self.getResponse(request, environ)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            import sys, traceback

            response = "500 Internal Server Error\n\nThe request was " \
                "unable to be successfully processed.\n\nTraceback:\n\n%s" % (
                    traceback.format_exception(*sys.exc_info()))

            start_response('500 Internal Server Error', [
                ('Content-Type', 'text/plain'),
                ('Content-Length', str(len(response))),
            ])

            return [response]

        # Encode the response
        try:
            stream = remoting.encode(response, context)
        except pyamf.EncodeError:
            import sys, traceback

            response = "500 Internal Server Error\n\nThe request was " \
                "unable to be encoded.\n\nTraceback:\n\n%s" % (
                    traceback.format_exception(*sys.exc_info()))

            start_response('500 Internal Server Error', [
                ('Content-Type', 'text/plain'),
                ('Content-Length', str(len(response))),
            ])

            return [response]

        response = stream.getvalue()

        start_response('200 OK', [
            ('Content-Type', remoting.CONTENT_TYPE),
            ('Content-Length', str(len(response))),
        ])

        return [response]
