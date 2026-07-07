import pytest
from django.contrib.auth.hashers import make_password
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from api.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def user(db):
    from apps.accounts.models import User

    return User.objects.create(
        email="test@example.com",
        username="tester",
        password=make_password("s3cretpass"),
        display_name="Tester",
    )


@pytest.fixture
def auth_headers(user):
    from api.security import create_token

    return {"Authorization": f"Bearer {create_token(user.id)}"}
