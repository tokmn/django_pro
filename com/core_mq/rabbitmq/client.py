import logging
import pika

from django.conf import settings
from pika import exceptions as pika_exceptions

from lib.threadutils import ThreadCtx

#
mq_thread_ctx = ThreadCtx(attr='x_rabbitmq_attr')

logger = logging.getLogger(__name__)


class MQClient:
    """
    Pika is not thread safe. Use a BlockingConnection per-thread.

    """

    def __init__(
            self,
            host: str = 'localhost',
            port: int = 5672,
            vhost: str = '/local',
            username: str = 'username',
            password: str = 'password',
            heartbeat: int = 0,
            exchange_map: dict = None,
            max_priority: int = 10
    ):
        credentials = pika.PlainCredentials(username=username, password=password)
        parameters = dict(
            host=host, port=port, virtual_host=vhost, heartbeat=heartbeat, credentials=credentials
        )
        self.parameters = pika.ConnectionParameters(**parameters)
        #
        self.max_priority = max_priority
        self._init(exchange_map or {})

    def _init(self, exchange_map: dict):
        channel = self.get_channel()
        arguments = {'x-max-priority': self.max_priority}
        for exchange, info in exchange_map.items():
            channel.exchange_declare(**info['exchange_info'])
            # Set queue for exchange
            queue_info_list = info.get('queue_info_list') or [
                dict(queue=exchange, routing_keys=[f'{exchange}.#'])
            ]
            for queue_info in queue_info_list:
                queue = queue_info['queue']
                channel.queue_declare(queue=queue, durable=True, arguments=arguments)
                # Bind routing for queue
                for routing_key in queue_info['routing_keys']:
                    channel.queue_bind(exchange=exchange, queue=queue, routing_key=routing_key)

        self.close()
        logger.debug('MQ init successfully.')

    def connect(self):
        connection = pika.BlockingConnection(self.parameters)
        mq_thread_ctx.set('connection', connection)
        return connection

    def ping_ok(self, connection):
        try:
            if connection and connection.process_data_events():
                return True
        except (pika_exceptions.ConnectionClosedByBroker, pika_exceptions.StreamLostError):
            pass
        return False

    def is_alive(self):
        connection = mq_thread_ctx.get('connection')
        if connection and connection.is_open and self.ping_ok(connection):
            return True
        return False

    @property
    def connection(self):
        connection = mq_thread_ctx.get('connection')
        if not self.ping_ok(connection):
            connection = self.connect()
        return connection

    def close(self):
        connection = mq_thread_ctx.get('connection')
        if self.ping_ok(connection):
            connection.close()
        mq_thread_ctx.clear()

    def _make_channel(self):
        channel = self.connection.channel()
        mq_thread_ctx.set('channel', channel)
        return channel

    def get_channel(self, producer: bool = False):
        channel = mq_thread_ctx.get('channel')
        if not self.is_alive() or not channel:
            channel = self._make_channel()
            if producer:
                channel.confirm_delivery()
            else:
                channel.basic_qos(prefetch_count=1)
        return channel


"""
### MQ client config example:

{
    'host': 'localhost',
    'port': 5672,
    'vhost': '/local',
    'username': 'username',
    'password': 'password',
    'heartbeat': 0,
    #
    'exchange_map': {
        'task': {
            'exchange_info': {
                'exchange': 'task',
                'exchange_type': 'topic',
                'durable': True,
            },
            'queue_info_list': [
                {
                    'queue': 'task',
                    'routing_keys': ['task.#'],
                    'count': 3,
                },
            ]
        }
    }
}

"""

mq_client = MQClient(**settings.RABBITMQ_CONF)
