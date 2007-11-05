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
Simple Python echo server for Flash Remoting.

This example uses the U{WGSI<http://wsgi.org>} webserver.
"""

import pyamf
from pyamf.gateway.wsgi import Gateway
from wsgiref import simple_server

class RemoteClass(object):
    """
    This Python class is mapped to the clientside Actionscript class.

    TODO how do I access the clientside class name ('org.red5.server.webapp.echo.RemoteClass')?
    """
    pass

#: Map ActionScript class to Python class
pyamf.register_class(RemoteClass, 'org.red5.server.webapp.echo.RemoteClass')

def echo(data):
    """
    Return data back to the client.

    @type data:
    @param data: Decoded AS->Python data
    """
    return data

if __name__ == '__main__':
    #: Define remote calls from the Flash Player.
    services = {
        'echo': echo
    }

    gw = Gateway(services)
    port = 8000
    print "Started echo server on port", port
    
    httpd = simple_server.WSGIServer(
        ('',8000),
        simple_server.WSGIRequestHandler,
    )
    httpd.set_app(gw)
    httpd.serve_forever()
