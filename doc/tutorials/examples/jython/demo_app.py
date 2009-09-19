import logging

def echo(data):
    return data

def handler(environ, start_response):
    from pyamf.remoting.gateway.wsgi import WSGIGateway

    services = {'my_service.echo': echo}
    gw = WSGIGateway(services, logger=logging, debug=True)

    return gw(environ, start_response)