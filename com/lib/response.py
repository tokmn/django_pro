import time
from django.http.request import HttpRequest

from lib.errorcode import SystemErrCode
from lib.exceptions import ApiException


class JsonHandler:
    def __init__(self, request: HttpRequest = None, result=None, exception=None):
        self.trace_id = getattr(request, 'x_trace_id', str()) if request else None

        self.code = SystemErrCode.success.code
        self.message = SystemErrCode.success.message
        self.detail = str()
        self.result = dict() if result is None else result

        self.parse_exception(exception)

    def parse_exception(self, e):
        if e is None:
            return

        if isinstance(e, ApiException):
            self.code = e.code
            self.message = e.message
            if e.detail:
                self.detail = e.detail
        else:  # Unknown exception
            self.code = SystemErrCode.server_internal_error.code
            self.message = SystemErrCode.server_internal_error.message

    def format(self):
        return dict(
            trace_id=self.trace_id,
            code=self.code,
            message=self.message,
            detail=self.detail,
            result=self.result,
            #
            timestamp=int(time.time()),
        )
