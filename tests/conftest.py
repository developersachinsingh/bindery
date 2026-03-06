import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app


@pytest.fixture
def client():
    flask_app = create_app(start_threads=False)
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as c:
        yield c
