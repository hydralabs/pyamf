# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

USE_CPYAMF = True

from ez_setup import use_setuptools

use_setuptools()

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

import sys

ext_modules = []

if USE_CPYAMF and not sys.platform.startswith('java'):
    ext_modules.append(Extension('cpyamf.util', ["cpyamf/util.c"], extra_compile_args=['-O3']))

install_requires = []
if sys.version_info < (2, 5):
    install_requires.extend(
        ["elementtree >= 1.2.6", "uuid>=1.30", "fpconst>=0.7.2"])
elif sys.platform.startswith('win'):
    install_requires.append("fpconst>=0.7.2")

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
    ext_modules = ext_modules,
    install_requires = install_requires,
    test_suite = "pyamf.tests.suite",
    zip_safe=True,
    license = "MIT License",
    platforms = ["any"],
    cmdclass = {'test': TestCommand},
    extras_require={
        'wsgi': ['wsgiref'],
        'twisted': ['Twisted>=2.5.0'],
        'django': ['Django>=0.96']
    },
    classifiers = [
        "Development Status :: 4 - Beta",
        "Natural Language :: English",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
	"Framework :: Django",
	"Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ])
