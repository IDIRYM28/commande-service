# app/consumers.py
import asyncio
import json

from aio_pika import connect_robust, ExchangeType
from aio_pika.abc import AbstractIncomingMessage
import os
from .database import SessionLocal
from .models import Client  # ou ce que vous souhaitez mettre à jour
from dotenv import load_dotenv, find_dotenv
import pika
# Charge automatiquement le premier .env
load_dotenv(find_dotenv())

RABBIT_URL = os.getenv("RABBITMQ_URL")
params = pika.URLParameters(RABBIT_URL)
EXCHANGE_NAME = "clients"
QUEUE_NAME    = "customer"


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