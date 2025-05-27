# nginx-pqc/Dockerfile
FROM ubuntu:22.04

ARG OPENSSL_VERSION=3.5.0
ARG OPENSSL_SRC_DIR=/usr/local/src/openssl-${OPENSSL_VERSION}
ARG OPENSSL_PREFIX=/opt/openssl-pqc
ARG NGINX_VERSION=1.28.0

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    wget \
    perl \
    libpcre3-dev \
    zlib1g-dev \
    libtool \
    automake \
    autoconf \
    git \
    ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# --- Build OpenSSL (Stage 1) ---
RUN cd /usr/local/src && \
    wget https://www.openssl.org/source/openssl-${OPENSSL_VERSION}.tar.gz && \
    tar -xzf openssl-${OPENSSL_VERSION}.tar.gz && \
    cd openssl-${OPENSSL_VERSION} && \
    ./config --prefix=${OPENSSL_PREFIX} --openssldir=${OPENSSL_PREFIX}/ssl && \
    make -j$(nproc) && \
    make install_sw

# --- Build Nginx (Stage 2) ---
RUN cd /usr/local/src && \
    wget https://nginx.org/download/nginx-${NGINX_VERSION}.tar.gz && \
    tar -xzf nginx-${NGINX_VERSION}.tar.gz && \
    cd nginx-${NGINX_VERSION} && \
    ./configure --prefix=/opt/nginx-pq \
                --sbin-path=/usr/sbin/nginx-pq \
                --conf-path=/etc/nginx-pq/nginx.conf \
                --pid-path=/var/run/nginx-pq.pid \
                --lock-path=/var/run/nginx-pq.lock \
                --error-log-path=/var/log/nginx-pq/error.log \
                --http-log-path=/var/log/nginx-pq/access.log \
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
                --with-ld-opt="-L${OPENSSL_PREFIX}/lib64 -Wl,-rpath,${OPENSSL_PREFIX}/lib64" && \
    make -j$(nproc) && \
    make install && \
    rm -rf /usr/local/src/*

# Create necessary directories and adjust permissions
RUN mkdir -p /var/log/nginx-pq && \
    mkdir -p /etc/nginx-pq/sites-enabled && \
    mkdir -p /etc/nginx-pq/snippets && \
    chown -R www-data:www-data /var/log/nginx-pq || true # Allow failure if user doesn't exist yet

# Expose ports
EXPOSE 80 443

# Set environment variables for the custom OpenSSL (for Nginx runtime if needed, usually linked)
ENV LD_LIBRARY_PATH=${OPENSSL_PREFIX}/lib64:$LD_LIBRARY_PATH

# Command to run Nginx in the foreground
CMD ["/usr/sbin/nginx-pq", "-g", "daemon off;"]
