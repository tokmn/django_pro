from functools import wraps
from django.http.request import HttpRequest

from utils.errorcode import SystemErrCode
from utils.exceptions import ApiException, CodeError


def validate_form(form_class):
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not isinstance(request, HttpRequest):
                raise CodeError("This decorator is only used to decorate view methods of FBV or CBV")
            form = form_class(getattr(request, 'X_REQUEST_DATA'), getattr(request, 'X_UPLOAD_FILES'))
            if not form.is_valid():
                raise ApiException(errcode=SystemErrCode.INVALID_REQUEST_DATA, detail=form.errors)
            return func(request, *args, **kwargs, cleaned_data=form.cleaned_data)

        return wrapper

    return decorator
