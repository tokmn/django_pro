from functools import wraps
from django.conf import settings

from .rabbitmq import producer


def run_with_mq(priority: int = None):
    """
    Use default exchange: task
    """
    exchange = settings.RABBITMQ_CONF['exchange_map']['task']['exchange_info']['exchange']

    def out_wrapper(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            message = dict(
                module_name=func.__module__,
                func_name=func.__name__,
                args=args,
                kwargs=kwargs,
            )
            producer.publish(exchange=exchange, message=message, priority=priority)
            return

        wrapper.original = func
        return wrapper

    return out_wrapper
