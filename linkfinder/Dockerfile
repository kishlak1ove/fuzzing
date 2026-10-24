# linkfinder/Dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Клонируем LinkFinder и устанавливаем зависимости
RUN git clone https://github.com/GerbenJavado/LinkFinder.git . \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir jsbeautifier

# Создаём точку входа
ENTRYPOINT ["python", "/app/linkfinder.py"]