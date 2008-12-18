# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

from ez_setup import use_setuptools

use_setuptools()

import sys
from setuptools import setup, find_packages, Extension
from setuptools.command import test

class TestCommand(test.test):
    def run_twisted(self):
        from twisted.trial import runner
        from twisted.trial import reporter

        from pyamf.tests import suite

        r = runner.TrialRunner(reporter.VerboseTextReporter)
        r.run(suite())

    def run_tests(self):
        import logging
        logging.basicConfig()
        logging.getLogger().setLevel(logging.CRITICAL)
        try:
            import twisted

            self.run_twisted()
        except ImportError:
            test.test.run_tests(self)

def get_cpyamf_extensions():
    """
    Returns a list of all extensions for the cpyamf module. If for some reason
    cpyamf can't be built an empty list is returned.
    """
    if '--disable-ext' in sys.argv:
        sys.argv.remove('--disable-ext')

        return []

    if sys.platform.startswith('java'):
        return []

    return [Extension(
        'cpyamf.util',
        ["cpyamf/util.c"],
        extra_compile_args=['-O3']
    )]

def get_extensions():
    """
    Returns a list of extensions to be built for PyAMF.
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
        install_requires.extend(
            ["elementtree >= 1.2.6", "uuid>=1.30", "fpconst>=0.7.2"])
    elif sys.platform.startswith('win'):
        install_requires.append("fpconst>=0.7.2")

    return install_requires

keyw = """\
amf amf0 amf3 flex flash remoting rpc http flashplayer air bytearray
objectproxy arraycollection recordset actionscript decoder encoder
gateway"""

setup(name = "PyAMF",
    version = "0.4",
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
    zip_safe=True,
    license = "MIT License",
    platforms = ["any"],
    cmdclass = {
        'test': TestCommand
    },
    extras_require = {
        'wsgi': ['wsgiref'],
        'twisted': ['Twisted>=2.5.0'],
        'django': ['Django>=0.96']
    },
    classifiers = [
        "Development Status :: 4 - Beta",
        "Natural Language :: English",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.3",
        "Programming Language :: Python :: 2.4",
        "Programming Language :: Python :: 2.5",
        "Programming Language :: Python :: 2.6",
        "Framework :: Django",
        "Framework :: Twisted",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ])
