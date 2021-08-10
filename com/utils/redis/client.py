import logging
import redis

from .lock import Lock
from utils.serializers import json_decode, json_encode

logger = logging.getLogger(__name__)


class Client:
    def __init__(
            self, host: str = 'localhost',
            port: int = 6379,
            db: int = 0,
            password: str = None,
            max_connections: int = None,
            key_prefix: str = None,
            set_key_ex: bool = True,
            key_default_ex: int = None,
    ):
        if max_connections is None:
            max_connections = 2 ** 4

        # Create a connection pool
        pool = redis.ConnectionPool(
            host=host, port=port, db=db, password=password, socket_timeout=3,
            max_connections=max_connections, decode_responses=True
        )
        # Create redis client
        self._redis = redis.StrictRedis(connection_pool=pool)
        # Key prefix
        self.key_prefix = key_prefix if key_prefix else ''
        # It's recommend that each key has a default timeout
        self.key_default_ex = None
        if set_key_ex:
            if key_default_ex is None:
                key_default_ex = 60 * 60 * 24 * 7  # seconds
            self.key_default_ex = key_default_ex
        # Key's default version
        self.default_version = 1

        logger.debug('Redis client init successfully')

    def _encode(self, value):
        """
        Serialize python obj to a string
        """
        if isinstance(value, bool) or not isinstance(value, int):
            return json_encode(value)
        return value

    def _decode(self, value):
        """
        Deserialize value to a python obj
        """
        try:
            value = int(value)
        except (ValueError, TypeError):
            value = json_decode(value)
        return value

    def _make_key(self, key, version=None):
        """
        Add prefix and version
        """
        if version is None:
            version = self.default_version
        _key = '{}:{}:{}'.format(self.key_prefix, version, key)
        return _key

    def shared_and_distributed_lock(self, name, timeout=None):
        """
        Shared and distributed lock base on redis
        """
        _name = '{}{}:{}'.format(self._make_key(''), '_shared_lock', name)
        return Lock(self._redis, _name, timeout=timeout)

    def set(self, key, value, ex=None, nx=False, version=None):
        """
        Set the string value of a key
        """
        _key = self._make_key(key, version)
        value = self._encode(value)
        # Set default expires if possible (# seconds)
        if ex is None:
            ex = self.key_default_ex
        return self._redis.set(_key, value, ex=ex, nx=nx)

    def get(self, key, version=None):
        """
        Get the value of a key
        """
        _key = self._make_key(key, version)
        value = self._redis.get(_key)
        if value is None:
            return value
        return self._decode(value)

    def delete(self, key, version=None):
        """
        Delete a key
        """
        _key = self._make_key(key, version)
        return self._redis.delete(_key)

    def exists(self, key, version=None):
        """
        Determine if a key exists
        """
        _key = self._make_key(key, version)
        return self._redis.exists(_key) == 1

    def expire(self, key, seconds=None, version=None):
        """
        Set a key's time to live in seconds
        """
        _key = self._make_key(key, version)
        return self._redis.expire(_key, seconds)

    def ttl(self, key, version=None):
        """
        Get the time to live for a key

        - Returns -1 if the key exists but has no associated expire.
        - Returns -2 if the key does not exist.
        """
        _key = self._make_key(key, version)
        return self._redis.ttl(_key)
