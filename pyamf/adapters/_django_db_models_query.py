# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Django model adapter module.

Sets up basic type mapping and class mappings for a
Django models.

@see: U{Django Project<http://www.djangoproject.com>}
@since: 0.1b
"""

from django.db.models import query

import pyamf

def write_queryset(qs):
    return list(qs)

pyamf.add_type(query.QuerySet, write_queryset)
