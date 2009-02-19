# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE for details.

"""
Tools for doing dynamic imports

This module has been borrowed from the Importing package.

@see: U{http://pypi.python.org/pypi/Importing}
@see: U{http://peak.telecommunity.com/DevCenter/Importing}

Original author: U{Phillip J. Eby<peak@eby-sarna.com>}

@since: 0.3.0
"""

__all__ = [
    'lazyModule', 'joinPath', 'whenImported', 'getModuleHooks',
]

import sys, os.path
from types import ModuleType

postLoadHooks = {}
loadedModules = []

try:
    from imp import find_module

    # google app engine requires this because it checks to ensure that the
    # find_module function is functioning at least basically
    # most appengine patchers just stub the function
    find_module('pyamf.util.imports')
except ImportError:
    def find_module(subname, path=None):
        # the dev_appserver freaks out if you have pyc, pyo in here as 
        # we're hooking pyamf.amf0 and pyamf.amf3 in the gae adapter and
        # monkey-patching it. It rightly complains as the byte-compiled module
        # is different to the 'final' module.
        PY_EXT = ('.py',)

        if path is None:
            path = sys.path

        for p in path:
            py = os.path.join(p, subname)

            for full in PY_EXT:
                full = py + full

                if os.path.exists(full):
                    return open(full), full, None

            py = os.path.join(p, subname, '__init__')

            for full in PY_EXT:
                full = py + full

                if os.path.exists(full):
                    return None, os.path.join(p, subname), None

        raise ImportError('No module named %s' % subname)

class SubModuleLoadHook(object):
    def __init__(self, parent, child, hook, *args, **kwargs):
        self.parent = parent
        self.child = child
        self.hook = hook
        self.args = args
        self.kwargs = kwargs

    def __eq__(self, other):
        if not isinstance(other, SubModuleLoadHook):
            return False

        return self.parent == other.parent and self.child == other.child

    def __call__(self, module):
        return self.hook(*self.args, **self.kwargs)

class AlreadyRead(Exception):
    pass

class LazyModule(ModuleType):
    __slots__ = ()
    __reserved_attrs__ = ('__name__', '__file__', '__path__')

    def __init__(self, name, file, path=None):
        ModuleType.__setattr__(self, '__name__', name)
        ModuleType.__setattr__(self, '__file__', file)

        if path is not None:
            ModuleType.__setattr__(self, '__path__', path)

    def __getattribute__(self, attr):
        if attr not in LazyModule.__reserved_attrs__:
            _loadModule(self)

        return ModuleType.__getattribute__(self, attr)

    def __setattr__(self, attr, value):
        if attr not in LazyModule.__reserved_attrs__:
            _loadModule(self)

        return ModuleType.__setattr__(self, attr, value)

def _loadModule(module):
    if _isLazy(module) and module not in loadedModules:
        _loadAndRunHooks(module)

def joinPath(modname, relativePath):
    """
    Adjust a module name by a '/'-separated, relative or absolute path
    """
    module = modname.split('.')

    for p in relativePath.split('/'):
        if p == '..':
            module.pop()
        elif not p:
            module = []
        elif p != '.':
            module.append(p)

    return '.'.join(module)

def lazyModule(modname, relativePath=None):
    """
    Return module 'modname', but with its contents loaded "on demand"

    This function returns 'sys.modules[modname]', if present.  Otherwise
    it creates a 'LazyModule' object for the specified module, caches it
    in 'sys.modules', and returns it.

    'LazyModule' is a subclass of the standard Python module type, that
    remains empty until an attempt is made to access one of its
    attributes.  At that moment, the module is loaded into memory, and
    any hooks that were defined via 'whenImported()' are invoked.

    Note that calling 'lazyModule' with the name of a non-existent or
    unimportable module will delay the 'ImportError' until the moment
    access is attempted.  The 'ImportError' will occur every time an
    attribute access is attempted, until the problem is corrected.

    This function also takes an optional second parameter, 'relativePath',
    which will be interpreted as a '/'-separated path string relative to
    'modname'.  If a 'relativePath' is supplied, the module found by
    traversing the path will be loaded instead of 'modname'.  In the path,
    '.' refers to the current module, and '..' to the current module's
    parent.  For example::

        fooBaz = lazyModule('foo.bar','../baz')

    will return the module 'foo.baz'.  The main use of the 'relativePath'
    feature is to allow relative imports in modules that are intended for
    use with module inheritance.  Where an absolute import would be carried
    over as-is into the inheriting module, an import relative to '__name__'
    will be relative to the inheriting module, e.g.::

        something = lazyModule(__name__,'../path/to/something')

    The above code will have different results in each module that inherits
    it.

    (Note: 'relativePath' can also be an absolute path (starting with '/');
    this is mainly useful for module '__bases__' lists.)
    """
    if relativePath:
        modname = joinPath(modname, relativePath)

    if modname not in sys.modules:
        file_name = path = None

        if '.' in modname:
            splitpos = modname.rindex('.')

            parent = sys.modules[modname[:splitpos]]
            file_name = find_module(modname[splitpos + 1:], parent.__path__)[1]
        else:
            file_name = find_module(modname)[1]

        if os.path.isdir(file_name):
            path = [file_name]
            py = os.path.join(file_name, '__init__')

            for full in ('.pyo', '.pyc', '.py'):
                full = py + full

                if os.path.exists(full):
                    break
            else:
                raise ImportError('No module name %d' % modname)

            file_name = full

        getModuleHooks(modname) # force an empty hook list into existence
        sys.modules[modname] = LazyModule(modname, file_name, path)

        if '.' in modname:
            # ensure parent module/package is in sys.modules
            # and parent.modname=module, as soon as the parent is imported

            splitpos = modname.rindex('.')

            whenImported(
                modname[:splitpos],
                lambda m: setattr(m, modname[splitpos + 1:], sys.modules[modname])
            )

    return sys.modules[modname]

def _isLazy(module):
    """
    Checks to see if the supplied C{module} is lazy
    """
    if module.__name__ not in postLoadHooks.keys():
        return False

    return postLoadHooks[module.__name__] is not None

def _loadAndRunHooks(module):
    """
    Load an unactivated "lazy" module object
    """
    if _isLazy(module): # don't reload if already loaded!
        loadedModules.append(module)
        reload(module)

    try:
        for hook in getModuleHooks(module.__name__):
            hook(module)
    finally:
        # Ensure hooks are not called again, even if they fail
        postLoadHooks[module.__name__] = None

def getModuleHooks(moduleName):
    """
    Get list of hooks for 'moduleName'; error if module already loaded
    """
    hooks = postLoadHooks.setdefault(moduleName, [])

    if hooks is None:
        raise AlreadyRead("Module already imported", moduleName)

    return hooks

def _setModuleHook(moduleName, hook):
    if moduleName in sys.modules and postLoadHooks.get(moduleName) is None:
        # Module is already imported/loaded, just call the hook
        module = sys.modules[moduleName]
        hook(module)

        return module

    getModuleHooks(moduleName).append(hook)

    return lazyModule(moduleName)

def whenImported(moduleName, hook):
    """
    Call 'hook(module)' when module named 'moduleName' is first used

    'hook' must accept one argument: the module object named by 'moduleName',
    which must be a fully qualified (i.e. absolute) module name.  The hook
    should not raise any exceptions, or it may prevent later hooks from
    running.

    If the module has already been imported normally, 'hook(module)' is
    called immediately, and the module object is returned from this function.
    If the module has not been imported, or has only been imported lazily,
    then the hook is called when the module is first used, and a lazy import
    of the module is returned from this function.  If the module was imported
    lazily and used before calling this function, the hook is called
    immediately, and the loaded module is returned from this function.

    Note that using this function implies a possible lazy import of the
    specified module, and lazy importing means that any 'ImportError' will be
    deferred until the module is used.
    """
    if '.' in moduleName:
        # If parent is not yet imported, delay hook installation until the
        # parent is imported.
        splitpos = moduleName.rindex('.')

        sub_hook = SubModuleLoadHook(moduleName[:splitpos],
            moduleName[splitpos + 1:], _setModuleHook, moduleName, hook)

        if moduleName[:splitpos] not in postLoadHooks.keys():
            whenImported(moduleName[:splitpos], sub_hook)
        elif postLoadHooks[moduleName[:splitpos]] is None:
            whenImported(moduleName[:splitpos], sub_hook)
        elif sub_hook not in postLoadHooks[moduleName[:splitpos]]:
            whenImported(moduleName[:splitpos], sub_hook)
        else:
            postLoadHooks[moduleName[:splitpos]].append(sub_hook)
    else:
        return _setModuleHook(moduleName, hook)
