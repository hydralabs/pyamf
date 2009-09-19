import logging
	
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s'
)

from pyamf.remoting.client import RemotingService

gw = RemotingService('http://127.0.0.1:8000/gateway/')
service = gw.getService('myservice', logger=logging, debug=True)

print service.echo('Hello World!')
