# Usa uma versão leve e oficial do Python
FROM python:3.11-slim

# Define a pasta de trabalho lá dentro do container
WORKDIR /app

# Instala algumas dependências do sistema necessárias para o banco de dados
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copia a nossa "lista de compras" primeiro (isso deixa o build mais rápido)
COPY requirements.txt .

# Instala as bibliotecas do Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o resto do nosso código (main.py, worker.py, etc) para dentro da pasta /app
COPY . .