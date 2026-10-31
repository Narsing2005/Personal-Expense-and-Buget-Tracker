def test_create_income_transaction(client, auth_headers):
    res = client.post("/api/transactions", headers=auth_headers, json={
        "title": "Monthly Consulting",
        "amount": 3500.0,
        "type": "Income",
        "category": "Salary",
        "date": "2026-10-15",
        "description": "Tech consulting paycheck"
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data["success"] is True
    assert data["transaction"]["amount"] == 3500.0
    assert data["transaction"]["type"] == "Income"
    assert "id" in data["transaction"]

def test_create_expense_transaction(client, auth_headers):
    res = client.post("/api/transactions", headers=auth_headers, json={
        "title": "Grocery Shopping",
        "amount": 125.50,
        "type": "Expense",
        "category": "Food & Dining",
        "date": "2026-10-16",
        "description": "Organic supermarket"
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data["success"] is True
    assert data["transaction"]["amount"] == 125.50
    assert data["transaction"]["type"] == "Expense"

def test_get_transactions_with_filters(client, auth_headers):
    client.post("/api/transactions", headers=auth_headers, json={
        "title": "Salary", "amount": 5000, "type": "Income", "category": "Salary", "date": "2026-10-01"
    })
    client.post("/api/transactions", headers=auth_headers, json={
        "title": "Rent", "amount": 1200, "type": "Expense", "category": "Housing & Rent", "date": "2026-10-02"
    })
    client.post("/api/transactions", headers=auth_headers, json={
        "title": "Coffee", "amount": 15, "type": "Expense", "category": "Food & Dining", "date": "2026-10-05"
    })

    # Filter by type=Expense
    res = client.get("/api/transactions?type=Expense", headers=auth_headers)
    assert res.status_code == 200
    assert res.get_json()["total"] == 2

    # Filter by search=Rent
    res_search = client.get("/api/transactions?search=Rent", headers=auth_headers)
    assert res_search.status_code == 200
    assert res_search.get_json()["total"] == 1
    assert res_search.get_json()["transactions"][0]["title"] == "Rent"

def test_update_transaction(client, auth_headers):
    create_res = client.post("/api/transactions", headers=auth_headers, json={
        "title": "Electricity",
        "amount": 80.0,
        "type": "Expense",
        "category": "Utilities",
        "date": "2026-10-10"
    })
    tx_id = create_res.get_json()["transaction"]["id"]

    update_res = client.put(f"/api/transactions/{tx_id}", headers=auth_headers, json={
        "title": "Electricity & Gas",
        "amount": 110.0,
        "type": "Expense",
        "category": "Utilities",
        "date": "2026-10-10",
        "description": "Combined bill"
    })
    assert update_res.status_code == 200
    updated_data = update_res.get_json()
    assert updated_data["transaction"]["title"] == "Electricity & Gas"
    assert updated_data["transaction"]["amount"] == 110.0

def test_delete_transaction(client, auth_headers):
    create_res = client.post("/api/transactions", headers=auth_headers, json={
        "title": "To Delete",
        "amount": 50.0,
        "type": "Expense",
        "category": "Entertainment",
        "date": "2026-10-12"
    })
    tx_id = create_res.get_json()["transaction"]["id"]

    del_res = client.delete(f"/api/transactions/{tx_id}", headers=auth_headers)
    assert del_res.status_code == 200

    # Ensure transaction is gone
    get_res = client.get("/api/transactions", headers=auth_headers)
    assert get_res.get_json()["total"] == 0
