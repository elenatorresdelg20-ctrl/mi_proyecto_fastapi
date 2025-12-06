from datetime import datetime
a = datetime
class BaseModel:
    def __init__(self, **data):
        for k, v in data.items():
            setattr(self, k, v)

    def model_dump(self, **kwargs):
        return self.__dict__

    @classmethod
    def model_validate(cls, obj):
        if isinstance(obj, cls):
            return obj
        return cls(**obj)

class Field:
    def __init__(self, default=None, alias=None, description=None):
        self.default = default
        self.alias = alias
        self.description = description

def field_validator(*args, **kwargs):
    def decorator(fn):
        return fn
    return decorator

__all__ = ["BaseModel", "Field", "field_validator"]
