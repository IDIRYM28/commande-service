from sqlalchemy.orm import Session
from . import models, schemas
from sqlalchemy.exc import NoResultFound

# Clients CRUD

def get_client(db: Session, client_id: int):
    return db.query(models.Client).filter(models.Client.id == client_id).first()

def list_clients(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Client).offset(skip).limit(limit).all()

def create_client(db: Session, client: schemas.ClientCreate):
    db_client = models.Client(name=client.name, email=client.email)
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

# Products CRUD

def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()

def list_products(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Product).offset(skip).limit(limit).all()

def create_product(db: Session, product: schemas.ProductCreate):
    db_product = models.Product(name=product.name, price=product.price)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

# Orders CRUD

def get_order(db: Session, order_id: int):
    return db.query(models.Order).filter(models.Order.id == order_id).first()

def list_orders(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Order).offset(skip).limit(limit).all()

def create_order(db: Session, order: schemas.OrderCreate):
    # Vérifier le client
    client = get_client(db, order.client_id)
    if not client:
        raise NoResultFound(f"Client {order.client_id} not found")
    db_order = models.Order(client_id=order.client_id)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    # Create lines avec prix et total
    for line in order.lines:
        product = get_product(db, line.product_id)
        if not product:
            raise NoResultFound(f"Product {line.product_id} not found")
        price = product.price
        total = price * line.quantity
        db_line = models.OrderLine(
            order_id=db_order.id,
            product_id=line.product_id,
            quantity=line.quantity,
            price=price,
            total=total
        )
        db.add(db_line)
    db.commit()
    db.refresh(db_order)
    return db_order
