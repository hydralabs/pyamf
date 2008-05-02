# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Gateway for Google App Engine.

This gateway allows you to expose functions in Google App Engine web
applications to AMF clients and servers.

@see: U{Google App Engine homepage (external)
<http://code.google.com/appengine>}

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.3.1
"""

import sys, os.path

try:
    sys.path.remove(os.path.dirname(os.path.abspath(__file__)))
except ValueError:
    pass

google = __import__('google')
__import__('google.appengine.ext.webapp')

webapp = google.appengine.ext.webapp

import pyamf
from pyamf import remoting
from pyamf.remoting import gateway

__all__ = ['WebAppGateway']

class WebAppGateway(webapp.RequestHandler, gateway.BaseGateway):
    """
    Google App Engine Remoting Gateway.
    """
    __name__ = None

    def __init__(self, *args, **kwargs):
        gateway.BaseGateway.__init__(self, *args, **kwargs)

    def getResponse(self, request):
        """
        Processes the AMF request, returning an AMF response.

        @param request: The AMF Request.
        @type request: L{Envelope<pyamf.remoting.Envelope>}
        @rtype: L{Envelope<pyamf.remoting.Envelope>}
        @return: The AMF Response.
        """
        response = remoting.Envelope(request.amfVersion, request.clientType)

        for name, message in request:
            processor = self.getProcessor(message)
            response[name] = processor(message, http_request=self.request)

        return response

    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.error(405)
        self.response.out.write("405 Method Not Allowed\n\n" + \
            "To access this PyAMF gateway you must use POST requests " + \
            "(%s received)" % self.request.method)

    def post(self):
        body = self.request.body_file.read()
        stream = None

        context = pyamf.get_context(pyamf.AMF0)

        # Decode the request
        try:
            request = remoting.decode(body, context)
        except pyamf.DecodeError:
            self.logger.debug(gateway.format_exception())

            response = "400 Bad Request\n\nThe request body was unable to " \
                "be successfully decoded."

            if self.debug:
                response += "\n\nTraceback:\n\n%s" % gateway.format_exception()

            self.error(400)
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.out.write(response)

            return

        # Process the request
        try:
            response = self.getResponse(request)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.logger.debug(gateway.format_exception())

            response = "500 Internal Server Error\n\nThe request was " \
                "unable to be successfully processed."

            if self.debug:
                response += "\n\nTraceback:\n\n%s" % gateway.format_exception()

            self.error(500)
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.out.write(response)

            return

        # Encode the response
        try:
            stream = remoting.encode(response, context)
        except pyamf.EncodeError:
            self.logger.debug(gateway.format_exception())

            response = "500 Internal Server Error\n\nThe request was " \
                "unable to be encoded."

            if self.debug:
                response += "\n\nTraceback:\n\n%s" % gateway.format_exception()

            self.error(500)
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.out.write(response)

            return

        response = stream.getvalue()

        self.response.headers['Content-Type'] = remoting.CONTENT_TYPE
        self.response.headers['Content-Length'] = str(len(response))
        self.response.out.write(response)

    def __call__(self, *args, **kwargs):
        return self
