FROM node:22-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium ca-certificates fonts-liberation libasound2 libatk-bridge2.0-0 \
    libatk1.0-0 libcups2 libdrm2 libgbm1 libgtk-3-0 libnss3 libx11-xcb1 \
    libxcomposite1 libxdamage1 libxrandr2 xdg-utils libxss1 libxkbcommon0 \
    && rm -rf /var/lib/apt/lists/*

ENV PUPPETEER_SKIP_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

WORKDIR /app
RUN npm init -y && npm install puppeteer

COPY extract.js /app/extract.js
ENTRYPOINT ["node", "/app/extract.js"]