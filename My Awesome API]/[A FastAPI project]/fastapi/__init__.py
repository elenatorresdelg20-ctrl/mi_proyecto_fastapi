from typing import Any, Callable, Optional

class HTTPException(Exception):
    def __init__(self, status_code: int, detail: Any = None):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")

class Request:
    def __init__(self, headers=None, state=None, path_params=None):
        self.headers = headers or {}
        self.state = state or type("State", (), {})()
        self.path_params = path_params or {}

class Response:
    def __init__(self, content=None, status_code=200):
        self.content = content
        self.status_code = status_code

class WebSocket:
    def __init__(self):
        self.headers = {}

class Depends:
    def __init__(self, dependency=None):
        self.dependency = dependency

class Body:
    def __init__(self, default=None):
        self.default = default

class Query:
    def __init__(self, default=None):
        self.default = default

class UploadFile:
    def __init__(self, filename="", file=None):
        self.filename = filename
        self.file = file

class File:
    def __init__(self, default=None):
        self.default = default

class FastAPI:
    def __init__(self, *args, **kwargs):
        self.routes = []
        self.middlewares = []

    def add_middleware(self, middleware_class, **kwargs):
        self.middlewares.append((middleware_class, kwargs))

    def include_router(self, router, **kwargs):
        self.routes.append((router, kwargs))

    def middleware(self, name):
        def wrapper(func):
            return func
        return wrapper

class APIRouter:
    def __init__(self, *args, **kwargs):
        self.routes = []

    def add_api_route(self, path, endpoint, methods=None, dependencies=None):
        self.routes.append((path, endpoint, methods, dependencies))

    def _wrap(self, path, **kwargs):
        def decorator(func):
            self.add_api_route(path, func, methods=kwargs.get("methods"), dependencies=kwargs.get("dependencies"))
            return func
        return decorator

    def get(self, path, **kwargs):
        return self._wrap(path, methods=["GET"], **kwargs)

    def post(self, path, **kwargs):
        return self._wrap(path, methods=["POST"], **kwargs)

    def put(self, path, **kwargs):
        return self._wrap(path, methods=["PUT"], **kwargs)

    def delete(self, path, **kwargs):
        return self._wrap(path, methods=["DELETE"], **kwargs)

class Security:
    def __init__(self, dependency=None):
        self.dependency = dependency

from .security import APIKeyHeader, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from .responses import PlainTextResponse, StreamingResponse

__all__ = [
    "FastAPI",
    "APIRouter",
    "HTTPException",
    "Request",
    "Response",
    "WebSocket",
    "Depends",
    "Body",
    "Query",
    "UploadFile",
    "File",
    "Security",
    "APIKeyHeader",
    "OAuth2PasswordBearer",
    "OAuth2PasswordRequestForm",
    "PlainTextResponse",
    "StreamingResponse",
]
