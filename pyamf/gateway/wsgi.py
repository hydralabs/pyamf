# -*- encoding: utf8 -*-
#
# Copyright (c) 2007 The PyAMF Project. All rights reserved.
# 
# Nick Joyce
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
U{WSGI<http://wsgi.org>} Server implementation.
"""

# Heavily borrowed from Flashticle http://osflash.org/flashticle

import sys, traceback
from types import ClassType

import pyamf
from pyamf import remoting, gateway
from pyamf.util import BufferedByteStream, hexdump

__all__ = ['WSGIGateway']

class WSGIGateway(gateway.BaseGateway):
    """
    U{WSGI<http://wsgi.org>} Remoting Gateway.
    """
    #: Number of requests from clients.
    request_number = 0

    def get_request_body(self, environ):
        """
        Read input data stream.

        @type environ:
        @param environ: 
        """
        return environ['wsgi.input'].read(int(environ['CONTENT_LENGTH']))
 
    def __call__(self, environ, start_response):
        """
        
        @type environ:
        @param environ:
        @type start_response:
        @param start_response: 
        """
        self.request_number += 1

        body = self.get_request_body(environ)
        
        context = pyamf.Context()
        request = remoting.decode(body, context)
        response = remoting.Envelope(request.amfVersion, request.clientType)

        processor = self.getProcessor(request)

        for name, message in request:
            response[name] = processor(message)

        stream = remoting.encode(response, context)

        start_response('200 OK', [
            ('Content-Type', remoting.CONTENT_TYPE),
            ('Content-Length', str(stream.tell())),
        ])

        self.save_request(body, stream)

        return [stream.getvalue()]
