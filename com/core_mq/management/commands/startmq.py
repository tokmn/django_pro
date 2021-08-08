import logging
from threading import Thread

from django.conf import settings
from django.core.management.base import BaseCommand

from core_mq.rabbitmq.consumer import Consumer

#
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Start mq consumer command'

    def handle(self, *args, **options):
        logger.info('Start mq consumer...')
        for exchange, info in settings.RABBITMQ_CONF['exchange_map'].items():
            queue_info_list = info.get('queue_info_list') or [
                dict(queue=exchange, count=2)
            ]
            for queue_info in queue_info_list:
                queue = queue_info['queue']
                count = queue_info.get('count', 2)
                for i in range(count):
                    Thread(target=Consumer(queue).run).start()
                    logger.info(f'Consumer(exchange:{exchange}, queue:{queue}, count:{i + 1}/{count}) start...')
        logger.info('Start all mq consumer successfully.')
