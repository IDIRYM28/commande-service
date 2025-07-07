# app/consumers.py
import asyncio
import json

from aio_pika import connect_robust, ExchangeType
from aio_pika.abc import AbstractIncomingMessage
import os
from .database import SessionLocal
from .models import Client
from .models import Product # ou ce que vous souhaitez mettre à jour
from dotenv import load_dotenv, find_dotenv
import pika
# Charge automatiquement le premier .env
load_dotenv(find_dotenv())

RABBIT_URL = os.getenv("RABBITMQ_URL")
params = pika.URLParameters(RABBIT_URL)
CLIENT_EXCHANGE = "clients"
CLIENT_QUEUE    = "customer"
PRODUCT_EXCHANGE = "produits"
PRODUCT_QUEUE ='produits'
async def handle_client_event(message: AbstractIncomingMessage) -> None:
    async with message.process():
        payload = json.loads(message.body)
        event_type = message.routing_key        # e.g. "client.created" or "client.updated"
        data = payload.get("data", payload)     # selon votre format
        db = SessionLocal()
        try:
            client_id = data["id"]
            # Exemple de mise à jour / création d’un Client local
            client = db.query(Client).get(client_id)
            if client:
                client.name  = data.get("name", client.name)
                client.email = data.get("email", client.email)
            else:
                client = Client(
                    id    = client_id,
                    name  = data.get("name"),
                    email = data.get("email")
                )
                db.add(client)
            db.commit()
        finally:
            db.close()


async def rabbitmq_consumer() -> None:
    # 1) Connexion robuste (reconnect automatique)
    connection = await connect_robust(RABBIT_URL)
    channel    = await connection.channel()
    # 2) Déclarez l’exchange et la queue
    exchange = await channel.get_exchange(
        'clients',
        ensure=False)
    queue = await channel.declare_queue(
        QUEUE_NAME,
        durable=True
    )
    # 3) Lie tous les events client.*
    await queue.bind(exchange,routing_key="#")

    # 4) Lance la consommation
    await queue.consume(handle_client_event)


async def handle_product_event(message: AbstractIncomingMessage) -> None:
    async with message.process():
        payload = json.loads(message.body)
        event_type = message.routing_key        # e.g. "client.created" or "client.updated"
        data = payload.get("data", payload)     # selon votre format
        db = SessionLocal()
        try:
            product_id = data["id"]
            # Exemple de mise à jour / création d’un Client local
            produit = db.query(Product).get(product_id)
            if produit:
                produit.name  = data.get("name", produit.name)
                produit.price = data.get("price", produit.price)
            else:
                produit = Product(
                    id    = product_id,
                    name  = data.get("name"),
                    price = data.get("price")
                )
                db.add(produit)
            db.commit()
        finally:
            db.close()



async def rabbitmq_consumer() -> None:
        # 1) Connexion robuste (reconnaissance automatique)
        connection = await connect_robust(RABBIT_URL)
        channel = await connection.channel()

        # 2) Consumer pour les événements clients
        client_exchange = await channel.get_exchange(CLIENT_EXCHANGE, ensure=False)
        client_queue = await channel.declare_queue(CLIENT_QUEUE, durable=True)
        await client_queue.bind(client_exchange, routing_key="#")
        await client_queue.consume(handle_client_event)

        # 3) Consumer pour les événements produits
        product_exchange = await channel.get_exchange(PRODUCT_EXCHANGE, ensure=False)
        product_queue = await channel.declare_queue(PRODUCT_QUEUE, durable=True)
        await product_queue.bind(product_exchange, routing_key="#")
        await product_queue.consume(handle_product_event)