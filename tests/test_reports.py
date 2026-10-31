def test_dashboard_summary_and_analytics(client, auth_headers):
    # Add income and expense
    client.post("/api/transactions", headers=auth_headers, json={
        "title": "Salary", "amount": 4000.0, "type": "Income", "category": "Salary", "date": "2026-10-01"
    })
    client.post("/api/transactions", headers=auth_headers, json={
        "title": "Rent", "amount": 1000.0, "type": "Expense", "category": "Housing & Rent", "date": "2026-10-02"
    })

    # Summary
    res = client.get("/api/dashboard/summary?month=2026-10", headers=auth_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["summary"]["monthly_income"] == 4000.0
    assert data["summary"]["monthly_expenses"] == 1000.0
    assert data["summary"]["monthly_savings"] == 3000.0
    assert data["summary"]["savings_rate"] == 75.0

    # Analytics
    analytics_res = client.get("/api/dashboard/analytics?month=2026-10", headers=auth_headers)
    assert analytics_res.status_code == 200
    a_data = analytics_res.get_json()
    assert "income_vs_expense" in a_data
    assert "category_breakdown" in a_data
    assert "monthly_trend" in a_data

def test_reports_endpoints(client, auth_headers):
    client.post("/api/transactions", headers=auth_headers, json={
        "title": "Salary Oct", "amount": 5000.0, "type": "Income", "category": "Salary", "date": "2026-10-01"
    })
    client.post("/api/transactions", headers=auth_headers, json={
        "title": "Groceries", "amount": 250.0, "type": "Expense", "category": "Food & Dining", "date": "2026-10-05"
    })

    # Monthly report
    m_res = client.get("/api/reports/monthly?year=2026", headers=auth_headers)
    assert m_res.status_code == 200
    assert m_res.get_json()["summary"]["total_income"] == 5000.0
    assert m_res.get_json()["summary"]["total_expense"] == 250.0

    # Category report
    c_res = client.get("/api/reports/category?month=2026-10", headers=auth_headers)
    assert c_res.status_code == 200
    assert len(c_res.get_json()["categories"]) == 1
    assert c_res.get_json()["categories"][0]["category"] == "Food & Dining"

    # Summary report
    s_res = client.get("/api/reports/summary", headers=auth_headers)
    assert s_res.status_code == 200
    assert s_res.get_json()["summary"]["net_savings"] == 4750.0
