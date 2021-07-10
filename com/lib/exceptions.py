import json


class CodeError(Exception):
    """
    Code error
    """
    pass


class ApiException(Exception):
    """
    Api exception
    """

    def __init__(self, errcode, detail: str = None):
        self.code = errcode.code
        self.message = errcode.message
        #
        self.detail = detail

    def __str__(self):
        info = dict(code=self.code, message=self.message)
        if self.detail is not None:
            info.update(detail=self.detail)

        return json.dumps(info, ensure_ascii=False)
