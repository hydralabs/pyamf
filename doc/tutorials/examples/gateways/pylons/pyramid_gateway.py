from pyramid_rpc.amfgateway import PyramidGateway


def my_view(request):
    return {'project':'pyamf_tutorial'}

def echo(request, data):
    """
    This is a function that we will expose.
    """
    # echo data back to the client
    return data


services = {
    'myservice.echo': echo,
    # Add other exposed functions and classes here
}

echoGateway = PyramidGateway(services, debug=True)

