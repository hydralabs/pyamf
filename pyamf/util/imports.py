# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.

"""
Tools for doing dynamic imports.

@since: 0.3
"""

import sys


__all__ = ['when_imported']

#: A list of callables to be executed when the module is imported.
post_load_hooks = {}
#: List of modules that have already been loaded.
loaded_modules = []


class ModuleFinder(object):
    """
    This is a special module finder object that executes a collection of
    callables when a specific module has been imported. An instance of this
    is placed in C{sys.meta_path}, which is consulted before C{sys.modules} -
    allowing us to provide this functionality.

    @see: L{when_imported}
    @since: 0.5
    """

    def find_module(self, name, path):
        """
        Called when an import is made. If there are hooks waiting for this
        module to be imported then we stop the normal import process and
        manually load the module.

        @param name: The name of the module being imported.
        @param path The root path of the module (if a package). We ignore this.
        @return: If we want to hook this module, we return a C{loader}
            interface (which is this instance again). If not we return C{None}
            to allow the standard import process to continue.
        """
        if name in loaded_modules or name not in post_load_hooks:
            return None

        return self

    def load_module(self, name):
        """
        If we get this far, then there are hooks waiting to be called on
        import of this module. We manually load the module and then run the
        hooks.

        @param name: The name of the module to import.
        """
        loaded_modules.append(name)
        parent, child = split_module(name)

        __import__(name, {}, {}, [])

        mod = sys.modules[name]

        run_hooks(name, mod)

        return mod


def run_hooks(name, module):
    """
    Run all hooks for a module.
    Load an unactivated "lazy" module object.
    """
    try:
        for hook in post_load_hooks[name]:
            hook(module)
    finally:
        del post_load_hooks[name]


def split_module(name):
    """
    Splits a module name into its parent and child parts.

    >>> split_module('foo.bar.baz')
    'foo.bar', 'baz'
    >>> split_module('foo')
    None, 'foo'
    """
    try:
        splitpos = name.rindex('.') + 1

        return name[:splitpos - 1], name[splitpos:]
    except ValueError:
        return None, name


def when_imported(name, hook):
    """
    Call C{hook(module)} when module named C{name} is first used.

    'hook' must accept one argument: the module object named by 'name', which
    must be a fully qualified (i.e. absolute) module name.  The hook should
    not raise any exceptions, or it will prevent later hooks from running.

    If the module has already been imported normally, 'hook(module)' is
    called immediately, and the module object is returned from this function.
    If the module has not been imported, then the hook is called when the
    module is first imported.
    """
    if name in loaded_modules or name in sys.modules:
        hook(sys.modules[name])

        return

    if name not in post_load_hooks:
        post_load_hooks[name] = []

    post_load_hooks[name].append(hook)


# this is required for reloading this module
for obj in sys.meta_path:
    if obj.__class__ is ModuleFinder:
        break
else:
    sys.meta_path.insert(0, ModuleFinder())
