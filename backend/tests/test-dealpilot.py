import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app
from models import Policy, User

# Test Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_dealpilot.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def test_system_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["service"] == "DealPilot AI Engine"


def test_product_search_channel3_fallback():
    payload = {
        "product_name": "Sony WH-1000XM5",
        "budget": 250.0,
        "requirements": ["noise cancellation"],
    }
    response = client.post("/api/products/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "products" in data
    assert len(data["products"]) > 0
    assert data["products"][0]["price"] <= 350.0


def test_negotiation_workflow_and_counter():
    # 1. Start negotiation
    start_payload = {
        "product_id": "prod_test_1",
        "product_name": "Noise Cancelling Headphones",
        "merchant_name": "AudioTech Direct",
        "original_price": 200.0,
        "user_budget": 180.0,
        "target_price": 160.0,
    }
    res_start = client.post("/api/negotiations/start", json=start_payload)
    assert res_start.status_code == 200
    neg_data = res_start.json()
    neg_id = neg_data["id"]
    assert neg_data["status"] in ["IN_PROGRESS", "ACCEPTED"]
    assert len(neg_data["offers"]) >= 2

    # 2. Issue a Counteroffer
    counter_payload = {"counter_amount": 165.0, "message": "Can you meet us at $165?"}
    res_counter = client.post(f"/api/negotiations/{neg_id}/counteroffer", json=counter_payload)
    assert res_counter.status_code == 200
    updated_neg = res_counter.json()
    assert updated_neg["attempts_count"] == 2


def test_policy_enforcement_and_rejection():
    # Attempt to negotiate an item way over policy budget ($300 default)
    start_payload = {
        "product_id": "expensive_camera",
        "product_name": "Pro Camera",
        "merchant_name": "AudioTech Direct",
        "original_price": 800.0,
        "user_budget": 750.0,
    }
    res = client.post("/api/negotiations/start", json=start_payload)
    neg_id = res.json()["id"]

    # Approval should be rejected by the deterministic policy engine
    appr_res = client.post("/api/purchases/approve", json={"negotiation_id": neg_id})
    assert appr_res.status_code == 400
    assert "Policy Violation" in appr_res.json()["detail"]


def test_paypal_create_and_capture_flow():
    # 1. Start compliant negotiation
    start_payload = {
        "product_id": "p_valid",
        "product_name": "Budget Earbuds",
        "merchant_name": "AudioTech Direct",
        "original_price": 100.0,
        "user_budget": 95.0,
        "target_price": 85.0,
    }
    neg = client.post("/api/negotiations/start", json=start_payload).json()
    neg_id = neg["id"]

    # 2. Approve purchase
    client.post("/api/purchases/approve", json={"negotiation_id": neg_id})

    # 3. Create PayPal Order
    order_res = client.post("/api/payments/create-order", json={"negotiation_id": neg_id})
    assert order_res.status_code == 200
    order_id = order_res.json()["order_id"]

    # 4. Capture PayPal Order
    cap_res = client.post(
        "/api/payments/capture-order",
        json={"negotiation_id": neg_id, "paypal_order_id": order_id},
    )
    assert cap_res.status_code == 200
    assert cap_res.json()["status"] == "COMPLETED"

    # 5. Check Analytics reflects purchase
    ana_res = client.get("/api/analytics")
    assert ana_res.json()["total_purchases"] >= 1