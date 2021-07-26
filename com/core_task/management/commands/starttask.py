import logging
import signal

from ..executor import run, stop_task_executor
from django.core.management.base import BaseCommand

#
logger = logging.getLogger(__name__)


def stop_task_handler(signum, _):
    logger.info('Receive a stop signal, signum:{}'.format(signum))
    stop_task_executor()


def register_signal():
    for signum in [
        signal.SIGINT,
        signal.SIGTERM,
    ]:
        signal.signal(signum, stop_task_handler)


class Command(BaseCommand):
    help = 'Start task command'

    def add_arguments(self, parser):
        parser.add_argument(
            '--thread_count', default=4, help='The count of thread',
        )

    def handle(self, *args, **options):
        thread_count = options['thread_count']
        register_signal()
        run(thread_count=thread_count)
