"""
Views for the PyAMF web based unit test runner.
"""

import logging, time

from django.shortcuts import render_to_response
from django.http import HttpResponseNotFound, HttpResponse

import pyamf
import simplejson
from punit import models

def frontpage(request):
    tests = models.get_all_tests()
    return render_to_response('punit/index.html', {
            'tests': tests,
            'expected': models.expected_failures,
            'pyamf_version': '.'.join(map(lambda x: str(x), pyamf.__version__))
    })

def run_test_method(request, module, test_case, method):
    start = time.time()
    try:
        result = models.run_test(module, test_case, method)
    except AttributeError:
        return HttpResponseNotFound()

    stop = time.time()

    content = simplejson.dumps({
        'test': '%s.%s.%s' % (module, test_case, method),
        'start': start,
        'stop': stop,
        'passed': result.wasSuccessful(),
        'failures': result.failures,
        'errors': result.errors,
        'expected_failure': '%s.%s.%s' % (module, test_case, method) in models.expected_failures
    })

    return HttpResponse(content=content, mimetype='application/x-javascript')

def all_tests(request):
    return HttpResponse(mimetype='application/x-javascript', content=simplejson.dumps({
        'tests': models.get_all_tests(),
        'expected': models.expected_failures,
        'skipped': models.skipped_tests
    }))