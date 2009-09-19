import base64

from pyamf.remoting.client import RemotingService

gw = RemotingService('http://demo.pyamf.org/gateway/recordset')

gw.addHTTPHeader('Set-Cookie', 'sessionid=QT3cUmACNeKQo5oPeM0')
gw.removeHTTPHeader('Set-Cookie')

username = 'admin'
password = 'admin'
auth = base64.encodestring('%s:%s' % (username, password))[:-1]

gw.addHTTPHeader("Authorization", "Basic %s" % auth)