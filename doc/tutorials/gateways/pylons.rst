******************
  Pylons Project
******************

.. image:: images/pylons-logo.png

.. topic:: Introduction

   The `Pylons Project`_ is a collection of web application framework
   technologies. This tutorial describes how to setup a bare bones
   application with a remoting gateway exposing a method.

   **Note**: This tutorial provides examples for both Pyramid_ and the legacy
   `Pylons package`_ (versions 0.97-1.x). For new projects it is encouraged
   to use the Pyramid package, see the `Pylons FAQ`_ for more information. 


.. contents::


Pyramid
=======

Pyramid_ is a small, fast, down-to-earth Python web application development
framework. It is developed as part of the `Pylons Project`_.

Example
-------

1. Create a new virtual environment using the virtualenv_ tool:

  .. code-block:: bash

     $ virtualenv --no-site-packages pyramid_amf_env


2. The Pyramid_ package supports extensibility through add-ons. For this tutorial
   we need AMF support which is available in the `pyramid_rpc`_ add-on.

  Install the ``pyramid``, ``pyramid_rpc`` and ``pyamf`` packages:

  .. code-block:: bash

     $ cd pyramid_amf_env
     $ bin/easy_install pyramid pyramid_rpc pyamf


  For more detailed instructions, refer to the Pyramid `installation documentation`_.


3. Create a new Pyramid project (called ``pyamf_tutorial`` in this example):

  .. code-block:: bash

     $ bin/paster create -t pyramid_starter pyamf_tutorial


4. Install the project into the enviroment:

  .. code-block:: bash

     $ cd pyamf_tutorial
     $ ../bin/python setup.py develop


5. Replace the contents of ``pyamf_tutorial/views.py`` with the following:

  .. literalinclude:: ../examples/gateways/pylons/pyramid_gateway.py
     :linenos:

  You can easily expose more functions by adding them to the ``services`` dictionary
  given to ``PyramidGateway``. Also see the `pyramid_rpc documentation`_.


6. Add the view to the routing map, open ``pyamf_tutorial/__init__.py`` and look for the line:

  .. code-block:: python

     config.add_static_view('static', 'pyamf_tutorial:static')

  Just above that line, configure the route to the view you created earlier.

  .. code-block:: python
  
     config.add_view('pyamf_tutorial.views.echoGateway', name='gateway')


7. Fire up the web server with:

  .. code-block:: bash

     $ ../bin/paster serve development.ini

  That should print something like:

  .. code-block:: bash

     Starting server in PID 16601.
     serving on 0.0.0.0:6543 view at http://127.0.0.1:6543


8. To test the gateway you can use a Python AMF client like this:

  .. literalinclude:: ../examples/gateways/pylons/pyramid_client.py
     :linenos:



Pylons (0.97-1.x)
=================

This section of the tutorial covers the legacy `Pylons package`_.

Example
-------

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
.. _pyramid_rpc documentation: http://docs.pylonsproject.org/projects/pyramid_rpc/dev/amf.html
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _installation documentation: http://docs.pylonsproject.org/projects/pyramid/1.1/narr/install.html#installing-chapter
