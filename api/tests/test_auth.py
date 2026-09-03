def test_register(client):
    response = client.post(
        "/auth/register", json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_register_duplicate_email(client):
    client.post(
        "/auth/register", json={"email": "test@example.com", "password": "password123"}
    )
    response = client.post(
        "/auth/register", json={"email": "test@example.com", "password": "password456"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_login_success(client):
    client.post(
        "/auth/register", json={"email": "test@example.com", "password": "password123"}
    )
    response = client.post(
        "/auth/login", data={"username": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_bad_credentials(client):
    client.post(
        "/auth/register", json={"email": "test@example.com", "password": "password123"}
    )
    response = client.post(
        "/auth/login",
        data={"username": "test@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
