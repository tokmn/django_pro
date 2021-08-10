import fcntl
from contextlib import contextmanager


@contextmanager
def file_io_lock(filename):
    """
    Perform the lock operation on file descriptor fd

    :param filename:
    :return:
    """

    def acquire(_fd):
        """Acquire an exclusive lock"""
        fcntl.flock(_fd, fcntl.LOCK_EX)

    def release(_fd):
        """Unlock"""
        fcntl.flock(_fd, fcntl.LOCK_UN)

    with open(filename, 'w') as f:
        fd = f.fileno()
        acquire(fd)
        yield  # Perform the decorated func
        release(fd)
