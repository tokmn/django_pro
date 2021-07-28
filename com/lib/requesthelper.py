import json
import logging
import requests
import time
from functools import wraps

#
logger = logging.getLogger(__name__)


def wrap_response(func):
    @wraps(func)
    def wrapper(self, url, **kwargs):
        request_info = '{} {} {}'.format(func.__name__.upper(), url, kwargs)
        logger.info('Prepare start request, {}'.format(request_info))
        #
        result = None
        response = None
        decode_response_content = None
        try:
            request_at = time.time()
            response = func(self, url, **kwargs)
            decode_response_content = response.content.decode('utf-8')
            result = json.loads(decode_response_content)
        except requests.exceptions.ContentDecodingError:
            logger.error('Request failed, response content deocde error. request info: {}, response content: {}'.format(
                request_info, response.content))
        except requests.exceptions.ConnectionError:
            logger.error('Request failed, connect error. request info: {}'.format(request_info))
        except requests.exceptions.ReadTimeout:
            logger.error('Request failed, read timout. request info: {}'.format(request_info))
        except requests.exceptions.InvalidURL:
            logger.error('Request failed, invalid url. request info: {}'.format(request_info))
        except json.decoder.JSONDecodeError:
            logger.error('Request failed, json decode error. request info: {}, decode response content: {}'.format(
                request_info, decode_response_content))
        except:
            logger.exception('Request failed. request info: {}'.format(request_info))
        else:
            logger.info('Request succssfully, duration: {}s. request info: {}, result: {}'.format(
                int(time.time() - request_at), request_info, result))

        return result

    return wrapper


class RequestHelper:
    """
    Request helper
    """

    def __init__(self):
        self.default_headers = {"Content-Type": "application/json"}
        self.default_timeout = 2

    def _check_timeout(self, kwargs: dict):
        if 'timeout' not in kwargs:
            kwargs.setdefault('timeout', self.default_timeout)

    def _check_headers(self, kwargs: dict):
        headers = kwargs.get('headers', {})
        if not headers:
            kwargs.setdefault('headers', self.default_headers)
        else:
            for name, value in self.default_headers.items():
                if name not in headers:
                    headers.setdefault(name, value)

    @wrap_response
    def get(self, url, params=None, **kwargs):
        self._check_timeout(kwargs)
        response = requests.get(url, params, **kwargs)
        return response

    @wrap_response
    def post(self, url, data=None, **kwargs):
        self._check_timeout(kwargs)
        self._check_headers(kwargs)
        response = requests.post(url, data=data, **kwargs)
        return response


request_helper = RequestHelper()
