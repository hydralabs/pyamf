:mod:`pyamf` --- pyamf
=============================================

.. automodule:: pyamf
   :members:
   :synopsis: AMF support for Python.

.. autofunction:: get_class_alias
.. autofunction:: unregister_class
.. autofunction:: register_alias_type
.. autofunction:: unregister_alias_type
.. autofunction:: unregister_class_loader

.. autofunction:: add_error_class

    An example::        >>> class AuthenticationError(Exception):        ...     pass        ...         >>> pyamf.add_error_class(AuthenticationError, 'Auth.Failed')        >>> print pyamf.ERROR_CLASS_MAP        {'TypeError': <type 'exceptions.TypeError'>, 'IndexError': <type 'exceptions.IndexError'>,        'Auth.Failed': <class '__main__.AuthenticationError'>, 'KeyError': <type 'exceptions.KeyError'>,        'NameError': <type 'exceptions.NameError'>, 'LookupError': <type 'exceptions.LookupError'>}

.. autofunction:: remove_error_class

   An example::       >>> class AuthenticationError(Exception):       ...     pass       ...       >>> pyamf.add_error_class(AuthenticationError, 'Auth.Failed')       >>> pyamf.remove_error_class(AuthenticationError)

.. autofunction:: add_type
.. autofunction:: remove_type
.. autofunction:: register_package

    For example `mymodule.py`::        class User(object):            pass        class Permission(object):            pass    Register it like this::

        >>> import mymodule
        >>> pyamf.register_package(mymodule, 'com.example.app')    Now all instances of `mymodule.User` will appear in Actionscript under the    alias `'com.example.app.User'`. Same goes for `mymodule.Permission` - the    Actionscript alias is `'com.example.app.Permission'`. The reverse is also    true, any objects with the correct aliases will now be instances of the    relevant Python class.    This function respects the `__all__` attribute of the module but you can    have further control of what not to auto alias by populating the `ignore`    argument.    This function provides the ability to register the module it is being    called in, an example::        >>> class Foo:        ...     pass        ...        >>> class Bar:        ...     pass        ...        >>> pyamf.register_package('foo')    You can also supply a list of classes to register. An example, taking the    above classes::        >>> pyamf.register_package([Foo, Bar], 'foo')

.. autodata:: AMF0
.. autodata:: AMF3
.. autodata:: DEFAULT_ENCODING
.. autodata:: version

   PyAMF version number.

   >>> pyamf.__version__ is pyamf.version
   True
   >>> pyamf.version
   (0, 6, 1, 'rc1')
   >>> str(pyamf.version)
   '0.6.1rc1'

   :see: :class:`pyamf.versions`


Type Maps
---------

.. autodata:: CLASS_CACHE

   >>> pyamf.CLASS_CACHE
   {<class 'pyamf.ASObject'>: <ClassAlias alias= class=<class 'pyamf.ASObject'> @ 0x100568a50>}

   :see: :func:`register_class`, :func:`unregister_class` and :func:`register_package`

.. autodata:: ALIAS_TYPES

   >>> pyamf.ALIAS_TYPES
   {<class 'pyamf.TypedObjectClassAlias'>: (<class 'pyamf.TypedObject'>,),
    <class 'pyamf.ErrorAlias'>: (<type 'exceptions.Exception'>,)}

   :see: :func:`get_class_alias`, :func:`register_alias_type` and :func:`unregister_alias_type`

.. autodata:: ERROR_CLASS_MAP

   >>> pyamf.ERROR_CLASS_MAP
   {'LookupError': <type 'exceptions.LookupError'>, 'NameError': <type 'exceptions.NameError'>,
    'TypeError': <type 'exceptions.TypeError'>, 'IndexError': <type 'exceptions.IndexError'>,
    'KeyError': <type 'exceptions.KeyError'>}

   :see: :func:`add_error_class` and :func:`remove_error_class`

.. autodata:: TYPE_MAP

   >>> pyamf.TYPE_MAP
   {<type 'array.array'>: <function to_list at 0x101345ed8>,
    <type 'collections.deque'>: <function to_list at 0x101345ed8>,
    <type 'collections.defaultdict'>: <function to_dict at 0x101349b18>}

   :see: :func:`get_type`, :func:`add_type` and :func:`remove_type`

.. autodata:: CLASS_LOADERS

   >>> pyamf.CLASS_LOADERS
   [<function flex_loader at 0x100569e60>, <function blaze_loader at 0x100569de8>]

   :see: :func:`register_class_loader` and :func:`unregister_class_loader`

.. autodata:: ENCODING_TYPES

   >>> pyamf.ENCODING_TYPES              
   (0, 3)

   :see: :data:`AMF0`, :data:`AMF3`, and :data:`DEFAULT_ENCODING`


Exception Types
---------------

.. autoexception:: BaseError
.. autoexception:: DecodeError
.. autoexception:: EOStream
.. autoexception:: ReferenceError
.. autoexception:: EncodeError

.. autoexception:: ClassAliasError
.. autoexception:: UnknownClassAlias


Other Types
-----------

.. autoclass:: Undefined
.. autoclass: Context
.. autoclass:: ClassAlias
