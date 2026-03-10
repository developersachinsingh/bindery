import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
import processor


@pytest.fixture
def client():
    flask_app = create_app(start_threads=False)
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def clear_job_registry():
    """Ensure JOB_REGISTRY is clean before and after every test."""
    processor.JOB_REGISTRY.clear()
    yield
    processor.JOB_REGISTRY.clear()
