# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
The adapter package provides additional functionality for other python
packages. This includes registering classes, setting up type maps etc.

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}
@since: 0.1b
"""

import sys, os.path, glob, types, imp

from peak.util import imports

thismodule = None

for name, mod in sys.modules.iteritems():
    if not isinstance(mod, types.ModuleType):
        continue

    if not hasattr(mod, '__file__'):
        continue

    if mod.__file__ == __file__:
        thismodule = (name, mod)

        break

class PackageImporter(object):
    def __init__(self, name):
        self.name = name

    def __call__(self, name):
        __import__('%s.%s' % (thismodule[0], self.name))

for f in glob.glob(os.path.join(os.path.dirname(__file__), '*.py')):
    mod = os.path.basename(f).split(os.path.extsep, 1)[0]

    if not mod.startswith('_') or mod == '__init__':
        continue

    try:
        imp.find_module(mod[1:])
    except ImportError:
        continue
    
    imports.whenImported(mod[1:], PackageImporter(mod))
