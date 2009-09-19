import logging
import wsgiref.handlers

from google.appengine.ext import webapp

from pyamf.remoting.gateway.google import WebAppGateway


class MainPage(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('Hello, webapp World!')


def echo(data):
    return data


services = {
    'myservice.echo': echo,
}


def main():
    gateway = WebAppGateway(services, logging=logger, debug=True)
    application_paths = [('/', gateway), ('/helloworld', MainPage)]
    application = webapp.WSGIApplication(application_paths, debug=True)

    wsgiref.handlers.CGIHandler().run(application)