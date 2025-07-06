import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app import crud, models, schemas

# Setup in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def setup_db():
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def db():
    db = TestingSessionLocal()
    try:
        # Pre-populate a client and product
        client = models.Client(name="TestClient", email="test@example.com")
        product = models.Product(name="TestProduct", price=10.0)
        db.add_all([client, product])
        db.commit()
        db.refresh(client)
        db.refresh(product)
        yield db
    finally:
        db.close()

class TestCRUD:
    def test_create_client(self, db):
        client_in = schemas.ClientCreate(name="Alice", email="alice@example.com")
        client = crud.create_client(db, client_in)
        assert client.id is not None
        assert client.name == "Alice"
        assert client.email == "alice@example.com"

    def test_list_clients(self, db):
        clients = crud.list_clients(db)
        assert len(clients) >= 1

    def test_get_client(self, db):
        client = crud.get_client(db, 1)
        assert client.name == "TestClient"

    def test_create_product(self, db):
        product_in = schemas.ProductCreate(name="Widget", price=5.5)
        product = crud.create_product(db, product_in)
        assert product.id is not None
        assert product.price == 5.5

    def test_list_products(self, db):
        products = crud.list_products(db)
        assert len(products) >= 1

    def test_get_product(self, db):
        product = crud.get_product(db, 1)
        assert product.name == "TestProduct"

    def test_create_order_and_lines(self, db):
        order_in = schemas.OrderCreate(
            client_id=1,
            lines=[schemas.OrderLineCreate(product_id=1, quantity=3)]
        )
        order = crud.create_order(db, order_in)
        assert order.id is not None
        assert len(order.lines) == 1
        line = order.lines[0]
        assert line.price == 10.0
        assert line.total == 30.0

    def test_get_order(self, db):
        order_in = schemas.OrderCreate(client_id=1, lines=[])
        created = crud.create_order(db, order_in)
        fetched = crud.get_order(db, created.id)
        assert fetched.id == created.id

    def test_list_orders(self, db):
        order_in = schemas.OrderCreate(client_id=1, lines=[])
        crud.create_order(db, order_in)
        orders = crud.list_orders(db)
        assert len(orders) >= 1