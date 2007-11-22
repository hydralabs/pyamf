# -*- encoding: utf8 -*-
#
# Copyright (c) 2007 The PyAMF Project. All rights reserved.
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

"""
Simple Python echo test U{Twisted<http://twistedmatrix.com>} server for Flash Remoting.

You can use this example with the echo_test.swf client on the
U{EchoTest<http://pyamf.org/wiki/EchoTest>} wiki page.

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import pyamf
from pyamf.gateway.twisted import TwistedGateway

class RemoteClass(object):
    """
    This Python class is mapped to the clientside Actionscript class.
    """
    pass

class ExternalizableClass(object):
    pass

def read_ec(obj, input):
    assert input.readBoolean() == True
    assert input.readBoolean() == False
    assert input.readByte() == 0
    assert input.readByte() == -1
    assert input.readByte() == 1
    assert input.readByte() == 127
    assert input.readByte() == -127
    assert input.readDouble() == 1.0
    assert input.readFloat() == 2.0
    assert input.readInt() == 0
    assert input.readInt() == -1
    assert input.readInt() == 1
    input.readMultiByte(7, 'iso-8859-1')
    input.readMultiByte(14, 'utf8')
    assert input.readObject() == [1, 'one', 1.0]
    assert input.readShort() == 0
    assert input.readShort() == -1
    assert input.readShort() == 1
    assert input.readUnsignedInt() == 0
    assert input.readUnsignedInt() == 1
    assert input.readUTF() == "Hello world!"
    assert input.readUTFBytes(12) == "Hello world!"

def write_ec(obj, output):
    output.writeBoolean(True)
    output.writeBoolean(False)
    output.writeByte(0)
    output.writeByte(-1)
    output.writeByte(1)
    output.writeByte(127)
    output.writeByte(-127)
    output.writeDouble(1.0)
    output.writeFloat(2.0)
    output.writeInt(0)
    output.writeInt(-1)
    output.writeInt(1)
    output.writeMultiByte(u"\xe4\xf6\xfc\xc4\xd6\xdc\xdf", 'iso-8859-1')
    output.writeMultiByte(u"\xe4\xf6\xfc\xc4\xd6\xdc\xdf", 'utf8')
    output.writeObject([1, 'one', 1])
    output.writeShort(0)
    output.writeShort(-1)
    output.writeShort(1)
    output.writeUnsignedInt(0)
    output.writeUnsignedInt(1)
    output.writeUTF("Hello world!")
    output.writeUTFBytes("Hello world!")

#: Map ActionScript class to Python class
pyamf.register_class(RemoteClass, 'org.red5.server.webapp.echo.RemoteClass')
pyamf.register_class(ExternalizableClass, 'org.red5.server.webapp.echo.ExternalizableClass',
    write_func=write_ec, read_func=read_ec)

def echo(data):
    """
    Return data back to the client.

    @type data:
    @param data: Decoded AS->Python data
    """
    return data

if __name__ == '__main__':
    import os, os.path

    from twisted.internet import reactor
    from twisted.web import server, static, resource

    #: Define remote calls from the Flash Player.
    services = {
        'echo': echo
    }

    port = 8000
    gw = TwistedGateway(services)
    root = resource.Resource()
    
    root.putChild('', gw)
    root.putChild('/echo/gateway', gw)
    root.putChild('crossdomain.xml', static.File(os.path.join(
        os.getcwd(),
        os.path.dirname(os.path.dirname(__file__)),
        '../../crossdomain.xml'), defaultType='application/xml'))

    reactor.listenTCP(port, server.Site(root))
    reactor.run()
