from django.conf.urls.defaults import *
import os

urlpatterns = patterns('',

    # AMF Remoting Gateway
    (r'^gateway/', 'pyamf.gateway.djangogateway.DjangoGateway', {'gateway': 'djangogateway.gateway.echoGateway'}),
    
    # Serve crossdomain.xml from the directory below __file__
    (r'^crossdomain.xml$', 'django.views.static.serve',
                {'document_root': os.path.abspath(os.path.join(os.path.dirname(__file__),'..')), 'path': 'crossdomain.xml'})
)
