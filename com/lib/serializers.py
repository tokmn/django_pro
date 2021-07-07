import datetime
import json
import uuid

from decimal import Decimal
from enum import Enum

from django.utils.duration import duration_string


class JsonEncoder(json.JSONEncoder):
    """
    Supports how to encode datetime, enum, decimal types, and UUIDs.
    """

    def __init__(self, **kwargs):
        kwargs.update(ensure_ascii=False)
        super().__init__(**kwargs)

    def default(self, o):
        # See "Date Time String Format" in the ECMA-262 specification.
        if isinstance(o, datetime.datetime):
            return o.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(o, datetime.date):
            return o.strftime("%Y-%m-%d")
        elif isinstance(o, datetime.time):
            return o.strftime("%H:%M:%S")
        elif isinstance(o, datetime.timedelta):
            return duration_string(o)
        elif isinstance(o, Enum):
            return str(o.value)
        elif isinstance(o, (Decimal, uuid.UUID)):
            return str(o)
        else:
            return super().default(o)
