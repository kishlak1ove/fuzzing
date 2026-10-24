FROM golang:alpine AS builder
RUN apk add --no-cache git
RUN go install github.com/ffuf/ffuf/v2@latest

FROM alpine:latest
RUN apk add --no-cache ca-certificates
COPY --from=builder /go/bin/ffuf /usr/local/bin/ffuf
ENTRYPOINT ["ffuf"]