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
Django Remoting gateway.

@see: U{Django homepage (external)<http://djangoproject.org>}

@author: U{Arnar Birgisson<mailto:arnarbi@gmail.com>}

@since: 0.1.0
"""

import pyamf
from pyamf import remoting, gateway

# import django workaround for module name
import sys, imp, os, os.path

idx = []

if '' in sys.path:
    idx.append((sys.path.index(''), ''))
    sys.path.remove('')

cwd = os.getcwd()

for name, mod in sys.modules.iteritems():
    if not name.endswith('django') or mod is None:
        continue

    if __file__ == mod.__file__:
        if name != 'django':
            os.chdir(os.path.abspath(os.path.dirname(__file__)))
            sys.modules['django'] = mod

        break

del name, mod

t = imp.find_module('django', sys.path)
imp.load_module('django', None, t[1], t[2])

for x in idx:
    sys.path.insert(x[0], x[1])

os.chdir(cwd)

del idx, imp, sys, os, cwd, t
# end import hack

from django.http import HttpResponse, HttpResponseNotAllowed
from django.core.urlresolvers import get_mod_func

__all__ = ['DjangoGateway']

class DjangoGateway(gateway.BaseGateway):
    """
    An instance of this class is suitable as a Django view.

    An example usage would be through urlconf::

        from django.conf.urls.defaults import *

        urlpatterns = patterns('',
            (r'^gateway/', 'yourproject.yourapp.gateway.gw_instance'),
        )

    where C{yourproject.yourapp.gateway.gw_instance} refers to an
    instance of this class.
    """

    def getResponse(self, request):
        """
        Processes the AMF request, returning an AMF response.

        @param request: The AMF Request.
        @type request: L{remoting.Envelope}
        @rtype: L{remoting.Envelope}
        @return: The AMF Response.
        """
        response = remoting.Envelope(request.amfVersion, request.clientType)
        processor = self.getProcessor(request)

        for name, message in request:
            response[name] = processor(message)

        return response

    def __call__(self, request):
        """
        Processes & dispatches the request.

        @param request: The HTTPRequest object
        @type request: U{HTTPRequest<django.http.HTTPRequest>}
        @return The response to the request
        @rtype U{HTTPResponse<django.http.HTTPResponse>}
        """
        if request.method != 'POST':
            return HttpResponseNotAllowed(['POST'])

        context = pyamf.get_context(pyamf.AMF0)
        stream = None
        http_response = HttpResponse(content_type=gateway.CONTENT_TYPE)

        # Decode the request
        try:
            request = remoting.decode(request.raw_post_data, context)
        except pyamf.DecodeError:
            return HttpResponse(status=400)

        # Process the request
        try:
            response = self.getResponse(request)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            return HttpResponseServerError()

        # Encode the response
        try:
            stream = remoting.encode(response, context)
        except pyamf.EncodeError:
            return HttpResponseServerError('Unable to encode the response')

        buf = stream.getvalue()
        http_response['Content-Length'] = str(len(buf))
        http_response.write(buf)

        return http_response
