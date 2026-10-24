# graphql-tools/Dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 1. Устанавливаем Clairvoyance (восстановление схемы)
RUN pip install --no-cache-dir clairvoyance

# 2. Устанавливаем graphql-cop (аудит безопасности)
RUN curl -sL https://raw.githubusercontent.com/dolevf/graphql-cop/master/graphql-cop.py -o /usr/local/bin/graphql-cop \
    && chmod +x /usr/local/bin/graphql-cop \
    && pip install --no-cache-dir requests colorama

# Контейнер должен просто висеть в фоне, чтобы n8n мог в него заходить
ENTRYPOINT ["tail", "-f", "/dev/null"]