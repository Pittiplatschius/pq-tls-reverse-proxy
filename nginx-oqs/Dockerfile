# nginx-oqs/Dockerfile
FROM ubuntu:22.04

ARG OPENSSL_VERSION=3.5.0
ARG OPENSSL_PREFIX=/opt/openssl-pqc
ARG OPENSSL_SRC_DIR=/usr/local/src/openssl-${OPENSSL_VERSION}
ARG NGINX_VERSION=1.28.0
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
    libpcre3-dev \
    zlib1g-dev \
    libtool \
    automake \
    autoconf \
    perl \
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

# --- Build Nginx ---
RUN cd /usr/local/src && \
    wget https://nginx.org/download/nginx-${NGINX_VERSION}.tar.gz && \
    tar -xzf nginx-${NGINX_VERSION}.tar.gz && \
    cd nginx-${NGINX_VERSION} && \
    ./configure --prefix=/opt/nginx-oqs \
                --sbin-path=/usr/sbin/nginx-oqs \
                --conf-path=/etc/nginx-oqs/nginx.conf \
                --pid-path=/var/run/nginx-oqs.pid \
                --lock-path=/var/run/nginx-oqs.lock \
                --error-log-path=/var/log/nginx-oqs/error.log \
                --http-log-path=/var/log/nginx-oqs/access.log \
                --with-http_ssl_module \
                --with-http_v2_module \
                --with-http_realip_module \
                --with-threads \
                --with-stream \
                --with-stream_ssl_module \
                --with-stream_realip_module \
                --with-pcre \
                --with-openssl=${OPENSSL_SRC_DIR} \
                --with-cc-opt="-I${OPENSSL_PREFIX}/include" \
                --with-ld-opt="-L${OPENSSL_PREFIX}/lib -L${OPENSSL_PREFIX}/lib64 -Wl,-rpath,${OPENSSL_PREFIX}/lib -Wl,-rpath,${OPENSSL_PREFIX}/lib64" && \
                # --with-ld-opt="-L${OPENSSL_PREFIX}/lib64 -Wl,-rpath,${OPENSSL_PREFIX}/lib64" && \
    make -j$(nproc) && \
    make install && \
    rm -rf /usr/local/src/*

# Create necessary directories and adjust permissions
RUN mkdir -p /var/log/nginx-oqs && \
    mkdir -p /etc/nginx-oqs/sites-enabled && \
    mkdir -p /etc/nginx-oqs/snippets && \
    chown -R www-data:www-data /var/log/nginx-oqs || true

# Expose ports
EXPOSE 80 443

# Set environment variables for Nginx runtime
ENV PATH=${OPENSSL_PREFIX}/bin:$PATH
ENV LD_LIBRARY_PATH=${OPENSSL_PREFIX}/lib:${OPENSSL_PREFIX}/lib64:$LD_LIBRARY_PATH
ENV OPENSSL_CONF=${OPENSSL_PREFIX}/ssl/openssl.cnf

# Command to run Nginx in the foreground
CMD ["/usr/sbin/nginx-oqs", "-g", "daemon off;"]