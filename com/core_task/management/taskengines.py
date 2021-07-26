from datetime import datetime
from django.db.models import F

from core_task.constants import TaskStatus
from core_task.models import Task

#
DEFAULT_WAITING_TASK_COUNT = 20


class TaskEngine:
    def create_task(self, *args, **kwargs):
        """
        Create new task
        :param args:
        :param kwargs:
        :return:
        """
        pass

    def update_task(self, *args, **kwargs):
        """
        Update task
        :param args:
        :param kwargs:
        :return:
        """

    def delete_task(self, *args, **kwargs):
        """
        Delete task
        :param args:
        :param kwargs:
        :return:
        """

    def get_waiting_tasks(self, *args, **kwargs):
        """
        Get waiting task
        :param args:
        :param kwargs:
        :return:
        """

    def retry_task(self, *args, **kwargs):
        """
        Retry task
        :param args:
        :param kwargs:
        :return:
        """


class MySQLTaskEngine(TaskEngine):
    """
    Task engine base on MySQL

    The status of task:

    - waiting -> [DELETED]
    - waiting -> pending
    - pending -> [DELETED]
    - pending -> running
    - running -> [DELETED]
    - running -> waiting[RETRY]
    - running -> success
    - running -> failed
    - success -> [DELETED]
    - failed -> [DELETED]

    """

    def create_task(self, task_name, task_attr, **kwargs):
        task = Task.objects.create(task_name=task_name, task_attr=task_attr, **kwargs)
        return task

    def update_task(self, task_name, task_attr, filter_kwargs: dict = None, update_kwargs: dict = None):
        if not filter_kwargs:
            filter_kwargs = dict(task_name=task_name, task_attr=task_attr)
        else:
            filter_kwargs.update(task_name=task_name, task_attr=task_attr)

        if not update_kwargs:
            update_kwargs = {}
        update_kwargs.update(updated_at=datetime.now())

        rows = Task.objects.filter(**filter_kwargs).update(**update_kwargs)
        return rows

    def delete_task(self, task_name, task_attr):
        deleted, rows = Task.objects.filter(task_name=task_name, task_attr=task_attr).delete()
        return deleted, rows

    def get_waiting_tasks(self):
        # Waiting tasks
        waiting_tasks = []

        task_set = Task.objects.filter(
            status=TaskStatus.WAITING.value,
            run_at__lte=datetime.now(),
        ).order_by('run_at')[:DEFAULT_WAITING_TASK_COUNT]

        # Add optimistic lock
        for task in task_set:
            rows = Task.objects.filter(
                pk=task.pk, status=TaskStatus.WAITING.value, version=task.version
            ).update(
                status=TaskStatus.PENDING.value,
                version=F('version') + 1,
                updated_at=datetime.now(),
            )
            if bool(rows):
                waiting_tasks.append(task)

        return waiting_tasks

    def retry_task(self, task_id, next_run_at, **kwargs):
        Task.objects.filter(pk=task_id, status=TaskStatus.RUNNING.value).update(
            status=TaskStatus.WAITING.value,
            run_at=next_run_at,
            updated_at=datetime.now(),
            **kwargs
        )


engine = MySQLTaskEngine()
