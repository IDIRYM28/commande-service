import pytest
import sys, os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add project root to path to import the 'app' package
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.main import app, get_db
from app.database import Base
from app import models




client = TestClient(app)

# Tests

def test_create_order():
    response = client.post(
        "/order",
        json={"client_id": 1, "lines": [{"product_id": 1, "quantity": 3}]}
    )
    print('qs',response)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] is not None
    # client1 price=15.0 -> total 30.0
    assert data["lines"][0]["price"] == 15.0
    assert data["lines"][0]["total"] == 45.0


def test_list_orders():
    #client.post("/orders", json={"client_id": 1, "lines": []})
    response = client.get("/orders")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_order_not_found():
    response = client.get("/orders/999")
    assert response.status_code == 404
