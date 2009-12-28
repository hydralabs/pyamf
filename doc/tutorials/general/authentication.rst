******************
  Authentication
******************

.. topic:: Introduction

   The basic authentication examples show how to use authentication
   for PyAMF with other AMF clients and servers.

   This approach to authentication will work because the PyAMF client
   is using "standard" remoting requests under the hood.

**Warning**: Authentication and authorization via RemoteObject will be
supported through the Plasma_ project in the future, but till then
requests can be made to your services without having the authenticator
called.

Python
------

Python_ AMF examples are available for:

- `httplib <../../examples/general/authentication/python/client.py>`_ -- Python AMF client
- `wsgiref <../../examples/general/authentication/python/server.py>`_ -- Python AMF server


Actionscript
------------

ActionScript examples are available for:

- `MXML/ActionScript 3.0 <../examples/general/authentication/flash/flex/>`_
- `ActionScript 3.0 <../examples/general/authentication/flash/as3/>`_
- `ActionScript 2.0 <../examples/general/authentication/flash/as2/>`_
- `Server-Side ActionScript <../examples/general/authentication/flash/ssa1/>`_


.. _Plasma: http://plasmads.org
.. _Python: http://python.org
