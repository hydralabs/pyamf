# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Gateway for the Django framework.

This gateway allows you to expose functions in Django to AMF clients and
servers.

@see: U{Django homepage (external)<http://djangoproject.com>}

@author: U{Arnar Birgisson<mailto:arnarbi@gmail.com>}

@since: 0.1.0
"""

django = __import__('django')
http = django.http

import pyamf
from pyamf import remoting
from pyamf.remoting import gateway

__all__ = ['DjangoGateway']

class DjangoGateway(gateway.BaseGateway):
    """
    An instance of this class is suitable as a Django view.

    An example usage would be through C{urlconf}::

        from django.conf.urls.defaults import *

        urlpatterns = patterns('',
            (r'^gateway/', 'yourproject.yourapp.gateway.gw_instance'),
        )

    where C{yourproject.yourapp.gateway.gw_instance} refers to an instance of
    this class.

    @ivar expose_request: The standard Django view always has the request
        object as the first parameter. To disable this functionality, set this
        to C{False}.
    @type expose_request: C{bool}
    """

    def __init__(self, *args, **kwargs):
        kwargs['expose_request'] = kwargs.get('expose_request', True)

        gateway.BaseGateway.__init__(self, *args, **kwargs)

    def getResponse(self, http_request, request):
        """
        Processes the AMF request, returning an AMF response.

        @param http_request: The underlying HTTP Request.
        @type http_request: C{HTTPRequest<django.core.http.HTTPRequest>}
        @param request: The AMF Request.
        @type request: L{Envelope<pyamf.remoting.Envelope>}
        @rtype: L{Envelope<pyamf.remoting.Envelope>}
        @return: The AMF Response.
        """
        response = remoting.Envelope(request.amfVersion, request.clientType)

        for name, message in request:
            processor = self.getProcessor(message)
            response[name] = processor(message, http_request=http_request)

        return response

    def __call__(self, http_request):
        """
        Processes and dispatches the request.

        @param http_request: The C{HTTPRequest} object.
        @type http_request: C{HTTPRequest}
        @return: The response to the request.
        @rtype: C{HTTPResponse}
        """
        if http_request.method != 'POST':
            return http.HttpResponseNotAllowed(['POST'])

        context = pyamf.get_context(pyamf.AMF0)
        stream = None
        http_response = http.HttpResponse()

        # Decode the request
        try:
            request = remoting.decode(http_request.raw_post_data, context)
        except pyamf.DecodeError:
            self.logger.debug(gateway.format_exception())
            http_response.status_code = 400

            return http_response

        self.logger.debug("AMF Request: %r" % request)

        # Process the request
        try:
            response = self.getResponse(http_request, request)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.logger.debug(gateway.format_exception())

            return http.HttpResponseServerError()

        self.logger.debug("AMF Response: %r" % response)

        # Encode the response
        try:
            stream = remoting.encode(response, context)
        except pyamf.EncodeError:
            self.logger.debug(gateway.format_exception())

            return http.HttpResponseServerError('Unable to encode the response')

        buf = stream.getvalue()
        http_response['Content-Type'] = remoting.CONTENT_TYPE
        http_response['Content-Length'] = str(len(buf))
        http_response.write(buf)

        return http_response
