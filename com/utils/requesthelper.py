import logging
import time
from functools import wraps
from json import loads
from json.decoder import JSONDecodeError
from requests import request
from requests import exceptions as request_exception

#
logger = logging.getLogger(__name__)


def wrap_response(func):
    @wraps(func)
    def wrapper(method, url, **kwargs):
        request_info = '{} {} {}'.format(method.upper(), url, kwargs)
        logger.info(f'Prepare start request, request info: {request_info}')
        #
        result = None
        response = None
        decode_response_content = None
        try:
            request_at = time.time()
            response = func(method, url, **kwargs)
            decode_response_content = response.content.decode('utf-8')
            result = loads(decode_response_content)
        except request_exception.ContentDecodingError:
            logger.error(f'Request failed, response content deocde error. '
                         f'request info: {request_info}, response content: {response.content}')
        except request_exception.ConnectionError:
            logger.error(f'Request failed, connect error. request info: {request_info}')
        except request_exception.ReadTimeout:
            logger.error(f'Request failed, read timout. request info: {request_info}')
        except request_exception.InvalidURL:
            logger.error(f'Request failed, invalid url. request info: {request_info}')
        except JSONDecodeError:
            logger.error(f'Request failed, json decode error. '
                         f'request info: {request_info}, decode response content: {decode_response_content}')
        except:
            logger.exception('Request failed. request info: {}'.format(request_info))
        else:
            logger.info(f'Request succssfully, duration: {int(time.time() - request_at)}s. '
                        f'request info: {request_info}, result: {result}')

        return result

    return wrapper


@wrap_response
def _make_request(method, url, **kwargs):
    response = request(method, url, **kwargs)
    return response


class RequestHelper:
    """
    Request helper
    """

    def __init__(self):
        self.default_headers = {"Content-Type": "application/json"}
        self.default_timeout = 2

    def _set_default_timeout(self, kwargs: dict):
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.default_timeout

    def _set_default_headers(self, kwargs: dict):
        headers = kwargs.get('headers', {})
        if headers:
            for name, value in self.default_headers.items():
                if name not in headers:
                    headers[name] = value
        else:
            kwargs['headers'] = self.default_headers

    def get(self, url, params=None, **kwargs):
        self._set_default_timeout(kwargs)
        return _make_request('get', url, params=params, **kwargs)

    def post(self, url, data=None, **kwargs):
        self._set_default_timeout(kwargs)
        self._set_default_headers(kwargs)
        return _make_request('post', url, data=data, **kwargs)


request_helper = RequestHelper()
