import datetime
import os
import sys
import inspect

from .management.task import taskapi
from lib.exceptions import CodeError


class CronTask:
    def __init__(self, task_func):
        self._check_task_func(task_func)
        self.task_func = task_func
        self.task_name = self._gen_task_name(task_func)
        self.task_func._cron_task = True

    def __call__(self, *args, **kwargs):
        return self.task_func(*args, **kwargs)

    @staticmethod
    def _check_task_func(task_func):
        """
        Check task func
        """
        if not inspect.isfunction(task_func):
            raise CodeError('task func required')

    def _gen_task_name(self, task_func):
        """
        Generate task name
        """
        module_name = task_func.__module__
        if module_name == '__main__':
            main_file = getattr(sys.modules[module_name], '__file__')
            module_name = os.path.splitext(os.path.basename(main_file))[0]
        return '{}:{}'.format(module_name, task_func.__name__)

    def cron_task(
            self,
            task_attr,
            run_at: datetime.datetime = None,
            extra: dict = None,
            remark: str = None
    ):
        return _TaskController(task_name=self.task_name,
                               task_attr=task_attr, run_at=run_at, extra=extra, remark=remark)


class _TaskController:
    def __init__(self, task_name, task_attr, run_at, extra, remark):
        self.task_name = task_name
        self.task_attr = task_attr
        self.run_at = run_at
        self.extra = extra
        self.remark = remark
        #
        self.task_args = None
        self.task_kwargs = None

    def params(self, *args, **kwargs):
        self.task_args = args
        self.task_kwargs = kwargs
        return self

    def add(self):
        taskapi.add_task(task_name=self.task_name,
                         task_attr=self.task_attr,
                         run_at=self.run_at,
                         task_args=self.task_args,
                         task_kwargs=self.task_kwargs,
                         extra=self.extra,
                         remark=self.remark
                         )

    def update(self):
        taskapi.update_task(task_name=self.task_name,
                            task_attr=self.task_attr,
                            run_at=self.run_at,
                            task_args=self.task_args,
                            task_kwargs=self.task_kwargs,
                            extra=self.extra,
                            remark=self.remark
                            )

    def cancel(self):
        taskapi.cancel_task(self.task_name, self.task_attr)


cron_task = CronTask
