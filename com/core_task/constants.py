from enum import Enum


class TaskStatus(Enum):
    WAITING = 'waiting'
    PENDING = 'pending'
    RUNNING = 'running'
    SUCCESS = 'success'
    FAILED = 'failed'
