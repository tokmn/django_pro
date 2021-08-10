import json
import logging
import time
import uuid

from django.http.request import HttpRequest
from django.http.request import MultiValueDict, QueryDict
from django.utils.deprecation import MiddlewareMixin

from utils.threadutils import thread_ctx
from utils.errorcode import SystemErrCode
from utils.exceptions import ApiException

#
logger = logging.getLogger(__name__)


class GateMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """
        Add extra attributes for request

        """

        request.X_INCOMING_AT = time.time()
        # Must be prioritized to set X_TRACE_ID
        request.X_TRACE_ID = uuid.uuid4()
        thread_ctx.set('x_trace_id', request.X_TRACE_ID)  # Set thread context for current request
        #
        self.load_request_data_and_files(request)

        log_request_info(request)

    def process_response(self, request, response):
        clear_thread_ctx_for_request(request)
        return response

    def load_request_data_and_files(self, request: HttpRequest):
        """
        Support content type of post:
            - application/x-www-form-urlencoded
            - multipart/form-data
            - application/json

        """

        x_exception = None
        x_request_data, x_upload_files = QueryDict(), MultiValueDict()

        if request.method == 'GET':
            x_request_data = request.GET

        elif request.content_type == 'application/x-www-form-urlencoded':
            x_request_data = request.POST

        elif request.content_type == 'multipart/form-data':
            x_request_data, x_upload_files = request.parse_file_upload(request.META, request)

        elif request.content_type == 'application/json':
            decoded_body = request.body.decode()
            try:
                x_request_data = json.loads(decoded_body)
            except:
                logger.exception(f'deserialize body failed, body: {decoded_body}')
                x_exception = ApiException(SystemErrCode.INVALID_REQUEST,
                                           detail='deserialize body failed')
        else:
            x_exception = ApiException(SystemErrCode.INVALID_REQUEST,
                                       detail='content-type unsupported')

        request.X_EXCEPTION = x_exception
        request.X_REQUEST_DATA = x_request_data
        request.X_UPLOAD_FILES = x_upload_files


def log_request_info(request: HttpRequest):
    request_info = {
        'METHOD': request.method,
        'SCHEME': request.scheme,
        'PATH': request.path,
        'CONTENT_TYPE': request.content_type,
        'CONTENT_LENGTH': request.headers.get('Content-Length'),
        'USER_AGENT': request.headers.get('User-Agent'),
        'X_REQUEST_DATA': getattr(request, 'X_REQUEST_DATA', None),
    }
    if hasattr(request, 'X_UPLOAD_FILES'):
        request_info['X_UPLOAD_FILES'] = get_info_for_upload_files(request.X_UPLOAD_FILES)

    logger.info(request_info)
    # Debug
    logger.debug(str(request.headers))


def get_info_for_upload_files(upload_files: MultiValueDict):
    info = []
    for field in upload_files.keys():
        files = []
        for o in upload_files.getlist(field):
            files.append(dict(name=o.name,
                              size=o.size,  # Unit: byte
                              type=o.content_type))
        info.append(dict(field=field, files=files))

    return info


def clear_thread_ctx_for_request(request):
    """
    Record duration for request before clear

    """

    duration = time.time() - request.X_INCOMING_AT
    logger.info('', extra={'duration': f'{duration:.3f}'})

    thread_ctx.clear()
