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
U{Twisted<http://twistedmatrix.com>} client example.
"""

from twisted.web import client

import pyamf
from pyamf import remoting, ClientTypes, Context

endPoint = 'http://localhost:8000'

def handleResult(data):
    result = remoting.decode(data)
    # Loop through result(s).
    for res in result:
        print "Response:", res
    reactor.stop()

def handleError(failure):
    print "Error:", failure.getErrorMessage()
    reactor.stop()

if __name__ == "__main__":
    from twisted.internet import reactor

    context = Context()
    response = remoting.Message(None, None, None, None)
    response.body = 'yoooo'
    response.status = remoting.STATUS_OK

    env = remoting.Envelope(pyamf.AMF0, ClientTypes.FlashCom)
    env['echo'] = response
    
    # Send a request to echo and send as only 
    # parameter 'myParameter'.
    data = remoting.encode(env, context).getvalue()

    # Send request.
    postRequest = client.getPage(
        endPoint,
        method='POST',
        headers={'Content-Type': remoting.CONTENT_TYPE,
                 'Content-Length': len(data)},
        postdata=data)
    
    # Handle result.
    postRequest.addCallback(handleResult).addErrback(handleError)
    
    print "Started Twisted client for PyAMF with endpoint: " + endPoint
    reactor.run()
