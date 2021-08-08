from django.apps import AppConfig

from core_mq.rabbitmq import producer


class CoreMqConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core_mq'

    # def ready(self):
    #     producer.setup()
