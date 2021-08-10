import logging
from importlib import import_module

from .client import mq_client
from utils.serializers import json_decode

#
logger = logging.getLogger(__name__)

functions_cache = {}


class Consumer:
    def __init__(self, queue):
        self.queue = queue

    def get_func(self, module_name, func_name):
        func_key = module_name + "." + func_name
        if func_key in functions_cache:
            func = functions_cache.get(func_key)
        else:
            module = import_module(module_name)
            func = getattr(module, func_name)
            functions_cache[func_key] = func
        return func

    def on_message_callback(self, ch, method, properties, body):
        queue_info = f'[{method.exchange}->{self.queue}->{method.routing_key}]'
        message = body.decode()
        try:
            message = json_decode(message)

            module_name, func_name = message["module_name"], message["func_name"]
            func = self.get_func(module_name, func_name)
            args, kwargs = message['args'], message['kwargs']
            func.original(*args, **kwargs)
        except:
            logger.exception(f'{queue_info} Consuming failed. message:{message}')
        else:
            logger.info(f'{queue_info} Consumeing successfully. message:{message}')
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def run(self):
        channel = mq_client.get_channel()
        try:
            channel.basic_consume(
                queue=self.queue,
                auto_ack=False,
                on_message_callback=self.on_message_callback
            )
            channel.start_consuming()
        except:
            logger.exception('Run consumer failed.')
