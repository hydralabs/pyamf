# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE for details.

from ez_setup import use_setuptools

use_setuptools()

import sys
from setuptools import setup, find_packages, Extension
from setuptools.command import test

try:
    from Cython.Distutils import build_ext
except ImportError:
    from setuptools.command.build_ext import build_ext

class TestCommand(test.test):
    def run_twisted(self):
        from twisted.trial import runner
        from twisted.trial import reporter

        from pyamf.tests import suite

        r = runner.TrialRunner(reporter.VerboseTextReporter)
        return r.run(suite())

    def run_tests(self):
        import logging
        logging.basicConfig()
        logging.getLogger().setLevel(logging.CRITICAL)

        try:
            import twisted

            return self.run_twisted()
        except ImportError:
            return test.test.run_tests(self)

def get_version():
    """
    Gets the version number. Pulls it from the source files rather than
    duplicating it.

    @since: 0.4
    """
    import os.path
    # we read the file instead of importing it as root sometimes does not
    # have the cwd as part of the PYTHONPATH

    fn = os.path.join(os.path.dirname(__file__), 'pyamf', '__init__.py')
    lines = open(fn, 'rt').readlines()

    version = None

    for l in lines:
        # include the ' =' as __version__ is a part of __all__
        if l.startswith('__version__ =', ):
            x = compile(l, fn, 'single')
            eval(x)
            version = locals()['__version__']
            break

    if version is None:
        raise RuntimeError('Couldn\'t determine version number')

    return '.'.join([str(x) for x in version])

def is_float_broken():
    """
    Older versions of python (<=2.5) and the Windows platform are renowned for
    mixing up 'special' floats. This function determines whether this is the
    case.

    @since: 0.4
    """
    import struct

    # we do this instead of float('nan') because windows throws a wobbler.
    nan = 1e300000 / 1e300000

    return str(nan) != str(struct.unpack("!d", '\xff\xf8\x00\x00\x00\x00\x00\x00')[0])

def get_cpyamf_extensions():
    """
    Returns a list of all extensions for the cpyamf module. If for some reason
    cpyamf can't be built an empty list is returned.

    @since: 0.4
    """
    if '--disable-ext' in sys.argv:
        sys.argv.remove('--disable-ext')

        return []

    if sys.platform.startswith('java'):
        print 80 * '*'
        print 'WARNING:'
        print '\tAn optional code optimization (C extension) could not be compiled.\n\n'
        print '\tOptimizations for this package will not be available!\n\n'
        print 'Compiling extensions is not supported on Jython'
        print 80 * '*'
        return []

    ext_modules = []

    try:
        import Cython

        ext_modules.extend([
            Extension('cpyamf.util', ['cpyamf/util.pyx']),
            Extension('cpyamf.amf3', ['cpyamf/amf3.pyx'])
        ])
    except ImportError:
        ext_modules.extend([
            Extension('cpyamf.util', ['cpyamf/util.c']),
            Extension('cpyamf.amf3', ['cpyamf/amf3.c'])
        ])

    return ext_modules

def get_extensions():
    """
    Returns a list of extensions to be built for PyAMF.

    @since: 0.4
    """
    ext_modules = []

    ext_modules.extend(get_cpyamf_extensions())

    return ext_modules

def get_install_requirements():
    """
    Returns a list of dependancies for PyAMF to function correctly on the
    target platform
    """
    install_requires = []

    if sys.version_info < (2, 5):
        install_requires.extend(["elementtree >= 1.2.6", "uuid>=1.30"])

    if is_float_broken():
        install_requires.append("fpconst>=0.7.2")

    return install_requires

keyw = """\
amf amf0 amf3 flex flash remoting rpc http flashplayer air bytearray
objectproxy arraycollection recordset actionscript decoder encoder
gateway remoteobject twisted pylons django sharedobject lso sol"""

setup(name = "PyAMF",
    version = get_version(),
    description = "AMF support for Python",
    long_description = open('README.txt', 'rt').read(),
    url = "http://pyamf.org",
    author = "The PyAMF Project",
    author_email = "dev@pyamf.org",
    keywords = keyw,
    packages = find_packages(exclude=["*.tests"]),
    ext_modules = get_extensions(),
    install_requires = get_install_requirements(),
    test_suite = "pyamf.tests.suite",
    zip_safe = True,
    license = "MIT License",
    platforms = ["any"],
    cmdclass = {
        'test': TestCommand,
        'build_ext': build_ext,
    },
    extras_require = {
        'wsgi': ['wsgiref'],
        'twisted': ['Twisted>=2.5.0'],
        'django': ['Django>=0.96'],
        'sqlalchemy': ['SQLAlchemy>=0.4'],
        'cython': ['Cython>=0.10'],
    },
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Framework :: Django",
        "Framework :: Pylons",
        "Framework :: Turbogears",
        "Framework :: Twisted",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: C",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.3",
        "Programming Language :: Python :: 2.4",
        "Programming Language :: Python :: 2.5",
        "Programming Language :: Python :: 2.6",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ])
