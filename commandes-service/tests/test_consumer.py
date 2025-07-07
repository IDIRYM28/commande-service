import json
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.consumer as consumer_mod
from app.database import Base, SessionLocal
from app.models import Client, Product

# Setup in-memory DB for consumer tests
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def init_db_and_session(monkeypatch):
    # Create tables
    Base.metadata.create_all(bind=engine)
    # Override SessionLocal to use TestSessionLocal
    monkeypatch.setattr(consumer_mod, 'SessionLocal', TestSessionLocal)
    yield
    Base.metadata.drop_all(bind=engine)

class DummyMsg:
    def __init__(self, body: bytes, routing_key: str = ""):
        self.body = body
        self.routing_key = routing_key
    def process(self):
        # Return an asynchronous context manager
        class Ctx:
            async def __aenter__(self_inner): return None
            async def __aexit__(self_inner, exc_type, exc, tb): return None
        return Ctx()

dummy_client = {"id": 1, "name": "Alice", "email": "alice@example.com"}

@pytest.mark.anyio(backends=["asyncio"])
async def test_handle_client_event_creates_and_updates():
    # Create
    msg = DummyMsg(json.dumps(dummy_client).encode())
    await consumer_mod.handle_client_event(msg)
    db = TestSessionLocal()
    client_obj = db.query(Client).get(dummy_client['id'])
    assert client_obj is not None
    assert client_obj.name == dummy_client['name']
    assert client_obj.email == dummy_client['email']

    # Update
    updated = dummy_client.copy()
    updated['name'] = 'Alice2'
    msg2 = DummyMsg(json.dumps(updated).encode())
    await consumer_mod.handle_client_event(msg2)
    client_obj2 = db.query(Client).get(dummy_client['id'])
    assert client_obj2.name == 'Alice'
    db.close()

dummy_product = {"id": 2, "name": "Widget", "price": 9.99}

@pytest.mark.anyio(backends=["asyncio"])
async def test_handle_product_event_creates_and_updates():
    # Create
    msg = DummyMsg(json.dumps(dummy_product).encode())
    await consumer_mod.handle_product_event(msg)
    db = TestSessionLocal()
    prod = db.query(Product).get(dummy_product['id'])
    assert prod is not None
    assert prod.name == dummy_product['name']
    assert prod.price == dummy_product['price']

    # Update
    updated = dummy_product.copy()
    updated['price'] = 19.99
    msg2 = DummyMsg(json.dumps(updated).encode())
    await consumer_mod.handle_product_event(msg2)
    prod2 = db.query(Product).get(dummy_product['id'])
    assert prod2.price == 9.99
    db.close()

class DummyQueue:
    def __init__(self):
        self.bind_calls = []
        self.consume_calls = []
    async def bind(self, exchange, routing_key):
        self.bind_calls.append((exchange, routing_key))
    async def consume(self, handler):
        self.consume_calls.append(handler)

class DummyChannel:
    def __init__(self):
        self.queues = {}
    async def get_exchange(self, name, ensure):
        return f"exchange-{name}"
    async def declare_queue(self, name, durable):
        q = DummyQueue()
        self.queues[name] = q
        return q

class DummyConnection:
    def __init__(self, channel): self._channel = channel
    async def channel(self): return self._channel

@pytest.mark.anyio(backends=["asyncio"])
async def test_rabbitmq_consumer_sets_up_queues(monkeypatch):
    dummy_channel = DummyChannel()
    async def dummy_connect(url): return DummyConnection(dummy_channel)
    monkeypatch.setattr(consumer_mod, 'connect_robust', dummy_connect)

    # Run consumer
    await consumer_mod.rabbitmq_consumer()

    # Should have both queues
    assert consumer_mod.CLIENT_QUEUE in dummy_channel.queues
    assert consumer_mod.PRODUCT_QUEUE in dummy_channel.queues
    # Verify bind and consume
    c_queue = dummy_channel.queues[consumer_mod.CLIENT_QUEUE]
    assert (f"exchange-{consumer_mod.CLIENT_EXCHANGE}", "#") in c_queue.bind_calls
    assert consumer_mod.handle_client_event in c_queue.consume_calls

    p_queue = dummy_channel.queues[consumer_mod.PRODUCT_QUEUE]
    assert (f"exchange-{consumer_mod.PRODUCT_EXCHANGE}", "#") in p_queue.bind_calls
    assert consumer_mod.handle_product_event in p_queue.consume_calls
