#!/bin/bash -e

# used by travis to determine whether to install Cython (and thereby compile
# the PyAMF extensions)


if [ "${USE_EXTENSIONS}" == "true" ]; then
    pip install Cython
fi
