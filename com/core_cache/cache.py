from django.conf import settings

from lib.redis import Cache as RedisCache

cache = RedisCache(**settings.REDIS_CONF)
