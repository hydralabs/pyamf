# Copyright (c) The PyAMF Project.
# See LICENSE.txt for details.

# The simplest Django settings possible

# support for Django < 1.5
DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = ':memory:'

# support for Django >= 1.5
SECRET_KEY = 'unittest'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.' + DATABASE_ENGINE,
        'NAME': DATABASE_NAME,
    }
}


INSTALLED_APPS = ('adapters',)
