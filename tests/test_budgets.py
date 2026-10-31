def test_create_and_get_budget(client, auth_headers):
    res = client.post("/api/budgets", headers=auth_headers, json={
        "month": "2026-10",
        "category": "Food & Dining",
        "limit_amount": 500.0,
        "notes": "Food budget"
    })
    assert res.status_code == 201
    assert res.get_json()["success"] is True

    get_res = client.get("/api/budgets?month=2026-10", headers=auth_headers)
    assert get_res.status_code == 200
    data = get_res.get_json()
    assert len(data["budgets"]) == 1
    assert data["budgets"][0]["limit_amount"] == 500.0
    assert data["budgets"][0]["remaining"] == 500.0
    assert data["budgets"][0]["spent"] == 0.0

def test_budget_alert_thresholds(client, auth_headers):
    # Set $500 budget for Food & Dining
    client.post("/api/budgets", headers=auth_headers, json={
        "month": "2026-10",
        "category": "Food & Dining",
        "limit_amount": 500.0
    })

    # 1. 50% Threshold: Add $260 expense (52% utilization)
    client.post("/api/transactions", headers=auth_headers, json={
        "title": "Groceries 1",
        "amount": 260.0,
        "type": "Expense",
        "category": "Food & Dining",
        "date": "2026-10-05"
    })
    notif_res = client.get("/api/notifications", headers=auth_headers)
    notifs = notif_res.get_json()["notifications"]
    assert any(n["level"] == "info" and n["threshold"] == 50 for n in notifs)

    # 2. 80% Threshold: Add another $150 expense ($410 spent out of $500 = 82%)
    client.post("/api/transactions", headers=auth_headers, json={
        "title": "Groceries 2",
        "amount": 150.0,
        "type": "Expense",
        "category": "Food & Dining",
        "date": "2026-10-10"
    })
    notif_res = client.get("/api/notifications", headers=auth_headers)
    notifs = notif_res.get_json()["notifications"]
    assert any(n["level"] == "warning" and n["threshold"] == 80 for n in notifs)

    # 3. 100% Threshold: Add $90 expense ($500 spent out of $500 = 100%)
    client.post("/api/transactions", headers=auth_headers, json={
        "title": "Lunch",
        "amount": 90.0,
        "type": "Expense",
        "category": "Food & Dining",
        "date": "2026-10-15"
    })
    notif_res = client.get("/api/notifications", headers=auth_headers)
    notifs = notif_res.get_json()["notifications"]
    assert any(n["threshold"] == 100 for n in notifs)

    # 4. Above 100% (Overspending): Add $50 expense ($550 spent out of $500 = 110%)
    client.post("/api/transactions", headers=auth_headers, json={
        "title": "Snack",
        "amount": 50.0,
        "type": "Expense",
        "category": "Food & Dining",
        "date": "2026-10-20"
    })
    notif_res = client.get("/api/notifications", headers=auth_headers)
    notifs = notif_res.get_json()["notifications"]
    assert any(n["threshold"] == 105 for n in notifs)

def test_delete_budget(client, auth_headers):
    create_res = client.post("/api/budgets", headers=auth_headers, json={
        "month": "2026-10",
        "category": "Entertainment",
        "limit_amount": 200.0
    })
    b_id = create_res.get_json()["budget"]["id"]

    del_res = client.delete(f"/api/budgets/{b_id}", headers=auth_headers)
    assert del_res.status_code == 200

    get_res = client.get("/api/budgets?month=2026-10", headers=auth_headers)
    assert len(get_res.get_json()["budgets"]) == 0
