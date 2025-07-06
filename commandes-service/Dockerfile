FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    sqlite3 \
    libsqlite3-dev \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

EXPOSE 8003

# → Syntaxe ENV : pas d'espaces autour du `=`
ENV ORDER_DB_URL="postgresql://openpg:openpgpwd@db-client:5432/orders_db"
ENV RABBITMQ_URL="amqp://guest:guest@rabbitmq:5672/"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
