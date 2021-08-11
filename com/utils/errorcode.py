class ErrorCode:
    """
    Error code
    """

    __slots__ = ["code", "message"]

    def __init__(self, code, message):
        self.code = code
        self.message = message


class SystemErrCode:
    """
    System error code
    """

    SUCCESS = ErrorCode(code=0, message="ok")
    INTERNAL_SERVER_ERROR = ErrorCode(code=1, message="internal server error, please try again later.")
    INVALID_REQUEST = ErrorCode(code=2, message="invalid request")
    INVALID_REQUEST_DATA = ErrorCode(code=3, message="invalid request data")
