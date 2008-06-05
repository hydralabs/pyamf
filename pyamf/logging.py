# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Logging utilities.

@since: 0.2.0
"""

logging = __import__('logging')

def _get_instance_name(obj):
    return "%s.%s.0x%x" % (
        obj.__class__.__module__, obj.__class__.__name__, id(obj))

def class_logger(cls):
    return logging.getLogger('%s.%s' % (cls.__module__, cls.__name__))

def instance_logger(instance):
    return logging.getLogger(_get_instance_name(instance))
