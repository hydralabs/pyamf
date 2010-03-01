**********
  Client 
**********

.. topic:: Introduction

   PyAMF isn't just about the Adobe Flash Player talking to a Python
   backend, oh no. We have put together a client module which allows
   you to make AMF calls to an HTTP Gateway, whether that be PyAMF or
   `other AMF implementations`_. If you come from a Adobe Flash
   background, this API should feel very natural to you.

.. contents::

Examples
========

The examples below are working, so feel free to try this out right now.


Basic Example
-------------

This example connects to a AMF gateway running at
``http://demo.pyamf.org/gateway/recordset`` and invokes the remote Python
``getLanguages`` method that is mapped to ``service.getLanguages``.
The result is printed on stdout.

.. literalinclude:: ../examples/general/client/basic.py
    :linenos:


Authentication
--------------

Use ``setCredentials(username, password)`` to authenticate with an
AMF client:

.. literalinclude:: ../examples/general/client/authentication.py
    :linenos:


Logging
-------

Enable logging with a ``DEBUG`` level to log messages including the timestamp
and level name.

.. literalinclude:: ../examples/general/client/logging.py
    :linenos:


HTTP Headers
------------

You can modify the headers of the HTTP request using this convenient API:

.. literalinclude:: ../examples/general/client/headers.py
    :linenos:


Exception Handling
------------------

As of PyAMF 0.6, the client will now raise an appropriate error if remoting
call returns an error. The default behaviour is to raise a ``pyamf.remoting.RemotingError``
but this behaviour can be modified:

.. code-block:: python

    # service method    def type_error():        raise TypeError('some useful message here')

And from the console:

.. literalinclude:: ../examples/general/client/exception.py


The gateway returns an error code which is mapped to an exception class.

Use :func:`pyamf.add_error_class` to add new code/class combos. A number of built-in
exceptions are automatically mapped: ``TypeError``, ``LookupError``, ``KeyError``,
``IndexError``, ``NameError``. :func:`pyamf.remove_error_class` is used for removing
classes.


More
====

Check the `API docs`_ for more information. The source for the
:doc:`../actionscript/recordset` example is also available.


.. _other AMF implementations: http://en.wikipedia.org/wiki/Action_Message_Format
.. _API docs: http://api.pyamf.org
