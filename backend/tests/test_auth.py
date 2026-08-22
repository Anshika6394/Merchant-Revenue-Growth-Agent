def test_registration_login_and_current_user(client):
    registration = client.post("/api/v1/auth/register", json={"email": "merchant@example.com", "password": "secure-password"})
    assert registration.status_code == 201
    login = client.post("/api/v1/auth/login", data={"username": "merchant@example.com", "password": "secure-password"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "merchant@example.com"


def test_duplicate_email_is_rejected(client):
    payload = {"email": "merchant@example.com", "password": "secure-password"}
    client.post("/api/v1/auth/register", json=payload)
    assert client.post("/api/v1/auth/register", json=payload).status_code == 409
