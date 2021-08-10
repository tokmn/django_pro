import uuid

from django.db import models

from utils.serializers import JsonEncoder


# Create your models here.


class Task(models.Model):
    """
    Task model
    """
    trace_id = models.UUIDField(default=uuid.uuid4)
    task_name = models.CharField(max_length=128)
    task_attr = models.CharField(max_length=64)
    task_args = models.JSONField(default=list, encoder=JsonEncoder)
    task_kwargs = models.JSONField(default=dict, encoder=JsonEncoder)
    extra = models.JSONField(default=dict, encoder=JsonEncoder)
    run_at = models.DateTimeField()
    status = models.CharField(max_length=12)
    version = models.PositiveIntegerField(default=0)
    remark = models.CharField(max_length=128, null=True)
    exc_info = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['task_name', 'task_attr'], name='unique_task_ident')
        ]
        indexes = [
            models.Index(fields=['run_at']),
            models.Index(fields=['status']),
        ]
        db_table = 'utils_task'

    def to_dict(self):
        return dict(
            id=self.pk,
            trace_id=str(self.trace_id),
            task_name=self.task_name,
            task_attr=self.task_attr,
            task_args=self.task_args,
            task_kwargs=self.task_kwargs,
            extra=self.extra,
            run_at=str(self.run_at),
            status=self.status,
            version=self.version,
            remark=self.remark,
            exc_info=self.exc_info,
            created_at=str(self.created_at),
            updated_at=str(self.updated_at),
        )
