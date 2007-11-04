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

from pyamf import remoting, gateway
from pyamf.util import BufferedByteStream, hexdump

__all__ = ['Gateway']

class Gateway(object):
    request_number = 0

    def __init__(self, services):
        self.services = services

    def get_processor(self, request):
        if 'DescribeService' in request.headers:
            return NotImplementedError

        return self.process_message

    def get_target(self, target):
        try:
            obj = self.services[target]
            meth = None
        except KeyError:
            name, meth = target.encode('utf8').replace('/', '.').rsplit('.', 1)
            obj = self.services[name]

        if isinstance(obj, (type, ClassType)):
            obj = obj()

            return getattr(obj, meth)
        elif callable(obj):
            return obj

        raise ValueError("Unknown")

    def get_error_response(self, (cls, e, tb)):
        details = traceback.format_exception(cls, e, tb)

        return dict(
            code='SERVER.PROCESSING',
            level='Error',
            description='%s: %s' % (cls.__name__, e),
            type=cls.__name__,
            details=''.join(details),
        )

    def process_message(self, message):
        func = self.get_target(message.target)

        try:
            message.body = func(*message.body)
            message.status = remoting.STATUS_OK
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            message.body = self.get_error_response(sys.exc_info())
            message.status = remoting.STATUS_ERROR

    def get_request_body(self, environ):
        return environ['wsgi.input'].read(int(environ['CONTENT_LENGTH']))

    def __call__(self, environ, start_response):
        self.request_number += 1

        body = self.get_request_body(environ)
        #x = open('request_' + str(self.request_number), 'wb')
        #x.write(body)
        envelope = remoting.decode(body)
        processor = self.get_processor(envelope)

        for message in envelope:
            processor(message)

        stream = remoting.encode(envelope)

        start_response('200 OK', [
            ('Content-Type', gateway.CONTENT_TYPE),
            ('Content-Length', str(stream.tell())),
        ])
        #x.write('=' * 80)
        #x.write(stream.getvalue())
        #x.close()

        return [stream.getvalue()]
