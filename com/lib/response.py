import time
from django.http.request import HttpRequest
from django.http.response import JsonResponse as DjangoJsonResponse

from lib.errorcode import SystemErrCode
from lib.exceptions import ApiException
from lib.serializers import JsonEncoder


class ResponseHandler:
    """
    Convert response data
    """

    def __init__(self, request: HttpRequest = None, data=None, exception=None):
        self.trace_id = getattr(request, 'X_TRACE_ID', str()) if request else None

        self.code = SystemErrCode.SUCCESS.code
        self.message = SystemErrCode.SUCCESS.message
        self.detail = str()
        self.result = dict() if data is None else data

        self._parse_exception(exception)

    def _parse_exception(self, e):
        if e is None:
            return

        if isinstance(e, ApiException):
            self.code = e.code
            self.message = e.message
            if e.detail:
                self.detail = e.detail
        else:  # Other exception
            self.code = SystemErrCode.INTERNAL_SERVER_ERROR.code
            self.message = SystemErrCode.INTERNAL_SERVER_ERROR.message

    def to_json(self):
        return dict(
            trace_id=self.trace_id,
            code=self.code,
            message=self.message,
            detail=self.detail,
            result=self.result,
            #
            timestamp=int(time.time()),
        )


class JsonResponse(DjangoJsonResponse):
    """
    Django's JsonResponse subclasee
    """

    def __init__(self, data: dict = None, request=None, exception=None, **kwargs):
        """
        If exists exception, will reset data

        """
        data = {} if exception is not None else data
        json_data = ResponseHandler(data=data, request=request, exception=exception).to_json()

        super().__init__(data=json_data, encoder=JsonEncoder, **kwargs)
