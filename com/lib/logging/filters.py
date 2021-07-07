import logging

from lib.threadutils import thread_ctx


class ContextFilter(logging.Filter):
    """
    Set custom context for log record
    """

    def filter(self, record) -> bool:
        record.x_trace_id = thread_ctx.get('x_trace_id')
        return True
