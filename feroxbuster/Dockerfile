FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
        ca-certificates \
        curl \
        unzip \
    && rm -rf /var/lib/apt/lists/*

ARG FEROX_VERSION=2.13.1

# Определяем архитектуру и скачиваем правильный бинарник
RUN ARCH=$(dpkg --print-architecture) && \
    echo "Building for: $ARCH" && \
    if [ "$ARCH" = "arm64" ]; then \
        FEROX_ARCH="aarch64-linux"; \
    elif [ "$ARCH" = "amd64" ]; then \
        FEROX_ARCH="x86_64-linux"; \
    else \
        echo "Unsupported architecture: $ARCH" && exit 1; \
    fi && \
    curl -sL "https://github.com/epi052/feroxbuster/releases/download/v${FEROX_VERSION}/${FEROX_ARCH}-feroxbuster.zip" \
        -o /tmp/feroxbuster.zip \
    && unzip /tmp/feroxbuster.zip -d /tmp \
    && mv /tmp/feroxbuster /usr/local/bin/feroxbuster \
    && chmod +x /usr/local/bin/feroxbuster \
    && rm /tmp/feroxbuster.zip \
    && apt-get purge -y unzip \
    && apt-get autoremove -y

RUN feroxbuster --version

ENTRYPOINT ["feroxbuster"]