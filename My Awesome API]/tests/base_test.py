from typing import Optional

from fastapi.testclient import TestClient
from requests import Session, Response
import os
import sys

# Ensure the application package ([A FastAPI project]) is importable when running tests
ROOT_APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "[A FastAPI project]"))
if ROOT_APP_DIR not in sys.path:
    sys.path.insert(0, ROOT_APP_DIR)

from app.main import app


class BaseAPITest:
    """Base API test class that starts a fastapi TestClient (https://fastapi.tiangolo.com/tutorial/testing/)."""
    client: Session

    @classmethod
    def setup_class(cls):
        with TestClient(app) as client:
            # Usage of context-manager to trigger app events when using TestClient:
            # https://fastapi.tiangolo.com/advanced/testing-events/
            cls.client = client

    def _request(self, method: str, endpoint: str, body: Optional[dict] = None, **kwargs) -> Response:
        """Perform a generic HTTP request against an endpoint of the API"""
        return self.client.request(method=method, url=endpoint, json=body, **kwargs)
