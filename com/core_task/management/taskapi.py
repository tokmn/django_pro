import datetime
import logging

from lib.exceptions import DuplicateEntryForMySQL
from ..constants import TaskStatus
from .taskengines import engine

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
    logger.info(
        'Add task, task_name:{}, task_attr:{}, run_at:{}, task_args:{}, task_kwargs:{}, extra:{}, remark:{}'.format(
            task_name, task_attr, run_at, task_args, task_kwargs, extra, remark
        ))
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
        logger.info('Add task successfully. {}'.format(task.to_dict()))


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
    logger.info(
        'Update task, task_name:{}, task_attr:{}, run_at:{}, task_args:{}, task_kwargs:{}, extra:{}, remark:{}'.format(
            task_name, task_attr, run_at, task_args, task_kwargs, extra, remark
        ))
    if run_at is None:
        run_at = datetime.datetime.now()

    updated_task_count = engine.update_task(
        task_name,
        task_attr,
        filter_kwargs=dict(status=TaskStatus.WAITING.value),
        update_kwargs=dict(
            run_at=run_at,
            task_args=task_args or [],
            task_kwargs=task_kwargs or {},
            extra=extra or {},
            remark=remark,
        )
    )
    logger.info('Update task end. updated_task_count:{}'.format(updated_task_count))


def cancel_task(task_name, task_attr):
    """
    Cancel task
    :param task_name:
    :param task_attr:
    :return:
    """
    logger.info('Cancel task, task_name:{}, task_attr:{}'.format(task_name, task_attr))
    canceled, canceled_task_count = engine.delete_task(task_name=task_name, task_attr=task_attr)
    logger.info('Cancel task successfully, canceled:{}, canceled_task_count:{}'.format(
        canceled, canceled_task_count))
