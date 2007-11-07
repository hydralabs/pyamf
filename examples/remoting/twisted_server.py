# -*- encoding: utf8 -*-
#
# Copyright (c) 2007 The PyAMF Project. All rights reserved.
# 
# Thijs Triemstra
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

"""
Twisted Remoting server example.
"""

from pyamf import remoting
from pyamf.gateway.twisted import TwistedGateway
from twisted.web import http

def handlePost(request):
    # Get header content type.
    contentType = request.getHeader('Content-Type')
    # Respond to AMF calls.
    if contentType == remoting.CONTENT_TYPE:
        # Request data from the client.
        data = request.content.getvalue()
        # Decode AMF request.
        req = remoting.decode(data)
        print req        
        # Add AMF header content type.
        request.setHeader('Content-Type', remoting.CONTENT_TYPE)
        # Returns serialized AMF in a StringIO.
        response = remoting.encode(req)
        # Write response data back to the client.
        request.write(response)
    else:
        # Return blank HTML page for non-AMF calls.
        request.setHeader('Content-Type', 'text/html')
    
class FunctionHandledRequest(http.Request):
    pageHandlers = {
        '/': handlePost,
        }

    def process(self):
        """
        """
        if self.pageHandlers.has_key(self.path):
            handler = self.pageHandlers[self.path]
            handler(self)
        else:
            self.setResponseCode(http.NOT_FOUND)
            self.write("<h1>Not Found</h1>Sorry, no such page.")
        self.finish()
    
class MyHttp(http.HTTPChannel):
    requestFactory = FunctionHandledRequest

class MyHttpFactory(http.HTTPFactory):
    protocol = MyHttp
    
def echo(data):
    return data

if __name__ == '__main__':
    services = {
        'echo': echo
    }

    gw = TwistedGateway(services)
    port = 8000
    print "Started PyAMF Remoting Gateway for Twisted on port", port

    from twisted.internet import reactor
    reactor.listenTCP(port, MyHttpFactory())
    reactor.run()
