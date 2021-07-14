import redis
from redis import lock

from lib.serializers import json_decode, json_encode


class Client:
    def __init__(
            self, host: str = 'localhost',
            port: int = 6379,
            db: int = 0,
            password: str = None,
            max_connections: int = None,
            key_prefix: str = None,
            set_key_default_timeout: bool = True,
            key_default_timeout: int = None,
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
        self.key_default_timeout = None
        if set_key_default_timeout:
            if key_default_timeout is None:
                key_default_timeout = 60 * 60 * 24 * 3  # seconds
            self.key_default_timeout = key_default_timeout
        # Key's default version
        self.default_version = 1

    def _encode(self, obj):
        """Serialize python obj to a string"""
        return json_encode(obj)

    def _decode(self, s):
        """Deserialize value to a python obj"""
        return json_decode(s)

    def _make_key(self, key, version=None):
        """Add prefix and version"""
        if version is None:
            version = self.default_version
        return '{}:{}:{}'.format(self.key_prefix, version, key)

    def shared_and_distributed_lock(self, name, timout=None):
        """
        Shared and distributed lock base on redis
        """
        return lock.Lock(self._redis, name, timeout=timout)

    def set(self, name, value, ex=None, nx=False, version=None):
        """
        Set the string value of a key
        """
        key = self._make_key(name, version)
        value = self._encode(value)
        # Set default timeout if possible
        if ex is None:
            ex = self.key_default_timeout
        return self._redis.set(key, value, ex=ex, nx=nx)

    def get(self, name, version=None):
        """
        Get the value of a key
        """
        key = self._make_key(name, version)
        value = self._redis.get(key)
        if value is None:
            return value
        return self._decode(value)

    def delete(self, name, version=None):
        """
        Delete a key
        """
        key = self._make_key(name, version)
        return self._redis.delete(key)

    def exists(self, name, version=None):
        """
        Determine if a key exists
        """
        key = self._make_key(name, version)
        return self._redis.exists(key) == 1

    def expire(self, name, seconds=None, version=None):
        """
        Set a key's time to live in seconds
        """
        key = self._make_key(name, version)
        return self._redis.expire(key, seconds)
