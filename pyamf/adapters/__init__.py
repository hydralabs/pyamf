# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
The adapter package provides additional functionality for other Python
packages. This includes registering classes, setting up type maps etc.

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import sys, os.path, glob, types, imp

from peak.util import imports

class PackageImporter(object):
    """
    Package importer used for lazy module loading.
    """
    def __init__(self, name):
        self.name = name

    def __call__(self, name):
        __import__('%s.%s' % ('pyamf.adapters', self.name))

for f in glob.glob(os.path.join(os.path.dirname(__file__), '*.py')):
    mod = os.path.basename(f).split(os.path.extsep, 1)[0]

    if not mod.startswith('_') or mod == '__init__':
        continue

    try:
        imp.find_module(mod[1:])
    except ImportError:
        continue

    imports.whenImported(mod[1:], PackageImporter(mod))
del f

