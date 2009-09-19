============
  Features
============

Here's a brief description of the features in PyAMF. The ``CHANGES``
document contains a more detailed summary of all new features.

- `AMF0`_ encoder/decoder for legacy Adobe Flash Players (version 6-8)
- `AMF3`_ encoder/decoder for the new AMF format in Adobe Flash Player 9
  and newer
- Optional C-extension for maximum performance, created using `Cython`_
- Support for ``IExternalizable``, ``ArrayCollection``, ``ObjectProxy``,
  ``ByteArray``, ``RecordSet``, ``RemoteObject`` and ``more``
- Remoting gateways for :doc:`Twisted <../tutorials/gateways/twisted>`,
  :doc:`Django <../tutorials/gateways/django>`,
  :doc:`Google App Engine <../tutorials/gateways/appengine>`,
  :doc:`Pylons <../tutorials/gateways/pylons>`,
  :doc:`TurboGears2 <../tutorials/gateways/turbogears>`,
  :doc:`web2py <../tutorials/gateways/web2py>`, and any compatible
  `WSGI <http://wsgi.org>`_ framework
- :doc:`Adapter framework <../architecture/adapters>` to integrate
  nicely with third-party Python projects including
  :doc:`Django <../tutorials/gateways/django>`,
  :doc:`Google App Engine <../tutorials/gateways/appengine>` and
  :doc:`SQLAlchemy <../tutorials/gateways/sqlalchemy>`
- ``Authentication``/``setCredentials`` support
- Python AMF :doc:`client <../tutorials/general/client>` with HTTP(S)
  and authentication support
- Service Browser requests supported
- :doc:`Local Shared Object <../tutorials/general/sharedobject>`
  support

Also see the our plans for :doc:`future development <future>`.


.. _AMF0: http://livedocs.adobe.com/flex/3/langref/flash/net/ObjectEncoding.html#AMF0
.. _AMF3: http://livedocs.adobe.com/flex/3/langref/flash/net/ObjectEncoding.html#AMF3
.. _Cython: http://cython.org
