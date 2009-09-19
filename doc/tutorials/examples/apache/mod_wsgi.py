import sys
import logging

sys.path.append('/usr/src/pyamf/')
sys.path.append('/var/www/myApp/')

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s'
)

from pyamf.remoting.gateway.wsgi import WSGIGateway


def echo(data):
   return data


services = {
   'echo': echo,
   # Add other exposed functions here
}

application = WSGIGateway(services, logger=logging, debug=True)
