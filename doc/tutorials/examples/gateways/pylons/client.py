import logging
	
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s'
)

from pyamf.remoting.client import RemotingService

client = RemotingService('http://127.0.0.1:5000/gateway')
service = client.getService('myservice')
echo = service.echo('Hello World!')

logging.debug(echo) 
