# -*- encoding: utf8 -*-
#
# Copyright (c) 2007 The PyAMF Project. All rights reserved.
# 
# Thijs Triemstra
# Nick Joyce
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
Server/client implementations for PyAMF.

@author: Thijs Triemstra
@author: Nick Joyce

@since: 0.1.0
"""

import sys, traceback

from pyamf import remoting

class BaseGateway(object):
    """
    Generic remoting gateway class.
    """

    def __init__(self, services):
        """
        @param services: Initial services
        @type services: dict
        """
        self.services = {}

        for name, service in services.iteritems():
            self.addService(service, name)

    def addService(self, service, name=None):
        """
        Adds a service to the gateway.

        @param service: The service to add to the gateway
        @type service: callable or a class instance
        @param name: The name of the service
        @type name: str
        """
        if name is None:
            # TODO: include the module in the name
            name = service.__class__.__name__

        if name in self.services.keys():
            raise remoting.RemotingError("Service %s already exists" % name)

        self.services[name] = service

    def removeService(self, service):
        """
        Removes a service from the gateway.

        @param service: The service to remove from the gateway
        @type service: callable or a class instance
        """
        self.services.popitem(service)

    def getTarget(self, target):
        """
        Returns a callable based on the target
        
        @param target: The target to retrieve
        @type target: str
        @rettype callable
        """
        try:
            obj = self.services[target]
            meth = None
        except KeyError:
            try:
                name, meth = target.rsplit('.', 1)
                obj = self.services[name]
            except KeyError:
                raise remoting.RemotingError("Unknown target %s" % target)

        if not callable(obj):
            raise TypeError("Not callable")

        return obj

    def save_request(self, body, stream):
        """
        Write AMF request to disk.
        """
        fname = 'request_' + str(self.request_number) + ".amf"
        x = open(fname, 'wb')
        try:
            x.write(body)
            x.write('=' * 80)
            x.write(stream.getvalue())
        except:
            pass
        finally:
            x.close()
        
    def get_error_response(self, (cls, e, tb)):
        """
        Call traceback and error details.

        @param cls: Class
        @type cls: callable or a class instance
        @param e: 
        @type e: 
        @param tb: 
        @type tb:
        """
        details = traceback.format_exception(cls, e, tb)

        return dict(
            code='SERVER.PROCESSING',
            level='Error',
            description='%s: %s' % (cls.__name__, e),
            type=cls.__name__,
            details=''.join(details),
        )

    def getProcessor(self, request):
        """
        
        """
        if 'DescribeService' in request.headers:
            return NotImplementedError

        return self.processRequest

    def processRequest(self, request):
        """
        Processes a request.

        @param request: The request to be processed
        @type request: L{remoting.Message}
        @return The response to the request
        @rettype L{remoting.Message}
        """
        func = self.getTarget(request.target)
        response = remoting.Message(None, None, None, None)

        try:
            response.body = func(*request.body)
            response.status = remoting.STATUS_OK
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            response.body = self.get_error_response(sys.exc_info())
            response.status = remoting.STATUS_ERROR

        return response

    def getResponse(self, request):
        """
        Returns the response to the request. Any implementing gateway must 
        define this function
        
        @param request: The AMF request
        @type request: L{remoting.Envelope}
        """
        raise NotImplementedError
