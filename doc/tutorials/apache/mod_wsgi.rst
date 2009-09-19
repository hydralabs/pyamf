*************
  mod_wsgi
*************

.. topic:: Introduction

   This tutorial shows you how to easily publish your PyAMF applications
   with the `Apache 2 <http://httpd.apache.org>`_ webserver and
   `mod_wsgi <http://modwsgi.org>`_. Mod_wsgi is an Apache module
   which can host any Python application which supports the Python
   `WSGI <http://wsgi.org>`_ interface. This was tested
   with Python 2.4.3, Apache 2.0.55, mod_wsgi 1.3 on Ubuntu 6.06.1 LTS.

   This tutorial assumes you already installed the Apache webserver
   running (on 192.168.1.100). Flash applications will be able to access
   your PyAMF remoting gateway on http://192.168.1.100/flashservices/gateway.


Create your PyAMF application
=============================

Create a folder for your application:

.. code-block:: bash

   mkdir /var/www/myApp

Create a startup file for your application in ``/var/www/myApp/startup.py``:

.. literalinclude:: ../examples/apache/mod_wsgi.py
    :linenos:

Make sure your Apache user (``www-data``) has access to your application
files.

This sample assumes you have a copy of the PyAMF source installed in
``/usr/src/pyamf`` but you can comment out line 4 if you installed
PyAMF in your Python's ``site-packages`` folder.


Setup Apache virtual host
=========================

Create a new virtual host or modify an existing one:

.. literalinclude:: ../examples/apache/mod_wsgi.vhost
    :language: apache
    :linenos:


Restart Apache
==============

That's it! Your Adobe Flash Player and AMF clients will now be able to
access your PyAMF application through http://192.168.1.100/flashservices/gateway. 


Useful Resources
================

http://code.google.com/p/modwsgi/wiki/ConfigurationGuidelines
   Configuration guidelines for mod_wsgi.

http://code.google.com/p/modwsgi/wiki/ConfigurationDirectives
    Configuration directives for mod_wsgi.
