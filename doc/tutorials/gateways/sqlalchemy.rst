**************
  SQLAlchemy 
**************


.. image:: images/sqlalchemy-logo.gif


.. topic:: Introduction

    `SQLAlchemy <http://sqlalchemy.org>`_ is the Python SQL toolkit and
    Object Relational Mapper that gives application developers the full
    power and flexibility of SQL.


Overview
========

PyAMF 0.4 and newer includes an adapter for decoding/encoding objects
managed by SQLAlchemy. The adapter is enabled by default, and SQLAlchemy
managed objects are transparently encoded/decoded by the adapter.

To use the adapter, make sure any SQLAlchemy managed classes are mapped
BEFORE assigning an AMF alias for the class.

.. code-block:: python

   # MUST COME FIRST
   sqlalchemy.orm.mapper(MappedClass, mapped_table)

   # MUST COME LATER
   pyamf.register_class(MappedClass, 'mapped_class_alias')


The adapter adds 2 additional attributes to all encoded objects that are
managed by SQLAlchemy.

- ``sa_key`` -- An Array of values that make up the primary key of the
   encoded object (analogous to ``mapper.primary_key_from_instance(obj)``
   in Python)
- ``sa_lazy`` -- An Array of attribute names that have not yet been
   loaded from the database

The additional information contained in these attributes can be used to lazy load attributes in the client.


Useful Resources
================

http://pyamf.org/wiki/AddressBookExample
   Demonstrates the use of SQLAlchemy and Flex.

http://api.pyamf.org/pyamf.adapters._sqlalchemy-module.html
   API documentation.
