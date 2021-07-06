import threading


class ThreadCtx:
    """
    Thread context
    """

    _thread_local = threading.local()

    def __init__(self):
        self.key = 'x_thread_ctx_key'

    def _get(self):
        return getattr(self._thread_local, self.key, {})

    def _set(self, _items: dict):
        setattr(self._thread_local, self.key, _items)

    def set(self, name: str, value):
        _items = self._get()
        _items[name] = value
        self._set(_items)

    def get(self, name: str):
        return self._get().get(name)

    def clear(self):
        if hasattr(self._thread_local, self.key):
            delattr(self._thread_local, self.key)


thread_ctx = ThreadCtx()
