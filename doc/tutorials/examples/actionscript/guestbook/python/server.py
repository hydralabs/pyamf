# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.

"""
Guestbook example server.

@see: U{GuestbookExample<http://pyamf.org/wiki/GuestbookExample>} wiki page.

@since: 0.3
"""   


import os.path
import ConfigParser

from twisted.internet import reactor
from twisted.web import server as _server, static, resource
from twisted.enterprise import adbapi

from pyamf.remoting.gateway.twisted import TwistedGateway

from guestbook import GuestBookService


port = 8080

cfg = ConfigParser.SafeConfigParser()
cfg.read('settings.cfg')

root = resource.Resource()
gw = TwistedGateway({'guestbook': GuestBookService(adbapi.ConnectionPool('MySQLdb',
                    host=cfg.get('db','host'), user=cfg.get('db','user'),
                    passwd=cfg.get('db','password'), db=cfg.get('db','database'),
                    cp_reconnect=True))}, expose_request=False)

root.putChild('gateway', gw)
root.putChild('crossdomain.xml', static.File(os.path.join(os.getcwd(),
    os.path.dirname(__file__), 'crossdomain.xml'), defaultType='application/xml'))

server = _server.Site(root)
