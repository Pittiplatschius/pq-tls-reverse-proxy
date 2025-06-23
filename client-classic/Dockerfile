# client-classic/Dockerfile
FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    openssl \
    curl \
    iputils-ping \
    dnsutils \
    net-tools \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

CMD ["sleep", "infinity"]