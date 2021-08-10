import logging

from django.http.response import HttpResponse
from django.utils.deprecation import MiddlewareMixin

from utils.response import JsonResponse

#
logger = logging.getLogger(__name__)


class ResponseMiddleware(MiddlewareMixin):
    def process_request(self, request):
        exception = getattr(request, 'X_EXCEPTION', None)
        if exception:
            return JsonResponse(request=request, exception=exception)

    def process_exception(self, request, exception):
        logger.exception(exception)
        return JsonResponse(request=request, exception=exception)

    def process_response(self, request, response):
        if isinstance(response, HttpResponse):
            return response
        return JsonResponse(data=response, request=request)
