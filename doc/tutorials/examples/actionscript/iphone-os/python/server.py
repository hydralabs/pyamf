#!/usr/bin/python
#
# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.

"""
iPhone example server.

@see: U{IPhoneOSExample<http://pyamf.org/wiki/IPhoneOSExample>} wiki page.

@since: 0.4
"""                                                             

import os
import pyamf
from sqlite3 import dbapi2 as sqlite

class AddressService(object):
    
    def getContacts(self):
        self.contacts = []
        
        db = sqlite.connect(os.path.expanduser('~') + "/Library/AddressBook/AddressBook.sqlitedb")
        cursor = db.cursor()
        cursor.execute("select first, last from ABPerson where first is not null order by first")
        for first, last in cursor.fetchall():
            self.contacts.append({"first": first, "last": last})
        cursor.close()
        db.close()

        return self.contacts

class IPhoneOSExample:
    def __init__(self, application):
        self.app = application
    
    def __call__(self, environ, start_response):
        if environ['REQUEST_METHOD'] == 'GET' and environ['PATH_INFO'] == '/':
            start_response('200 OK', [('Content-Type', 'application/x-shockwave-flash')])
            return open('../flex/deploy/IPhoneOSExample.swf')
        
        return self.app(environ, start_response)

services = {
    'addressbook': AddressService()
}

if __name__ == '__main__':
    from pyamf.remoting.gateway.wsgi import WSGIGateway
    from wsgiref import simple_server
 
    gw = WSGIGateway(services)
    app = IPhoneOSExample(gw)
    
    httpd = simple_server.WSGIServer(
        ('localhost', 8000),
        simple_server.WSGIRequestHandler,
    )

    httpd.set_app(app)

    print "Running iPhone AMF gateway on http://localhost:8000"

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
