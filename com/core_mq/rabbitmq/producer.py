import logging
import pika

from .client import mq_client
from lib.serializers import json_encode

#
logger = logging.getLogger(__name__)


def publish(exchange, message, routing_key: str = None, priority: int = None):
    routing_key = routing_key or f'{exchange}.default'
    publish_info = dict(exchange=exchange, routing_key=routing_key, message=message)
    try:
        if not isinstance(message, str):
            message = json_encode(message)
        channel = mq_client.get_channel(producer=True)
        channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
                priority=priority or max([priority, mq_client.max_priority]),
            ),
            mandatory=True
        )
    except:
        logger.exception(f'Publish mq message failed, unexpected error. {publish_info}')
    else:
        logger.info(f'Publish mq message successfully. {publish_info}')
