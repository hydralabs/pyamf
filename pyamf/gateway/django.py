# -*- encoding: utf8 -*-
#
# Copyright (c) 2007 The PyAMF Project. All rights reserved.
# 
# Arnar Birgisson
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
from pyamf import remoting

# import django workaround for module name
import sys
thismodule = sys.modules['django']
del sys.modules['django']
real_django = __import__('django')
sys.modules['real_django'] = real_django
sys.modules['django'] = thismodule
from real_django.http import HttpResponse, HttpResponseNotAllowed
from real_django.core.urlresolvers import get_mod_func

def DjangoGateway(request, gateway):
    """
    A Django generic view that reads an AMF remoting request from the POST body and responds.

    This gateway instance is used to dispatch the remoting requests.

    @type request:
    @param request: Remoting request.
    @param gateway:
    @type gateway: Instance of L{BaseGateway<pyamf.gateway.BaseGateway>} or a qualified
    string to such an instance that will be imported.

    @raise HttpResponseNotAllowed: Only the POST request method is allowed.
    @return: Response to remoting request.
    @rtype:
    """

    # Import gateway if it is a string (similar to Django's urlconf)
    if not isinstance(gateway, pyamf.gateway.BaseGateway):
        gateway = gateway.encode('ascii')
        mod_name, var_name = get_mod_func(gateway)
        if var_name != '':
            gateway = getattr(__import__(mod_name, {}, {}, ['']), var_name)

    if request.method == 'POST':
        response = HttpResponse()
        context = pyamf._get_context(pyamf.AMF0)()

        amfrequest = remoting.decode(request.raw_post_data, context)
        amfresponse = remoting.Envelope(amfrequest.amfVersion, amfrequest.clientType)

        processor = gateway.getProcessor(amfrequest)
        for name, message in amfrequest:
            amfresponse[name] = processor(message)
        stream = remoting.encode(amfresponse, context)

        response['Content-Type'] = remoting.CONTENT_TYPE
        response['Content-Length'] = str(len(stream))
        response.write(stream.getvalue())
    else:
        response = HttpResponseNotAllowed(['POST'])

    return response
