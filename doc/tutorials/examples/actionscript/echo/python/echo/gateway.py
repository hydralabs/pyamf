# Copyright (c) 2007-2009 The PyAMF Project.
# See LICENSE.txt for details.

"""
Echo example gateway for Django.

@since: 0.1.0
"""

from pyamf.remoting.gateway.django import DjangoGateway

import echo

echoGateway = DjangoGateway({
    'echo': echo.echo,
    'Red5Echo': echo,
}, expose_request=False)
