# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
The adapter package provides additional functionality for other Python
packages. This includes registering classes, setting up type maps etc.

@since: 0.1.0
"""

import os.path, glob

from pyamf.util import imports

class PackageImporter(object):
    """
    Package importer used for lazy module loading.
    """
    def __init__(self, name):
        self.name = name

    def __call__(self, mod):
        __import__('%s.%s' % ('pyamf.adapters', self.name))

adapters_registered = False

def register_adapters():
    global adapters_registered

    if adapters_registered is True:
        return

    try:
        import pkg_resources
        packageDir = pkg_resources.resource_filename('pyamf', 'adapters')
    except:
        packageDir = os.path.dirname(__file__)

    for f in glob.glob(os.path.join(packageDir, '*.py')):
        mod = os.path.basename(f).split(os.path.extsep, 1)[0]

        if mod == '__init__' or not mod.startswith('_'):
            continue

        try:
            module = imports.whenImported(mod[1:].replace('_', '.'), PackageImporter(mod))
        except ImportError:
            pass

    adapters_registered = True
