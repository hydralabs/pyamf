# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

from ez_setup import use_setuptools

use_setuptools()

from setuptools import setup, find_packages
from setuptools.command import test

class TestCommand(test.test):
    def run_twisted(self):
        from twisted.trial import runner
        from twisted.trial import reporter

        from pyamf.tests import suite

        r = runner.TrialRunner(reporter.VerboseTextReporter)
        r.run(suite())

    def run_tests(self):
        try:
            import twisted

            self.run_twisted()
        except ImportError:
            test.test.run_tests(self)

setup(name = "PyAMF",
    version = "0.1b",
    description = "AMF encoder and decoder for Python",
    url = "http://pyamf.org",
    packages = find_packages(exclude=["*.tests"]),
    install_requires = ["elementtree>=1.2.6", "uuid>=1.30", "fpconst"],
    test_suite = "pyamf.tests.suite",
    license = "MIT License",
    cmdclass = {'test': TestCommand},
    entry_points={
        'console_scripts': [
            'amfinfo = pyamf.scripts.parse_dump:main',
        ],
    },
    extras_require={
        'wsgi': ['wsgiref'],
        'twisted': ['Twisted>=2.5.0'],
        'django': ['Django>=0.96']
    },
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Natural Language :: English",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ])
