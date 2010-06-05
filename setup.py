# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

from ez_setup import use_setuptools

# 15 seconds is far too long ....
use_setuptools(download_delay=3)

import sys, os.path

from setuptools import setup, find_packages, Extension
from setuptools.command import test

try:
    from Cython.Distutils import build_ext
except ImportError:
    from setuptools.command.build_ext import build_ext


# add the path of the folder this file lives in
base_path = os.path.dirname(os.path.normpath(os.path.abspath(__file__)))

# since the basedir is set as the first option in sys.path, this works
sys.path.insert(0, base_path)

readme = os.path.join(base_path, 'README.txt')


class TestCommand(test.test):
    """
    Ensures that unittest2 is imported if required and replaces the old
    unittest module.
    """

    def run_tests(self):
        try:
            import unittest2
            import sys

            sys.modules['unittest'] = unittest2
        except ImportError:
            pass

        return test.test.run_tests(self)


def get_cpyamf_extensions():
    """
    Returns a list of all extensions for the cpyamf module. If for some reason
    cpyamf can't be built an empty list is returned.

    :since: 0.4
    """
    try:
        import Cython

        extension = '.pyx'
    except ImportError:
        extension = '.c'

    import glob

    ext_modules = []

    for file in glob.glob(os.path.join('cpyamf', '*' + extension)):
        mod = file.replace(os.path.sep, '.')[:-len(extension)]

        ext_modules.append(Extension(mod, [file]))

    return ext_modules


def get_extensions():
    """
    Returns a list of extensions to be built for PyAMF.

    :since: 0.4
    """
    if sys.platform.startswith('java'):
        print(80 * '*')
        print('WARNING:')
        print('\tAn optional code optimization (C extension) could not be compiled.\n\n')
        print('\tOptimizations for this package will not be available!\n\n')
        print('Compiling extensions is not supported on Jython')
        print(80 * '*')

        return []

    if '--disable-ext' in sys.argv:
        sys.argv.remove('--disable-ext')

        return []

    ext_modules = []

    ext_modules.extend(get_cpyamf_extensions())

    return ext_modules


def get_install_requirements():
    """
    Returns a list of dependancies for PyAMF to function correctly on the
    target platform.
    """
    install_requires = []

    if sys.version_info < (2, 5):
        install_requires.extend(["elementtree >= 1.2.6", "uuid>=1.30"])

    return install_requires


def get_test_requirements():
    tests_require = ['pysqlite']

    if sys.version_info < (2, 7):
        tests_require.append('unittest2')

    return tests_require


def get_version():
    mp = sys.meta_path[:]

    from pyamf import version

    # need to remove all references to imported pyamf modules, as building
    # the c extensions change pyamf.util.BufferedByteStream, which blow up
    # the tests (at least the first time its built which in case of the 
    # buildbots is always true)
    for k, v in sys.modules.copy().iteritems():
        if k and k.startswith('pyamf'):
            del sys.modules[k]

    sys.meta_path = mp

    return version


keyw = """\
amf amf0 amf3 flex flash remoting rpc http flashplayer air bytearray
objectproxy arraycollection recordset actionscript decoder encoder
gateway remoteobject twisted pylons django sharedobject lso sol"""


def main():
    setup(name = "PyAMF",
        version = str(get_version()),
        description = "AMF support for Python",
        long_description = open(readme, 'rt').read(),
        url = "http://pyamf.org",
        author = "The PyAMF Project",
        author_email = "users@pyamf.org",
        keywords = keyw,
        packages = find_packages(exclude=["*.tests"]),
        ext_modules = get_extensions(),
        install_requires = get_install_requirements(),
        tests_require = get_test_requirements(),
        test_suite = "pyamf.tests.get_suite",
        zip_safe = True,
        license = "MIT License",
        platforms = ["any"],
        cmdclass = {
            'build_ext': build_ext,
           'test': TestCommand
        },
        extras_require = {
            'wsgi': ['wsgiref'],
            'twisted': ['Twisted>=2.5.0'],
            'django': ['Django>=0.96'],
            'sqlalchemy': ['SQLAlchemy>=0.4'],
            'cython': ['Cython>=0.12.1'],
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


if __name__ == '__main__':
    main()
