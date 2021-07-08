import logging

from django.http.response import HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin

from lib.response import JsonHandler
from lib.serializers import JsonEncoder

#
logger = logging.getLogger(__name__)


class ResponseMiddleware(MiddlewareMixin):
    def process_request(self, request):
        pass

    def process_exception(self, request, exception):
        logger.exception(exception)

        data = JsonHandler(request=request, exception=exception).format()
        return JsonResponse(data=data, encoder=JsonEncoder)

    def process_response(self, request, response):
        if isinstance(response, HttpResponse):
            return response

        #
        result = None
        if isinstance(response, dict):
            result = response
        else:
            logger.error("The type of response must be dictionary")

        data = JsonHandler(request=request, result=result).format()
        return JsonResponse(data=data, encoder=JsonEncoder)
