# Copyright (c) 2009 The PyAMF Project.
# See LICENSE for details.

"""
Python ByteArray example.

@since: 0.5
""" 

import os
from optparse import OptionParser

from gateway import images_root

from pyamf.amf3 import ByteArray
from pyamf.remoting.client import RemotingService


# parse commandline options
parser = OptionParser()
parser.add_option("-p", "--port", default=8000,
    dest="port", help="port number [default: %default]")
parser.add_option("--host", default="127.0.0.1",
    dest="host", help="host address [default: %default]")
(options, args) = parser.parse_args()


# define gateway
url = 'http://%s:%d' % (options.host, int(options.port))
server = RemotingService(url)

# get list of snapshots
snapshots = server.getService('getSnapshots')()

print "Found %d snapshot(s):" % (len(snapshots))

for snapshot in snapshots:
    print "\t%s:\t%s" % (snapshot['name'], snapshot['url'])    

# save snapshot
image = os.path.join(images_root, 'django-logo.jpg')
file = open(image, 'r').read()

snapshot = ByteArray()
snapshot.write(file)

save_snapshot = server.getService('ByteArray.saveSnapshot')
saved = save_snapshot(snapshot)

print "Saved snapshot:\n\t%s:\t%s" % (saved['name'], saved['url'])