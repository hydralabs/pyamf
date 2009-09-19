************
  Buildbot 
************


.. image:: images/buildbot-logo.png


.. topic:: Introduction

   This document describes how to setup the AMF gateway for
   `Buildbot <http://buildbot.net>`_ that can be used by other programs
   to query the build status.

   There will be live demo available on our BuildBot's
   `homepage <http://buildbot.pyamf.org>`_.

   Note: this page is a work in progress (#298,
   `#293 <http://buildbot.net/trac/ticket/293>`_)


Download
========

Grab the Flex and Python example clients from SVN with:

.. code-block:: bash

   svn export http://svn.pyamf.org/examples/branches/buildbot-example-298/buildbot buildbot-example

Alternatively, if you just want to have a look, you can
`browse the example source online
<http://pyamf.org/browser/examples/branches/buildbot-example-298/buildbot>`_.


Buildbot configuration
======================

Install buildbot:

.. code-block:: bash

   easy_install buildbot


Create a new buildmaster:

.. code-block:: bash

   buildbot create-master test


`Download <http://buildbot.net/trac/raw-attachment/ticket/293/amf.py>`_
the Buildbot AMF gateway and put it in your
buildmaster root folder:

.. code-block:: bash

   cd test
   wget http://buildbot.net/trac/raw-attachment/ticket/293/amf.py


Modify your buildmaster configuration file called
``master.cfg`` and enable the AMF gateway in the
WebStatus view:


.. code-block:: python
   :linenos:

   from buildbot.status import html
   from amf import AMFServer

   public = html.WebStatus(http_port="8080", allowForce=False)
   public.putChild('gateway', AMFServer())
   c['status'].append(public)


Start your buildmaster:

.. code-block:: bash

   buildbot start .


Check if the AMF gateway is working by browsing to
http://localhost:8080/gateway. That should return
something like this:

.. code-block:: bash

   Method Not Allowed

   Your browser approached me (at /gateway) with the method "GET". I only allow the method POST here.


Client
======

Python
------

When you run the Python AMF client by default it connects
to http://localhost:8080/gateway and prints the status of
the builder(s):

.. code-block:: bash

   2009-07-18 21:02:36,319 INFO  Connecting to http://localhost:8080/gateway
   2009-07-18 21:02:36,363 INFO  Total builders: 1
   2009-07-18 21:02:36,363 INFO  Builder status:
   2009-07-18 21:02:36,374 INFO  	buildbot-full       None


Flash Player
------------

The easiest is to copy the contents of the Flex deploy folder
into your <buildmaster home>/public_html folder. That allows
you to run the application on http://localhost:8080/amf.html.