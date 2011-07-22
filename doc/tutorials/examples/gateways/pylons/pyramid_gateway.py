import logging

from pyramid.config import Configurator
from pyramid_rpc.amfgateway import PyramidGateway

from paste.httpserver import serve


def echo(request, data):
    """
    This is a function that we will expose.
    """
    # echo data back to the client
    return data


services = {
    'myservice.echo': echo,
    # Add other exposed functions and classes here
}

echoGateway = PyramidGateway(services, logger=logging, debug=True)


if __name__ == '__main__':
    config = Configurator()
    config.add_view(echoGateway, name='gateway')
    app = config.make_wsgi_app()
    serve(app, host='0.0.0.0')
