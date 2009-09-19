**********
  Swing 
**********

.. topic:: Introduction

    This howto describes how to setup the 
    `Swing <http://en.wikipedia.org/wiki/Swing_(Java)>`_
    example application using `Jython <http://jython.org>`_ 2.5
    and newer.


Download
========

Grab the example from SVN with:

.. code-block:: bash
 
   svn export http://svn.pyamf.org/examples/trunk/jython jython-example
   cd jython-example

Alternatively, if you just want to have a look, you can browse
the example `online <http://pyamf.org/browser/examples/trunk/jython>`_.


Run Application
===============

The Swing application contains a AMF client and server that
starts on http://localhost:8000 when you run the ``gui.py``
file:

.. code-block:: bash

  jython gui.py

Use the ``Start Server`` button to launch the server and make
AMF client calls using the ``Invoke Method`` button.

.. image:: images/swing-example.png