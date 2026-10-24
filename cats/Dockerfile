FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        tar \
    && rm -rf /var/lib/apt/lists/*

ARG CATS_VERSION=14.0.0

# Определяем архитектуру и скачиваем правильный архив
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "arm64" ]; then \
        CATS_ARCH="arm64"; \
    elif [ "$ARCH" = "amd64" ]; then \
        CATS_ARCH="amd64"; \
    else \
        echo "Unsupported architecture: $ARCH" && exit 1; \
    fi && \
    curl -L "https://github.com/Endava/cats/releases/download/cats-${CATS_VERSION}/cats_linux_${CATS_ARCH}_${CATS_VERSION}.tar.gz" \
        -o /tmp/cats.tar.gz \
    && tar -xzf /tmp/cats.tar.gz -C /usr/local/bin/ \
    && chmod +x /usr/local/bin/cats \
    && rm /tmp/cats.tar.gz

RUN cats -h > /dev/null

ENTRYPOINT ["cats"]