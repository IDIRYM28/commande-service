from pydantic import BaseModel
from typing import List, Optional
import datetime

class ClientBase(BaseModel):
    name: str
    email: str

class ClientCreate(ClientBase):
    pass

class ClientRead(ClientBase):
    id: int
    class Config:
        orm_mode = True

class ProductBase(BaseModel):
    name: str
    price: float

class ProductCreate(ProductBase):
    pass

class ProductRead(ProductBase):
    id: int
    class Config:
        orm_mode = True

class OrderLineBase(BaseModel):
    product_id: int
    quantity: int

class OrderLineCreate(OrderLineBase):
    pass

class OrderLineRead(OrderLineBase):
    id: int
    price: float
    total: float
    product: ProductRead
    class Config:
        orm_mode = True

class OrderBase(BaseModel):
    client_id: int

class OrderCreate(OrderBase):
    lines: List[OrderLineCreate]

class OrderRead(OrderBase):
    id: int
    created_at: datetime.datetime
    client: Optional[ClientRead]
    lines: List[OrderLineRead]
    class Config:
        orm_mode = True