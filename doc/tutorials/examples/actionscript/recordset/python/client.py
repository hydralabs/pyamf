# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.


from optparse import OptionParser
from pyamf.remoting.client import RemotingService


parser = OptionParser()
parser.add_option("-p", "--port", default=8000,
    dest="port", help="port number [default: %default]")
parser.add_option("--host", default="localhost",
    dest="host", help="host address [default: %default]")
(options, args) = parser.parse_args()


url = 'http://%s:%d' % (options.host, int(options.port))
client = RemotingService(url)
service = client.getService('service')

print service.getLanguages()
