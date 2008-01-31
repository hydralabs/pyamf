# Copyright (c) 2007-2008 The PyAMF Project.
# See LICENSE for details.

"""
Django adapter module.

Sets up basic type mapping and class mappings for a
Django project.

@see: U{Django Project<http://www.djangoproject.com>}

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1b
"""

import pyamf

try:
    from django.db.models.query import QuerySet
except ImportError:
    QuerySet = None

if QuerySet is not None:
    def _write_queryset(qs):
        return list(qs)

    pyamf.add_type(QuerySet, _write_queryset)
