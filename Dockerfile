FROM python:3.11-slim

# Install system dependencies for libpostal
RUN apt-get update && apt-get install -y \
    build-essential curl automake autoconf libtool pkg-config git \
    && rm -rf /var/lib/apt/lists/*

# Build and install libpostal from source
RUN git clone https://github.com/openvenues/libpostal.git /tmp/libpostal \
    && cd /tmp/libpostal \
    && ./bootstrap.sh \
    && ./configure --datadir=/usr/local/share/libpostal \
    && make \
    && make install \
    && ldconfig \
    && rm -rf /tmp/libpostal

WORKDIR /app

# Allow overriding install ref (defaults to main)
ARG RYANDATA_ADDR_UTILS_REF=main

# Install the package from git ref plus API deps
RUN pip install --no-cache-dir \
    "git+https://github.com/Abstract-Data/RyanData-Address-Utils.git@${RYANDATA_ADDR_UTILS_REF}" \
    fastapi \
    "uvicorn[standard]" \
    postal

# Optional: copy source for local development/mounting (no-op unless mounted)
COPY . /app

# Default to Python shell; can override with CMD for API (see Make targets)
CMD ["python"]

