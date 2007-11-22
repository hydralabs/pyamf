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
U{Django<http://djangoproject.org>} Remoting gateway.

@author: U{Arnar Birgisson<mailto:arnarbi@gmail.com>}

@since: 0.1.0
"""

import pyamf
from pyamf import remoting, gateway

# import django workaround for module name
import sys
_thismodule = sys.modules['django']
del sys.modules['django']
_real_django = __import__('django')
sys.modules['real_django'] = _real_django
sys.modules['django'] = _thismodule

from real_django.http import HttpResponse, HttpResponseNotAllowed
from real_django.core.urlresolvers import get_mod_func

__all__ = ['DjangoGateway']

class DjangoGateway(gateway.BaseGateway):
    """
    An instance of this class is suitable as a Django view.
    
    An example usage would be through urlconf::
    
        from django.conf.urls.defaults import *

        urlpatterns = patterns('',
            (r'^gateway/', 'yourpoject.yourapp.gateway.gw_instance'),
        )

    where C{yourpoject.yourapp.gateway.gw_instance} refers to an instance of this class.
    """
    
    def __call__(self, request):

        if request.method == 'POST':
            response = HttpResponse()

            context = pyamf.get_context(pyamf.AMF0)
            amfrequest = remoting.decode(request.raw_post_data, context)
            amfresponse = remoting.Envelope(amfrequest.amfVersion, amfrequest.clientType)

            processor = self.getProcessor(amfrequest)

            for name, message in amfrequest:
                amfresponse[name] = processor(message)

            stream = remoting.encode(amfresponse, context)

            response['Content-Type'] = remoting.CONTENT_TYPE
            response['Content-Length'] = str(len(stream))
            response.write(stream.getvalue())
        else:
            response = HttpResponseNotAllowed(['POST'])

        return response
