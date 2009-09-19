**********
  Client 
**********

.. topic:: Introduction

   PyAMF isn't just about the Adobe Flash Player talking to a Python
   backend, oh no. We have put together a client module which allows
   you to make AMF calls to an HTTP Gateway, whether that be PyAMF or
   `other AMF implementations <http://en.wikipedia.org/wiki/Action_Message_Format>`_.
   If you come from a Adobe Flash background, this API will feel
   very natural to you.


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


Authenication
-------------

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


More
====

Check the `API docs <http://api.pyamf.org>`_ for more information. The source
for the RecordSet example is also available.