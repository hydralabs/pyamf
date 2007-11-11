# -*- encoding: utf8 -*-
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
WSGI Remoting example.

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}
"""

from pyamf.gateway.wsgi import WSGIGateway
from wsgiref import simple_server

def echo(data):
    return data

if __name__ == '__main__':
    services = {
        'echo': echo
    }

    gw = WSGIGateway(services)
    port = 8000
    print "Started PyAMF Remoting Gateway for WSGI on port", port

    httpd = simple_server.WSGIServer(
        ('',port),
        simple_server.WSGIRequestHandler,
    )
    httpd.set_app(gw)
    httpd.serve_forever()
