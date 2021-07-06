class CodeError(Exception):
    """
    Code error
    """
    pass


class ApiException(Exception):
    """
    Api exception
    """

    def __init__(self, errorcode, detail: str = None):
        self.code = errorcode.code
        self.message = errorcode.message
        #
        self.detail = detail
