# client-pqc/Dockerfile
FROM ubuntu:22.04

ARG OPENSSL_VERSION=3.5.0
ARG OPENSSL_PREFIX=/opt/openssl-pqc

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    wget \
    perl \
    libtool \
    automake \
    autoconf \
    git \
    zlib1g-dev \
    curl \
    iputils-ping \
    dnsutils \
    net-tools \
    ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Download and compile OpenSSL
RUN cd /usr/local/src && \
    wget https://www.openssl.org/source/openssl-${OPENSSL_VERSION}.tar.gz && \
    tar -xzf openssl-${OPENSSL_VERSION}.tar.gz && \
    cd openssl-${OPENSSL_VERSION} && \
    ./config --prefix=${OPENSSL_PREFIX} --openssldir=${OPENSSL_PREFIX}/ssl && \
    make -j$(nproc) && \
    make install_sw && \
    rm -rf /usr/local/src/*

# Set environment variables for the custom OpenSSL
ENV PATH=${OPENSSL_PREFIX}/bin:$PATH
# ENV LD_LIBRARY_PATH=${OPENSSL_PREFIX}/lib64:$LD_LIBRARY_PATH
# dynamic lib env for windows,unix and mac
ENV LD_LIBRARY_PATH=${OPENSSL_PREFIX}/lib:${OPENSSL_PREFIX}/lib64:$LD_LIBRARY_PATH

# Verify installation
RUN openssl version

# Kopieren Sie das Server-Zertifikat, um es für curl-Tests zu verwenden (optional, für --cacert)
# COPY ./nginx-pqc/nginx_config/ssl/server.crt /etc/ssl/certs/proxy_server.crt

CMD ["sleep", "infinity"]
