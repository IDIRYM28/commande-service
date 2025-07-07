from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from .database import SessionLocal, engine, Base
from . import models, schemas, crud
from . import consumer
import asyncio
# Création des tables à l'initialisation
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Order Service", version="1.0")
@app.on_event("startup")
async def startup_event():
    # Démarre le consumer en tâche de fond
    print('qsdqssqdsd')
    await asyncio.create_task(consumer.rabbitmq_consumer())
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/order", response_model=schemas.OrderRead)
def create_order_endpoint(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_order(db, order)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=str(e))
@app.post("/clients", response_model=schemas.ClientCreate)
def create_client_endpoint(client: schemas.ClientCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_client(db, client)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=str(e))
@app.post("/produits", response_model=schemas.ProductCreate)
def create_product_endpoint(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_product(db, product)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/orders", response_model=list[schemas.OrderRead])
def list_orders_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.list_orders(db, skip, limit)

@app.get("/orders/{order_id}", response_model=schemas.OrderRead)
def get_order_endpoint(order_id: int, db: Session = Depends(get_db)):
    db_order = crud.get_order(db, order_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order
