from django.conf import settings

from utils.redis import Cache as RedisCache

cache = RedisCache(**settings.REDIS_CONF)
