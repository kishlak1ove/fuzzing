FROM n8nio/n8n:2.42.6

USER root

COPY --from=alpine:3.22 /sbin/apk /sbin/apk
COPY --from=alpine:3.22 /lib/apk /lib/apk
COPY --from=alpine:3.22 /etc/apk /etc/apk
COPY --from=alpine:3.22 /usr/lib/libapk* /usr/lib/

RUN apk add --no-cache docker-cli

USER node