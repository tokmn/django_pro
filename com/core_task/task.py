import datetime
import os
import sys
import inspect

from .management.task import taskapi
from lib.exceptions import CodeError


class TaskManager:
    """
    Manage the action of the task, such as: add, update, cancel
    """

    def __init__(self, *args, **kwargs):
        self.task_func = None
        self._task_name = None

    @staticmethod
    def _check_task_func(task_func):
        """
        Check task func
        """
        if not task_func or not inspect.isfunction(task_func):
            raise CodeError("task func required")

    @property
    def task_name(self):
        """
        Task name of task func
        """
        if not self._task_name:
            self._task_name = self._gen_task_name(self.task_func)
        return self._task_name

    def __call__(self, task_func, *args, **kwargs):
        self.set_task_func(task_func)
        return self.task_func

    def set_task_func(self, task_func):
        self._check_task_func(task_func)
        self.task_func = task_func
        self._register_actions()
        # Set task flag
        self.task_func._x_task = True

    def _register_actions(self):
        """
        Register action for task func
        """
        actions = [
            self.add,
            self.update,
            self.cancel,
            #
            self.execute,
        ]
        for action in actions:
            setattr(self.task_func, action.__name__, action)

    def _gen_task_name(self, task_func):
        module_name = task_func.__module__
        if module_name == "__main__":
            main_file = getattr(sys.modules[module_name], "__file__")
            module_name = os.path.splitext(os.path.basename(main_file))[0]
        return "{}:{}".format(module_name, task_func.__name__)

    def execute(self, *args, **kwargs):
        """
        Execute task func
        """
        return self.task_func(*args, **kwargs)

    def add(
            self,
            task_attr: str,
            *args,
            run_at: datetime.datetime = None,
            extra: dict = None,
            remark: str = None,
            **kwargs
    ):
        taskapi.add_task(task_name=self.task_name, task_attr=task_attr, run_at=run_at,
                         task_args=args, task_kwargs=kwargs, extra=extra, remark=remark)

    def update(
            self,
            task_attr: str,
            *args,
            run_at: datetime.datetime = None,
            extra: dict = None,
            remark: str = None,
            **kwargs
    ):
        taskapi.update_task(task_name=self.task_name, task_attr=task_attr, run_at=run_at,
                            task_args=args, task_kwargs=kwargs, extra=extra, remark=remark)

    def cancel(self, task_attr):
        taskapi.cancel_task(self.task_name, task_attr)


task_manager = TaskManager
