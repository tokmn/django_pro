import json
from django.forms import Field, JSONField, ValidationError


class BoolField(Field):
    def to_python(self, value):
        if not value:
            value = None
        elif isinstance(value, str) and value.lower() in ('false', '0'):
            value = False
        else:
            value = bool(value)
        return value


class DictField(JSONField):
    def to_python(self, value):
        if not value:
            return {}
        elif isinstance(value, dict):
            return value

        converted = None
        try:
            converted = json.loads(value, cls=self.decoder)
        except json.JSONDecodeError:
            pass

        if not isinstance(converted, dict):
            raise ValidationError('输入一个有效的字典')

        return converted


class ListField(JSONField):
    def to_python(self, value):
        if not value:
            value_ = []
        elif isinstance(value, list):
            value_ = value
        else:
            value_ = None
            try:
                value_ = json.loads(value, cls=self.decoder)
            except json.JSONDecodeError:
                pass

            if not isinstance(value_, list):
                raise ValidationError('输入一个有效的列表')

        return value_

    def validate(self, value):
        if not value and self.required:
            raise ValidationError(self.error_messages['required'], code='required')
        elif self.max_length and self.max_length < len(value):
            raise ValidationError(f'列表中的元素不能超过{self.max_length}个')
        elif self.min_length and self.min_length > len(value):
            raise ValidationError(f'列表中的元素不能少于{self.min_length}个')
