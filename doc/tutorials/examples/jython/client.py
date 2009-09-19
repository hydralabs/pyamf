import logging

from pyamf.remoting.client import RemotingService
from pyamf.remoting import RemotingError

url = 'http://localhost:8080/pyamf'
client = RemotingService(url, logger=logging, debug=True)
service = client.getService('my_service')

try:
    print service.echo('Hello World!')
except RemotingError, e:
    print e