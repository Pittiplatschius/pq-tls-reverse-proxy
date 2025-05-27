# client-classic/Dockerfile
FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    openssl \
    curl \
    iputils-ping \
    dnsutils \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Kopieren Sie das Server-Zertifikat, um es für curl-Tests zu verwenden (optional, für --cacert)
COPY ./nginx-pqc/nginx_config/ssl/server.crt /etc/ssl/certs/proxy_server.crt

CMD ["sleep", "infinity"]
