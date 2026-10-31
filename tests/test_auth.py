def test_register_success(client):
    res = client.post("/api/auth/register", json={
        "name": "Sarah Connor",
        "email": "sarah@cyberdyne.com",
        "password": "SecurePassword99"
    })
    data = res.get_json()
    assert res.status_code == 201
    assert data["success"] is True
    assert "token" in data
    assert data["user"]["email"] == "sarah@cyberdyne.com"

def test_register_duplicate_email(client):
    client.post("/api/auth/register", json={
        "name": "Sarah Connor",
        "email": "sarah@cyberdyne.com",
        "password": "SecurePassword99"
    })
    res = client.post("/api/auth/register", json={
        "name": "Sarah Another",
        "email": "sarah@cyberdyne.com",
        "password": "AnotherPassword123"
    })
    assert res.status_code == 409
    assert res.get_json()["success"] is False

def test_register_invalid_inputs(client):
    res = client.post("/api/auth/register", json={
        "name": "S",
        "email": "not-an-email",
        "password": "123"
    })
    assert res.status_code == 400
    assert len(res.get_json()["errors"]) >= 3

def test_login_success(client):
    client.post("/api/auth/register", json={
        "name": "Bruce Wayne",
        "email": "bruce@waynecorp.com",
        "password": "BatPassword2026"
    })
    res = client.post("/api/auth/login", json={
        "email": "bruce@waynecorp.com",
        "password": "BatPassword2026"
    })
    assert res.status_code == 200
    assert res.get_json()["success"] is True
    assert "token" in res.get_json()

def test_login_wrong_password(client):
    client.post("/api/auth/register", json={
        "name": "Bruce Wayne",
        "email": "bruce@waynecorp.com",
        "password": "BatPassword2026"
    })
    res = client.post("/api/auth/login", json={
        "email": "bruce@waynecorp.com",
        "password": "WrongPassword"
    })
    assert res.status_code == 401
    assert res.get_json()["success"] is False

def test_get_current_user_profile(client, auth_headers):
    res = client.get("/api/auth/me", headers=auth_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["user"]["email"] == "jordan@example.com"
