import logging
from logging import LogRecord

from lib.threadutils import thread_ctx


class ContextFilter(logging.Filter):
    """
    Set custom context for log record
    """

    def filter(self, record) -> bool:
        record.x_trace_id = thread_ctx.get('x_trace_id')
        return True


class DiscardFilter(logging.Filter):
    """
    Discard log
    """

    def filter(self, record):
        return False


class ReportFilter(logging.Filter):
    """
    Report specific log
    """

    def filter(self, record: LogRecord) -> bool:
        """
        Error log and above it or exc_info exists, will be filtered and reported

        :param record:
        :return:
        """
        if record.levelno >= logging.ERROR or record.exc_info:
            # TODO add report service
            pass

        return True
