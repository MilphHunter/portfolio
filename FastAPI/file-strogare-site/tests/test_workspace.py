import random
import string

from main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def random_string() -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(1, 30)))


def test_create_random_tags():
    i = 0
    while i < 100:
        title = random_string()
        response = client.post("/admin/create-tag", data={
            "title": title
        })
        assert response.status_code == 201
        assert "id" in response.json()
        i += 1
