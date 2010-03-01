**********************
  Google App Engine 
**********************

.. image:: images/appengine-logo.gif

.. topic:: Introduction

   This howto will show you how to use a PyAMF application (0.3.1 or newer)
   with Google App Engine.

   `Google App Engine`_ (GAE) lets you run your web applications on Google's
   infrastructure for free. You can serve your app using a free domain name
   on the appspot.com domain, or use `Google Apps`_ to serve it from your
   own domain.

   GAE applications are implemented using Python 2.5.2. The `runtime
   environment`_ includes the full Python language and most_
   of the Python standard library, including :doc:`django`.

.. contents::

Prerequisites
=============

Before you can start using GAE you need to download and install:

- Python 2.5 or newer for your platform from `the Python website`_. Users of
  Mac OS X 10.5 or newer already have Python 2.5 or newer installed.
- `Google App Engine SDK`_
- :doc:`PyAMF 0.3.1 or newer</community/download>`


Create Project
==============

Start a new GAE project:

- Create a new folder for your project
- Copy ``main.py``, ``app.yaml``, and ``index.yaml`` from
  ``google_appengine/new_project_template`` to your new folder. On a Mac
  you can find it under ``/usr/local``
- Move the ``pyamf`` folder from your unpacked ``PyAMF-0.x.x`` folder
  to the root folder of the new GAE project


Your folder structure of your project should now look something like this:

.. code-block:: bash

   + MyProject
     - main.py
     - app.yaml
     - index.yaml
     - pyamf


Application
===========

You can setup your application using the ``WebAppGateway`` or the
``WSGIGateway``.


WebApp Gateway
--------------

The ``WebAppGateway`` class allows a GAE application to handle AMF requests
on the root URL and other standard HTTP requests on another URL
(``/helloworld`` in the example below).

The ``main.py`` module tells GAE what code to launch. Modify it for PyAMF:

.. literalinclude:: ../examples/gateways/appengine/webapp.py
   :linenos:


WSGI Gateway
------------

If you don't want to use the pure ``google.appengine`` approach as
described above, you can also use the ``WSGIGateway`` by modifying your
``main.py`` like this:

.. literalinclude:: ../examples/gateways/appengine/wsgi.py
   :linenos:


Start the server
================

Run this command from your application folder:

.. code-block:: bash

   dev_appserver.py --debug --address=localhost --port=8080 .


Test the application
====================

Python
------

To test the gateway you can use a Python AMF client like this:

.. literalinclude:: ../examples/gateways/appengine/client.py
   :linenos:


Flash
-----

Create a new Adobe Flash document and place a ``TextField`` on
the stage. Make it dynamic in the Properties pane, and give it
the instance name ``output``. Then, paste the following code
into the Actions pane:

.. literalinclude:: ../examples/gateways/appengine/flash.as
   :language: actionscript
   :linenos:

Run ``Debug`` > ``Debug`` movie to test PyAMF with Google App
Engine! Other examples for Flex etc can be found on the
Examples page.


Future Plans
============

This method works fine as long as the app is only going to be
the gateway. It would be beneficial, however, to have the SWF
running on the same instance.

If you have suggestions join us on the IRC channel or use the
mailinglist.


Useful Resources
================

http://aralbalkan.com/1307
   Aral Balkan - Building Flash applications with Google App Engine.

:doc:`../gateways/django`
   PyAMF integration with Django.

:doc:`../actionscript/bytearray`
   ByteArray example using Django and Flex.

http://blog.pyamf.org/archives/pyamf-and-google-app-engine
   Related post on PyAMF blog.

http://pyamf.appspot.com/punit
   Run the PyAMF test suite on the Google App Engine.


.. _Google App Engine: http://code.google.com/appengine
.. _Google Apps: http://www.google.com/a/help/intl/en/index.html
.. _runtime environment: http://code.google.com/appengine/docs/python
.. _most: http://code.google.com/appengine/docs/python/purepython.html
.. _the Python website: http://python.org/download
.. _Google App Engine SDK: http://code.google.com/appengine/downloads.html