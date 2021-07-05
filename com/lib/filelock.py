import fcntl

from contextlib import contextmanager


@contextmanager
def file_io_lock(filename):
    """
    通过指定文件的文件描述符执行文件控制（锁）

    :param filename:
    :return:
    """

    with open(filename, "w") as f:
        # 排它锁
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        yield
        # 锁释放
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
