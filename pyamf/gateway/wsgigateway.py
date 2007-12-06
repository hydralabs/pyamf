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
WSGI server implementation.

@see: U{WSGI homepage (external)<http://wsgi.org>}

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import pyamf
from pyamf import remoting, gateway

__all__ = ['WSGIGateway']

class WSGIGateway(gateway.BaseGateway):
    """
    U{WSGI<http://wsgi.org>} Remoting Gateway.
    """

    def getResponse(self, request):
        """
        Processes the AMF request, returning an AMF response.

        @param request: The AMF Request.
        @type request: L{Envelope<remoting.Envelope>}
        @rtype: L{Envelope<remoting.Envelope>}
        @return: The AMF Response.
        """
        response = remoting.Envelope(request.amfVersion, request.clientType)
        processor = self.getProcessor(request)

        for name, message in request:
            response[name] = processor(message)

        return response

    def badRequestMethod(self, environ, start_response):
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
            response = self.getResponse(request)
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
            ('Content-Type', gateway.CONTENT_TYPE),
            ('Content-Length', str(len(response))),
        ])

        return [response]
