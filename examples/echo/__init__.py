# -*- encoding: utf8 -*-
#
# Copyright (c) 2007 The PyAMF Project. All rights reserved.
# 
# Nick Joyce
# Thijs Triemstra
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
Echo client and server examples.

Support for:

 - U{Twisted<http://twistedmatrix.com>}
 - U{WSGI<http://wsgi.org>}

You can use this example with the echo_test.swf client on the
U{EchoTest<http://pyamf.org/wiki/EchoTest>} wiki page.

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}
@author: U{Thijs Triemstra<mailto:info@collab.nl>}

@since: 0.1.0
"""

import os, os.path

def run_wsgi_server(options, services):
    """
    Runs the AMF services using the
    L{WSGIGateway<pyamf.gateway.wsgi.WSGIGateway>}.

    @param options: commandline options
    @type options: dict
    @param services: List of services for the Flash gateway.
    @type services: dict
    @return: The function that will run the server.
    @rtype: callable
    """
    from pyamf.gateway.wsgi import WSGIGateway
    from wsgiref import simple_server

    gw = WSGIGateway(services, options.debug)

    httpd = simple_server.WSGIServer(
        ('',int(options.port)),
        simple_server.WSGIRequestHandler,
    )

    httpd.set_app(gw)

    return httpd.serve_forever

def run_twisted_server(options, services):
    """
    Runs the AMF services using the
    L{TwistedGateway<pyamf.gateway.twistedmatrix.TwistedGateway>}.

    @param options: commandline options
    @type options: dict
    @param services: List of services for the Flash gateway.
    @type services: dict
    @return: The function that will run the server.
    @rtype: callable
    """
    from twisted.internet import reactor
    from twisted.web import server, static, resource

    from pyamf.gateway.twisted import TwistedGateway

    gw = TwistedGateway(services, options.debug)
    root = resource.Resource()

    root.putChild('', gw)
    root.putChild('/gateway', gw)
    root.putChild('crossdomain.xml', static.File(os.path.join(
        os.getcwd(), os.path.dirname(__file__), '../crossdomain.xml'),
        defaultType='application/xml'))

    reactor.listenTCP(int(options.port), server.Site(root))

    return reactor.run

def run_server(name, options, services):
    """
    Starts the echo AMF server.

    @param options: commandline options
    @type options: dict
    @param services: List of services for the Flash gateway.
    @type services: dict
    """
    if options.type == 'wsgi':
        print "Started %s - WSGI Server on http://%s:%d" % (name, options.host, int(options.port))
        func = run_wsgi_server(options, services)
    elif options.type == 'twisted':
        print "Started %s - Twisted Server on http://%s:%d" % (name, options.host, int(options.port))
        func = run_twisted_server(options, services)

    func()

def run_twisted_client(options, service, result_func, fault_func):
    """
    Runs AMF services for a Twisted echo client.

    @param options: commandline options
    @type options: dict
    @param service: Target service on the AMF gateway.
    @type service: 
    @return: The function that will run the client.
    @rtype: callable
    """
    from twisted.internet import reactor
    from pyamf.gateway.twisted import TwistedClient

    client = TwistedClient(options, service, result_func, fault_func)
    client.send("Hello World!")
    
    return reactor.run

def run_client(name, options, service, result_func, fault_func):
    """
    Starts the echo AMF client.

    @param options: commandline options.
    @type options: dict
    @param service: Target service on the AMF gateway.
    @type service: dict
    """
    if options.type == 'twisted':
        print "Started %s - Twisted Client for http://%s:%d" % (name, options.host, int(options.port))
        func = run_twisted_client(options, service, result_func, fault_func)
        
    func()
    
def parse_args(args):
    """
    Parse commandline options.
    """
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option('-t', '--type', dest='type',
        choices=('wsgi', 'twisted',), default='wsgi',
        help='Determines which AMF gateway type to use')
    parser.add_option('-d', '--debug', action='store_true', dest='debug',
        default=False, help='Write AMF request and response to disk')
    parser.add_option('--host', dest='host', default='localhost',
                      help='The host address for the AMF gateway')
    parser.add_option('-p', '--port', dest='port', default=8000,
                      help='The port number the server uses')

    return parser.parse_args(args)
