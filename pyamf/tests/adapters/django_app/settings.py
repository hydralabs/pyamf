# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

# The simplest Django settings possible

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

SECRET_KEY = "wat"

INSTALLED_APPS = ('adapters',)

