FROM n8nio/n8n:latest

USER root

# Восстанавливаем apk из чистого Alpine (n8n использует Alpine 3.22)
COPY --from=alpine:3.22 /sbin/apk /sbin/apk
COPY --from=alpine:3.22 /lib/apk /lib/apk
COPY --from=alpine:3.22 /etc/apk /etc/apk
COPY --from=alpine:3.22 /usr/lib/libapk* /usr/lib/

# Устанавливаем Docker CLI
RUN apk add --no-cache docker-cli

USER node