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

    success = ErrorCode(code=0, message="ok")
    server_internal_error = ErrorCode(code=1, message="服务器开小差啦，请稍后再试！")
