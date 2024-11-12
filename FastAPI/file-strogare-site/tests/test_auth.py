import random
import string

from main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def random_string(length: int) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def test_register_user_with_random_data():
    i = 0
    while i < 100:
        name = random_string(10)
        email = random_string(5) + "@test.com"
        password = random_string(12)

        response = client.post("/auth/register", data={
            "name": name,
            "email": email,
            "password": password
        })

        assert response.status_code == 200
        assert response.json()["email"] == email
        assert "id" in response.json()
        i += 1
