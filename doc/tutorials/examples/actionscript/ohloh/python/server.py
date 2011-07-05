#!/usr/bin/python
#
# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

"""
Ohloh API example server for Flash.

@since: 0.3.1
"""

import logging
from optparse import OptionParser
from wsgiref import simple_server

from pyamf.remoting.gateway.wsgi import WSGIGateway

from ohloh import UserAccount


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s'
)

parser = OptionParser()
parser.add_option("-p", "--port", default=8000,
    dest="port", help="port number [default: %default]")
parser.add_option("--host", default="localhost",
    dest="host", help="host address [default: %default]")
parser.add_option("--api-key", default="123456789",
    dest="api_key", help="Ohloh API key [default: %default]")
(options, args) = parser.parse_args()

ohloh = UserAccount(options.api_key)
services = {
    'ohloh.account': ohloh.getAccount
}

host = options.host
port = int(options.port)
gw = WSGIGateway(services, logger=logging)

httpd = simple_server.WSGIServer((host, port),
    simple_server.WSGIRequestHandler,
)

httpd.set_app(gw)

print "Running Ohloh API AMF gateway on http://%s:%d" % (host, port)

try:
    httpd.serve_forever()
except KeyboardInterrupt:
    pass
