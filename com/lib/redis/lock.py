import time
from threading import Thread

from redis.lock import Lock as RedisLock


class Lock(RedisLock):
    """
    Redis lock's subclass.

    Add monitor to Preventing unexpected timeout.
    """

    def do_acquire(self, token):
        if self.redis.get(self.name):
            return False
        result = super().do_acquire(token)
        if result is True:
            self.update_timeout(token)
        return result

    def _update_timeout(self, token):
        """
        if locked key exists and has timeout, will be updated constantly
        """
        while 1:
            _token = self.redis.get(self.name)
            if not _token or _token != token:
                break
            remaining_time = self.redis.ttl(self.name)
            if remaining_time < 0:
                break
            elif remaining_time < 3:
                self.redis.expire(self.name, remaining_time + 3)
            time.sleep(1)

    def update_timeout(self, token):
        """
        Start daemon thread to update timeout
        """
        Thread(target=self._update_timeout,
               args=(token.decode(),),
               daemon=True).start()
