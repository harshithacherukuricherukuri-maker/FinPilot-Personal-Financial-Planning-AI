import sys
from pathlib import Path
import pytest
import io

_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "FinPilot API is running"}


def test_health_endpoints():
    r1 = client.get("/health")
    assert r1.status_code == 200
    assert r1.json()["status"] == "healthy"

    r2 = client.get("/api/health")
    assert r2.status_code == 200
    assert r2.json()["status"] == "healthy"


def test_get_transactions_endpoint():
    response = client.get("/api/transactions?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "transaction_id" in data[0]
        assert "amount" in data[0]


def test_get_summary_endpoint():
    response = client.get("/api/summary?user_id=1")
    assert response.status_code == 200
    data = response.json()
    assert "total_income" in data
    assert "total_expenses" in data
    assert "net_cash_flow" in data
    assert "savings_rate" in data
    assert data["total_income"] > 0


def test_get_categories_endpoint():
    response = client.get("/api/categories?user_id=1")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert "total_expense" in data
    assert isinstance(data["categories"], list)


def test_get_behavior_endpoint():
    response = client.get("/api/behavior?user_id=1")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "indicator" in data[0]
        assert "metric" in data[0]


def test_get_budget_endpoint():
    response = client.get("/api/budget?user_id=1")
    assert response.status_code == 200
    data = response.json()
    assert "total_budget" in data
    assert "total_actual" in data
    assert "categories" in data


def test_upload_transactions_endpoint():
    csv_content = """transaction_id,user_id,date,description,amount,transaction_type,category
TXN-UP-001,1,2025-05-01,Bonus Pay,1200.0,income,Income
TXN-UP-002,1,2025-05-02,Electronics,250.0,expense,Shopping
"""
    files = {"file": ("test_upload.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    response = client.post("/api/transactions/upload", files=files)
    assert response.status_code == 201
    data = response.json()
    assert data["records_received"] == 2
    assert data["records_cleaned"] == 2
    assert "records_inserted" in data


def test_forecast_endpoint():
    response = client.get("/api/forecast?user_id=1&horizon=3")
    assert response.status_code == 200
    data = response.json()
    assert "forecast" in data
    assert len(data["forecast"]) == 3
    assert "model" in data
    assert "governance" in data
    assert data["governance"]["is_autonomous_advisor"] is False


def test_forecast_evaluation_endpoint():
    response = client.get("/api/forecast/evaluation?user_id=1&test_months=3")
    assert response.status_code == 200
    data = response.json()
    assert "mae" in data
    assert "rmse" in data
    assert "mape" in data
    assert data["mae"] >= 0


def test_recommendations_endpoint():
    response = client.get("/api/recommendations?user_id=1&risk_tolerance=moderate")
    assert response.status_code == 200
    data = response.json()
    assert "budget_recommendations" in data
    assert "investment_decision_support" in data
    assert "governance" in data


def test_wealth_optimization_endpoint():
    response = client.get("/api/wealth-optimization?user_id=1")
    assert response.status_code == 200
    data = response.json()
    assert "baseline_scenario" in data
    assert "alternative_scenarios" in data
    assert "monthly_extra_cash_flow" in data
    assert "projected_savings_difference" in data


def test_insights_endpoint():
    response = client.get("/api/insights?user_id=1")
    assert response.status_code == 200
    data = response.json()
    assert "forecast_explanation" in data
    assert "wealth_explanation" in data
    assert "recommendations_explanation" in data
    assert "governance" in data
