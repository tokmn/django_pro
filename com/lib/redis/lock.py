import threading
import time
import uuid
import weakref

from threading import Thread

from redis.lock import Lock as RedisLock
from redis.exceptions import LockError


class Lock(RedisLock):
    """
    Redis lock's subclass.

    Add lock renewal
    """

    def __init__(self, redis, name, timeout: int = None):
        """
        Create a new Lock instance

        :param redis:
            Redis client
        :param name:
            The name of locked key
        :param timeout:
            The timeout of lock
        """

        self.default_ex_timeout = 3
        # Timeout must be set
        if timeout is None or timeout < self.default_ex_timeout:
            timeout = self.default_ex_timeout  # seconds
        super().__init__(redis, name, timeout=timeout)

    def acquire(self, *args, **kwargs):
        """
        Support a shared and distributed lock
        """
        token = uuid.uuid1().hex

        while True:
            if self.redis.set(self.name, token, nx=True, ex=self.timeout):
                self.local.token = token
                self._start_lock_renewal(token)
                return True

    def release(self):
        """
        Relase Lock
        """
        self._stop_lock_renewal()
        super().release()

    @staticmethod
    def _lock_renewal(self_ref, token, _lock_renewal_stop):
        """
        Renew the lock key in redis
        """
        while not _lock_renewal_stop.wait(timeout=1):
            self = self_ref()
            if self is None:
                break
            _token = self.redis.get(self.name)
            if not _token or _token != token:
                break
            remaining_time = self.redis.ttl(self.name)
            if remaining_time < 0:
                break
            elif remaining_time < self.default_ex_timeout:
                try:
                    # Add additional time
                    self.extend(self.default_ex_timeout)
                # Maybe self.local has no attribute 'token', if released
                except (AttributeError, LockError):
                    break

    def _start_lock_renewal(self, token):
        """
        Start one thread for lock renewal
        """
        _lock_renewal_stop = threading.Event()
        self._lock_renewal_stop = _lock_renewal_stop
        _lock_renewal_thread = Thread(
            target=self._lock_renewal, args=(weakref.ref(self), token, _lock_renewal_stop)
        )
        _lock_renewal_thread.daemon = True
        _lock_renewal_thread.start()

    def _stop_lock_renewal(self):
        """
        Stop lock renewal
        """
        try:
            self._lock_renewal_stop.set()
        except AttributeError:
            pass
