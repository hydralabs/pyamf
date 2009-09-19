import logging
import wsgiref.handlers

from pyamf.remoting.gateway.wsgi import WSGIGateway


def echo(data):
    return data


services = {
    'myservice.echo': echo,
}


def main():
    gateway = WSGIGateway(services, logger=logging, debug=True)
    wsgiref.handlers.CGIHandler().run(gateway)


if __name__ == '__main__':
    main()