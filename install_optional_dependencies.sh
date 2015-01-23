#!/bin/bash -e

# used by Travis to install optional dependencies
# see .travis.yml:env for envrionment variables

function install_django {
  if [ -z "${DJANGO_VERSION}" ]; then
      return 0
  fi

  pip install "Django==${DJANGO_VERSION}"
}

function install_sqlalchemy {
  if [ -z "${SQLALCHEMY_VERSION}" ]; then
      return 0
  fi

  pip install "SQLAlchemy==${SQLALCHEMY_VERSION}"
}

function install_twisted {
  if [ -z "${TWISTED_VERSION}" ]; then
      return 0
  fi

  pip install "Twisted==${TWISTED_VERSION}"
}

function install_gae_sdk {
  if [ -z "${GAESDK_VERSION}" ]; then
      return 0
  fi

  wget https://storage.googleapis.com/appengine-sdks/featured/google_appengine_${GAESDK_VERSION}.zip -nv
  unzip -q google_appengine_${GAESDK_VERSION}.zip -d ~/gaesdk
  python -c "import dev_appserver"
}

install_django
install_sqlalchemy
install_twisted
install_gae_sdk
