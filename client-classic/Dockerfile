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
    build-essential \
    git \
    wget \
    unzip \
    luajit \
    && rm -rf /var/lib/apt/lists/*

# wrk installieren
RUN git clone https://github.com/wg/wrk.git /tmp/wrk && \
    cd /tmp/wrk && make && mv wrk /usr/local/bin && rm -rf /tmp/wrk \

CMD ["sleep", "infinity"]