from scim_endpoint.models import RequestLogging


def request_logging(get_response):

    def middleware(request):
        response = get_response(request)
        RequestLogging.objects.create(
            request_body=request.body.decode(),
            response_body=response.content.decode(),
            response_status_code=response.status_code,
            method=request.method.lower(),
            path=request.path,
        )
        return response

    return middleware
