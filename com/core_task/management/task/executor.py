import datetime
import logging
import time
import traceback
from importlib import import_module
from threading import Thread

from ...constants import TaskStatus
from ...models import Task
from .taskapi import engine
from lib.threadutils import thread_ctx

#
logger = logging.getLogger(__name__)

# Sleep time
executor_idle_seconds = 2
# Thread count
default_thread_count = 4
#
# Status
is_running = False
# Signal
stop_signal = False
# task map {task_name: task_func, ...}
task_func_map = {}


def stop_task_executor():
    global stop_signal, is_running
    stop_signal = True
    is_running = False


def import_task_func(task_name):
    module_name, func_name = task_name.split(':')
    task_func = getattr(import_module(module_name), func_name)
    task_func_map[task_name] = task_func
    logger.info('Import task func successfully. task_name: {}'.format(task_name))

    return task_func


class TaskExecutor(Thread):
    """
    Task executor
    """

    def execute_task(self, task: Task):
        """
        Parse task func and execute
        """
        try:
            logger.info('Execute task, task info: {}'.format(task.to_dict()))
            task_func = task_func_map.get(task.task_name, None)
            if not task_func:
                task_func = import_task_func(task.task_name)

            # Set task running
            updated_task_count = engine.update_task(
                task_name=task.task_name, task_attr=task.task_attr,
                filter_kwargs=dict(status=TaskStatus.PENDING.value),
                update_kwargs=dict(status=TaskStatus.RUNNING.value)
            )
            if not bool(updated_task_count):
                logger.warning('Task is not pending, execute task failed. task_id: {}'.format(task.pk))
                return

            # Execute task
            result = task_func.execute(*task.task_args, **task.task_kwargs)
            if result and isinstance(result, datetime.datetime):
                engine.retry_task(task_id=task.pk, next_run_at=result)
                logger.info('Retry task, task_id: {}, next_run_at: {}'.format(task.pk, result))
                return
        except Exception as _:
            task.status = TaskStatus.FAILED.value
            task.exc_info = traceback.format_exc()
            task.save()
            logger.exception('Task func execute failed. task info: {}'.format(task.to_dict()))
            return
        else:
            # NOTE: Don't save the successful task
            # task.status = TaskStatus.SUCCESS.value
            # task.save()
            logger.info(
                'Task func execute successfully. task info: {}, executed result: {}'.format(
                    task.to_dict(), result)
            )
        # Delete task
        engine.delete_task(task_name=task.task_name, task_attr=task.task_attr)

    def run(self):
        """
        Get tasks and run
        :return:
        """
        logger.info('{} start ...'.format(self.name))
        global is_running
        is_running = True
        while not stop_signal:
            waiting_tasks = engine.get_waiting_tasks()
            logger.info('Get waiting task count: {}'.format(len(waiting_tasks)))
            if not waiting_tasks:
                time.sleep(executor_idle_seconds)
                continue
            for task in waiting_tasks:
                thread_ctx.set('x_trace_id', task.trace_id)
                self.execute_task(task)

            thread_ctx.clear()
        else:
            logger.info('{} is stopped'.format(self.name))


def run(thread_count=None):
    """
    Start task executor
    """
    logger.info('Prepare task executor')
    if is_running:
        logger.info('Task executor is running, not allow start again')
        return

    if thread_count is None:
        thread_count = default_thread_count
    logger.info('Task executor thread count: {}'.format(thread_count))

    for i in range(thread_count):
        task_executor = TaskExecutor(name='Task-executor-{}'.format(i + 1))
        task_executor.start()

    logger.info('Start all task executor successfully')
