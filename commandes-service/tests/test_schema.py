import pytest
from app import schemas
from pydantic import ValidationError
import datetime

class TestSchemas:
    def test_order_line_create_valid(self):
        line = schemas.OrderLineCreate(product_id=1, quantity=5)
        assert line.product_id == 1
        assert line.quantity == 5

    def test_order_line_read_model(self):
        product_data = {"id": 2, "name": "P", "price": 3.5}
        data = {"id": 10, "product_id": 2, "quantity": 4, "price": 3.5, "total": 14.0, "product": product_data}
        line = schemas.OrderLineRead(**data)
        assert line.id == 10
        assert line.total == pytest.approx(14.0)
        assert line.product.id == 2

    def test_order_create_invalid(self):
        with pytest.raises(ValidationError):
            schemas.OrderCreate(client_id=None, lines=[])

    def test_order_read_model(self):
        now = datetime.datetime.utcnow()
        client_data = {"id": 1, "name": "C", "email": "c@e.com"}
        line_data = {"id":1, "product_id":1, "quantity":2, "price":2.0, "total":4.0, "product": {"id":1, "name":"X", "price":2.0}}
        data = {"id":5, "client_id":1, "created_at": now, "client": client_data, "lines": [line_data]}
        order = schemas.OrderRead(**data)
        assert order.created_at == now
        assert order.client.email == "c@e.com"
        assert order.lines[0].quantity == 2