"""Lightweight SQLAlchemy-compatible stubs for offline testing."""
from datetime import datetime, date
from typing import Any, Callable, Iterable, List

class ForeignKey:
    def __init__(self, target, *args, **kwargs):
        self.target = target

class _Type:
    def __call__(self, *args, **kwargs):
        return self

Integer = _Type()
String = _Type()
Float = _Type()
DateTime = _Type()
Boolean = _Type()

class _Column:
    def __init__(self, type_=None, *args, primary_key=False, index=False, unique=False, nullable=True, default=None, **kwargs):
        self.type_ = type_
        self.primary_key = primary_key
        self.index = index
        self.unique = unique
        self.nullable = nullable
        self.default = default
        self.name = None
        self.owner = None

    def __set_name__(self, owner, name):
        self.name = name
        self.owner = owner

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return instance.__dict__.get(self.name, self.default() if callable(self.default) else self.default)

    def __set__(self, instance, value):
        instance.__dict__[self.name] = value

    def __call__(self, obj):
        return getattr(obj, self.name, None)

    def _make_cmp(self, op: Callable[[Any, Any], bool]):
        def comparator(other):
            return lambda obj: op(getattr(obj, self.name, None), other)
        return comparator

    def __eq__(self, other):
        return self._make_cmp(lambda a, b: a == b)(other)

    def __ge__(self, other):
        return self._make_cmp(lambda a, b: a >= b)(other)

    def __le__(self, other):
        return self._make_cmp(lambda a, b: a <= b)(other)

    def __gt__(self, other):
        return self._make_cmp(lambda a, b: a > b)(other)

    def __lt__(self, other):
        return self._make_cmp(lambda a, b: a < b)(other)

    def label(self, name):
        self.label_name = name
        return self

Column = _Column

class _Index:
    def __init__(self, name, *cols):
        self.name = name
        self.cols = cols

class _UniqueConstraint:
    def __init__(self, *cols, name=None):
        self.cols = cols
        self.name = name

Index = _Index
UniqueConstraint = _UniqueConstraint

class _FuncCall:
    def __init__(self, func_name: str, arg=None, default=None):
        self.func_name = func_name
        self.arg = arg
        self.default = default
        self.label_name = None
        self.owner = getattr(arg, "owner", None)

    def label(self, name: str):
        self.label_name = name
        return self

    def __call__(self, obj):
        if isinstance(self.arg, _FuncCall):
            return self.arg(obj)
        if callable(self.arg):
            return self.arg(obj)
        return getattr(obj, getattr(self.arg, "name", None), None)

    def compute(self, objs: List[Any]):
        values = []
        if self.func_name == "coalesce":
            base = self.arg.compute(objs) if isinstance(self.arg, _FuncCall) else self.arg
            return base if base is not None else self.default

        for obj in objs:
            if isinstance(self.arg, _FuncCall):
                values.append(self.arg.compute([obj]))
            elif callable(self.arg):
                values.append(self.arg(obj))
            else:
                values.append(getattr(obj, getattr(self.arg, "name", None), None))

        if self.func_name == "sum":
            return sum(values)
        if self.func_name == "count":
            return len(values)
        if self.func_name == "avg":
            return sum(values) / len(values) if values else 0
        if self.func_name == "date":
            if not values:
                return None
            first = values[0]
            if isinstance(first, (datetime, date)):
                return first.date() if isinstance(first, datetime) else first
            return first
        return None

class _Func:
    def sum(self, arg):
        return _FuncCall("sum", arg)

    def count(self, arg):
        return _FuncCall("count", arg)

    def avg(self, arg):
        return _FuncCall("avg", arg)

    def coalesce(self, arg, default):
        return _FuncCall("coalesce", arg, default=default)

    def date(self, arg):
        def extractor(obj):
            value = getattr(obj, getattr(arg, "name", None), None)
            return value.date() if hasattr(value, "date") else value
        fc = _FuncCall("date", extractor)
        fc.owner = getattr(arg, "owner", None)
        return fc

func = _Func()

class _MetaData:
    def __init__(self):
        self.tables = []

    def create_all(self, bind=None):
        return True

class _DeclarativeMeta(type):
    def __new__(mcls, name, bases, attrs):
        cls = super().__new__(mcls, name, bases, attrs)
        if name != "BaseModel" and hasattr(cls, "__tablename__"):
            Base.metadata.tables.append(cls)
        return cls

class BaseModel(metaclass=_DeclarativeMeta):
    metadata = _MetaData()

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

Base = BaseModel

class _Engine:
    def __init__(self, url, connect_args=None, pool_pre_ping=False):
        self.url = url

class _Session:
    def __init__(self, storage):
        self.storage = storage

    def add(self, obj):
        self.storage.setdefault(type(obj), []).append(obj)
        if getattr(obj, "id", None) is None:
            obj.id = len(self.storage[type(obj)])

    def add_all(self, objs: Iterable[Any]):
        for obj in objs:
            self.add(obj)

    def commit(self):
        return True

    def refresh(self, obj):
        return obj

    def close(self):
        return True

    def query(self, *entities):
        return _Query(self, list(entities))

class _Query:
    def __init__(self, session: _Session, entities: List[Any]):
        self.session = session
        self.entities = entities or []
        self.model = None
        if self.entities:
            first = self.entities[0]
            if isinstance(first, type):
                self.model = first
            else:
                owner = next((getattr(ent, "owner", None) for ent in self.entities if hasattr(ent, "owner")), None)
                if owner is None and hasattr(first, "arg"):
                    owner = getattr(first.arg, "owner", None)
                self.model = owner
        self._filters: List[Callable[[Any], bool]] = []
        self._groupers: List[Callable[[Any], Any]] = []

    def filter(self, *conds):
        self._filters.extend([c for c in conds if c is not None])
        return self

    def group_by(self, *funcs):
        self._groupers.extend(funcs)
        return self

    def _apply_filters(self, data: List[Any]):
        result = []
        for obj in data:
            if all(cond(obj) for cond in self._filters):
                result.append(obj)
        return result

    def _get_data(self):
        return list(self.session.storage.get(self.model, [])) if self.model else []

    def all(self):
        data = self._apply_filters(self._get_data())
        if self.entities and all(ent == self.model for ent in self.entities):
            return data
        if self._groupers:
            grouped = {}
            for obj in data:
                key = tuple(g(obj) for g in self._groupers)
                grouped.setdefault(key, []).append(obj)
            rows = []
            for key, objs in grouped.items():
                row_values = []
                for ent in self.entities:
                    if isinstance(ent, _FuncCall):
                        row_values.append(ent.compute(objs))
                    elif callable(ent):
                        row_values.append(ent(objs[0]))
                    elif hasattr(ent, "name"):
                        attr_name = ent.name if isinstance(ent.name, str) else getattr(ent.name, "name", None)
                        row_values.append(getattr(objs[0], attr_name, None))
                    else:
                        row_values.append(ent)
                rows.append(tuple(row_values))
            return rows
        if self.entities:
            if all(isinstance(ent, _FuncCall) for ent in self.entities):
                return [tuple(ent.compute(data) for ent in self.entities)]
            rows = []
            for obj in data:
                values = []
                for ent in self.entities:
                    if isinstance(ent, _FuncCall):
                        values.append(ent.compute([obj]))
                    elif hasattr(ent, "name"):
                        attr_name = ent.name if isinstance(ent.name, str) else getattr(ent.name, "name", None)
                        values.append(getattr(obj, attr_name, None))
                    else:
                        values.append(ent)
                rows.append(tuple(values))
            return rows
        return data

    def first(self):
        results = self.all()
        return results[0] if results else None

    def one(self):
        results = self.all()
        if len(results) != 1:
            raise ValueError("Expected exactly one result")
        return results[0]


def create_engine(url, connect_args=None, pool_pre_ping=False):
    return _Engine(url, connect_args=connect_args, pool_pre_ping=pool_pre_ping)


def sessionmaker(autocommit=False, autoflush=False, bind=None):
    storage = {}

    class _SessionFactory:
        def __call__(self):
            return _Session(storage)

    return _SessionFactory()

__all__ = [
    "create_engine",
    "sessionmaker",
    "declarative_base",
    "Column",
    "Integer",
    "String",
    "Float",
    "DateTime",
    "Boolean",
    "ForeignKey",
    "Index",
    "UniqueConstraint",
    "func",
    "Base",
]


def declarative_base():
    return Base
