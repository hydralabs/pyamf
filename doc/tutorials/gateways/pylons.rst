******************
  Pylons Project
******************

.. topic:: Introduction

   The `Pylons Project`_ is a collection of web application framework
   technologies. This tutorial describes how to setup a bare bones
   application with a remoting gateway exposing a method.

   **Note**: This tutorial provides examples for both Pyramid_ and the old
   `Pylons package`_ (versions 0.97-1.x). For new projects it is recommended
   to use the Pyramid package, see the `Pylons FAQ`_ for more information. 


.. contents::


Pyramid
=======

The Pyramid_ package supports extensibility through add-ons. For this tutorial
we need RPC support for AMF_ which is available in the `pyramid_rpc`_ add-on.

Install_ the ``pyramid_rpc`` package:

  .. code-block:: bash

     $ easy_install pyramid_rpc


Example
-------

1. Create a new Python script called ``server.py`` with the following:

  .. literalinclude:: ../examples/gateways/pylons/pyramid_gateway.py
     :linenos:

  You can easily expose more functions by adding them to the ``services`` dictionary
  given to ``PyramidGateway``.


2. Fire up the web server with:

  .. code-block:: bash

     $ python server.py

  That should print something like:

  .. code-block:: bash

     serving on 0.0.0.0:8080 view at http://127.0.0.1:8080


3. To test the gateway you can use a Python AMF client like this:

  .. literalinclude:: ../examples/gateways/pylons/pyramid_client.py
     :linenos:


Pylons
======

1. Create a new Pylons project with:

  .. code-block:: bash

     $ paster create -t pylons testproject


2. ``cd`` into it and create a controller:

  .. code-block:: bash

     $ cd testproject
     $ paster controller gateway


3. Replace the contents of ``testproject/controllers/gateway.py`` with the following:

  .. literalinclude:: ../examples/gateways/pylons/pylons_gateway.py
     :linenos:

  You can easily expose more functions by adding them to the dictionary given to ``WSGIGateway``.
  You can also create a totally different controller and expose it under another gateway URL.


4. Add the controller to the routing map, open ``testproject/config/routing.py`` and look for the line:

  .. code-block:: python

     # CUSTOM ROUTES HERE

  Just below that line, add a mapping to the controller you created earlier. This maps URLs with
  the prefix 'gateway' to the AMF gateway.
  
  .. code-block:: python
  
     map.connect('/gateway', controller='gateway')


5. Import the remoting gateway, open ``testproject/lib/helpers.py`` and add:

  .. code-block:: python
    
     from pyamf.remoting.gateway.wsgi import WSGIGateway


6. Copy a ``crossdomain.xml`` file into ``testproject/public``:

  .. literalinclude:: ../examples/gateways/pylons/crossdomain.xml
     :language: xml
     :linenos:


7. Fire up the web server with:

  .. code-block:: bash

     $ paster serve --reload development.ini

  That should print something like:

  .. code-block:: bash

     Starting subprocess with file monitor
     Starting server in PID 4247.
     serving on 0.0.0.0:5000 view at http://127.0.0.1:5000


8. To test the gateway you can use a Python AMF client like this:

  .. literalinclude:: ../examples/gateways/pylons/pylons_client.py
     :linenos:


.. _Pylons Project: http://pylonsproject.org/
.. _Pyramid: http://docs.pylonsproject.org/docs/pyramid.html
.. _Pylons package: http://docs.pylonsproject.org/docs/pylons.html
.. _pyramid_rpc: http://docs.pylonsproject.org/projects/pyramid_rpc/dev/
.. _Pylons FAQ: http://docs.pylonsproject.org/faq/pylonsproject.html
.. _AMF: http://docs.pylonsproject.org/projects/pyramid_rpc/dev/amf.html
.. _Install: http://docs.pylonsproject.org/projects/pyramid_rpc/dev/#installation
