import io
import json
import logging
import time
import traceback

from decimal import Decimal
from logging import LogRecord

from lib.serializers import JsonEncoder

#
DEFAULT_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DEFAULT_MSEC_FORMAT = '%s,%03d'


class JsonFormatter(logging.Formatter):
    def get_format_time(self, record):
        ct = self.converter(record.created)
        _format_time = time.strftime(DEFAULT_TIME_FORMAT, ct)
        format_time = DEFAULT_MSEC_FORMAT % (_format_time, record.msecs)

        return format_time

    def get_message(self, record):
        message = str(record.msg)
        if record.args:
            message = message % record.args

        return message

    def get_format_exception(self, ei):
        buf = io.StringIO()
        traceback.print_exception(ei[0], ei[1], ei[2], None, buf)
        s = buf.getvalue()
        buf.close()

        return s

    def wrap_data(self, record: LogRecord):
        data = {
            'datetime': self.get_format_time(record),
            'level': record.levelname,
            'trace_id': getattr(record, 'x_trace_id', None),
            'location': '{}@{}'.format(record.name, record.lineno),
        }
        if record.msg:
            if isinstance(record.msg, (dict, list, set, tuple, int, float, Decimal)):
                message = record.msg
            else:
                message = self.get_message(record)
            data['message'] = message

        if record.exc_info:
            data['exc_info'] = self.get_format_exception(record.exc_info)

        if hasattr(record, 'duration'):
            data['duration'] = record.duration

        return data

    def format(self, record):
        data = self.wrap_data(record)

        return json.dumps(data, ensure_ascii=False, cls=JsonEncoder)
