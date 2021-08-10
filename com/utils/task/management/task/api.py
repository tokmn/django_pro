import datetime
import logging

from utils.exceptions import DuplicateEntryForMySQL
from ...constants import TaskStatus
from .engines import engine

#
logger = logging.getLogger(__name__)


def add_task(task_name, task_attr, run_at, task_args=None, task_kwargs=None, extra=None, remark=None):
    """
    Add new task
    :param task_name:
    :param task_attr:
    :param run_at:
    :param task_args:
    :param task_kwargs:
    :param extra:
    :param remark:
    :return:
    """
    logger.info(f'Add task, task_name:{task_name}, task_attr:{task_attr}, run_at:{run_at}, '
                f'task_args:{task_args}, task_kwargs:{task_kwargs}, extra:{extra}, remark:{remark}')
    status = TaskStatus.WAITING.value
    # If not set run_at, task will run immediately
    if not run_at:
        run_at = datetime.datetime.now()
    try:
        task = engine.create_task(
            task_name,
            task_attr,
            run_at=run_at,
            status=status,
            task_args=task_args or [],
            task_kwargs=task_kwargs or {},
            extra=extra or {},
            remark=remark
        )
    except Exception as e:
        if e.args and isinstance(e.args, tuple) and e.args[0] == DuplicateEntryForMySQL.code:
            logger.warning('Add task failed, task already exists')
        else:
            logger.exception('Add task error')
    else:
        logger.info(f'Add task successfully. {task.to_dict()}')


def update_task(task_name, task_attr, run_at, task_args=None, task_kwargs=None, extra=None, remark=None):
    """
    Update an eixsting task

    Task's status must be `waiting`

    :param task_name:
    :param task_attr:
    :param run_at:
    :param task_args:
    :param task_kwargs:
    :param extra:
    :param remark:
    :return:
    """
    logger.info(f'Add task, task_name:{task_name}, task_attr:{task_attr}, run_at:{run_at}, '
                f'task_args:{task_args}, task_kwargs:{task_kwargs}, extra:{extra}, remark:{remark}')

    filter_kwargs = dict(status=TaskStatus.WAITING.value)

    update_kwargs = {}
    for key, value in dict(run_at=run_at, extra=extra, remark=remark,
                           task_args=task_args, task_kwargs=task_kwargs).items():
        if value is not None:
            update_kwargs[key] = value
    if not update_kwargs:
        logger.info('Update task end. nothing to updated')
        return

    updated_task_count = engine.update_task(
        task_name, task_attr,
        filter_kwargs=filter_kwargs,
        update_kwargs=update_kwargs
    )
    logger.info(f'Update task end. updated_task_count:{updated_task_count}')


def cancel_task(task_name, task_attr):
    """
    Cancel task
    :param task_name:
    :param task_attr:
    :return:
    """
    logger.info(f'Cancel task, task_name:{task_name}, task_attr:{task_attr}')
    canceled, canceled_task_count = engine.delete_task(task_name=task_name, task_attr=task_attr)
    logger.info(f'Cancel task successfully, canceled:{canceled}, canceled_task_count:{canceled_task_count}')
