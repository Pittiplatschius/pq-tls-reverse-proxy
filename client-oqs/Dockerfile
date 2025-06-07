# client-oqs/Dockerfile
FROM ubuntu:22.04

ARG OPENSSL_VERSION=3.5.0
ARG OPENSSL_PREFIX=/opt/openssl-pqc
ARG LIBOQS_BRANCH=main
ARG OQSPROVIDER_BRANCH=main

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    wget \
    curl \
    git \
    cmake \
    ninja-build \
    libtool \
    automake \
    autoconf \
    perl \
    zlib1g-dev \
    iputils-ping \
    dnsutils \
    net-tools \
    ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# --- Build liboqs ---
RUN cd /usr/local/src && \
    git clone --depth 1 --branch ${LIBOQS_BRANCH} https://github.com/open-quantum-safe/liboqs.git && \
    cd liboqs && \
    mkdir build && cd build && \
    cmake -GNinja -DCMAKE_INSTALL_PREFIX=${OPENSSL_PREFIX} -DOQS_USE_OPENSSL=OFF .. && \
    ninja && \
    ninja install && \
    cd /usr/local/src

# --- Build OpenSSL 3.5.0 ---
RUN cd /usr/local/src && \
    wget https://www.openssl.org/source/openssl-${OPENSSL_VERSION}.tar.gz && \
    tar -xzf openssl-${OPENSSL_VERSION}.tar.gz && \
    cd openssl-${OPENSSL_VERSION} && \
    ./config --prefix=${OPENSSL_PREFIX} --openssldir=${OPENSSL_PREFIX}/ssl shared && \
    make -j$(nproc) && \
    make install_sw && \
    cd /usr/local/src

# --- Build OQS Provider ---
ENV OPENSSL_ROOT_DIR=${OPENSSL_PREFIX}
ENV LIBOQS_ROOT_DIR=${OPENSSL_PREFIX}

RUN cd /usr/local/src && \
    git clone --depth 1 --branch ${OQSPROVIDER_BRANCH} https://github.com/open-quantum-safe/oqs-provider.git && \
    cd oqs-provider && \
    mkdir build && cd build && \
    cmake -GNinja -DOPENSSL_ROOT_DIR=${OPENSSL_ROOT_DIR} -DCMAKE_INSTALL_PREFIX=${OPENSSL_ROOT_DIR} .. && \
    ninja && \
    ninja install && \
    cd /usr/local/src

# Copy custom openssl.cnf to activate OQS provider
COPY ./openssl.cnf ${OPENSSL_PREFIX}/ssl/openssl.cnf

# Set environment variables for the custom OpenSSL with OQS
ENV PATH=${OPENSSL_PREFIX}/bin:$PATH
ENV LD_LIBRARY_PATH=${OPENSSL_PREFIX}/lib:${OPENSSL_PREFIX}/lib64:$LD_LIBRARY_PATH

# Verify installation
RUN openssl version
RUN openssl list -providers

CMD ["sleep", "infinity"]