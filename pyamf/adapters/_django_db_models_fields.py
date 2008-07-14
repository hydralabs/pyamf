# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
C{django.db.models.fields} adapter module.

@see: U{Django Project<http://www.djangoproject.com>}
@since: 0.3.2
"""

from django.db.models import fields

import pyamf

def convert_NOT_PROVIDED(x):
    return pyamf.Undefined

pyamf.add_type(lambda x: x == fields.NOT_PROVIDED, convert_NOT_PROVIDED)
