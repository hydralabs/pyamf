*******
  UDP
*******

.. topic:: Introduction

   This page describes how to setup the UDP example application
   using `Adobe AIR 2.0`_, PyAMF and Twisted_.

   Adobe AIR 2.0 now support `UDP sockets`_ allowing you to send
   and receive messages using the Universal Datagram Protocol (UDP).
   The example application also enumerates the list of hardware
   and software network interfaces available on the client computer.

.. contents::
 
Download
========

#. Download and install the `Adobe AIR 2 Runtime`_. Also download the
   Adobe AIR 2 SDK if you want to modify and compile the application.

#. Grab the example from SVN with::

     svn export http://svn.pyamf.org/trunk/doc/tutorials/examples/actionscript/udp udp-example
     cd udp-example/python

   Alternatively, if you just want to have a look, you can browse_ the example online.


Server
======

**Note**: Make sure you have Twisted_ >= 2.5 installed.

The UDP server for the Adobe Flash Player starts on
localhost:55555 when you launch the `development server`_:

.. code-block:: bash

    python server.py

You should see something like::

    Registered alias 'org.pyamf.examples.air.udp.vo.HelloWorld' for class 'HelloWorld'
    Server started listening on port 55555


Client
======

AIR
---

After you started the server you can simply install the `AIR file`_, launch it and
it will show you're connected to localhost:55555, i.e.:

.. image:: images/udp-overview.png

The server terminal window shows it receiving and echoing back the `HelloWorld`
instances::

    Registered alias 'org.pyamf.examples.air.udp.vo.HelloWorld' for class 'HelloWorld'
    Server started listening on port 55555
    received <HelloWorld msg='UDP message' time=2009-12-28 19:36:53.370000 /> from 192.168.0.3:55554
    received <HelloWorld msg='UDP message' time=2009-12-28 19:36:57.418000 /> from 192.168.0.3:55554
    received <HelloWorld msg='UDP message' time=2009-12-28 19:37:01.418000 /> from 192.168.0.3:55554
    received <HelloWorld msg='UDP message' time=2009-12-28 19:37:05.417000 /> from 192.168.0.3:55554
    received <HelloWorld msg='UDP message' time=2009-12-28 19:37:09.417000 /> from 192.168.0.3:55554

Drag the window or resize it by dragging any of the sides or corners:

.. image:: images/udp-resize.png

Right-click for the fullscreen and always on top options:

.. image:: images/udp-options.png


.. _Adobe AIR 2.0: http://labs.adobe.com/technologies/air2
.. _Adobe AIR 2 Runtime: http://labs.adobe.com/downloads/air2.html
.. _Twisted: http://twistedmatrix.com
.. _UDP sockets: http://help.adobe.com/en_US/FlashPlatform/beta/reference/actionscript/3/flash/net/DatagramSocket.html
.. _browse: http://dev.pyamf.org/browser/trunk/doc/tutorials/examples/actionscript/udp
.. _development server: http://dev.pyamf.org/browser/trunk/doc/tutorials/examples/actionscript/udp/python/server.py
.. _AIR file: http://dev.pyamf.org/browser/trunk/doc/tutorials/examples/actionscript/udp/air/deploy/udp.air
