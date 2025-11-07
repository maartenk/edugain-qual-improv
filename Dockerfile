ARG DEVENV_PYTHON=3.11

FROM python:${DEVENV_PYTHON}-alpine AS builder

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apk add --no-cache \
    bash \
    build-base \
    ca-certificates \
    curl \
    libffi-dev \
    openssl-dev

WORKDIR /src

# Copy metadata separately to leverage Docker layer caching
COPY pyproject.toml README.md requirements.txt requirements-runtime.txt ./
COPY analyze.py ./analyze.py
COPY src ./src

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"
RUN pip install --upgrade pip setuptools wheel

ARG INSTALL_EXTRAS=tests
RUN pip install --no-cache-dir ".[${INSTALL_EXTRAS}]"

FROM python:${DEVENV_PYTHON}-alpine AS runtime

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:${PATH}"

RUN apk add --no-cache \
    bash \
    ca-certificates \
    curl \
    libffi \
    openssl

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY docker/entrypoint.sh /usr/local/bin/edugain-entrypoint.sh
RUN chmod +x /usr/local/bin/edugain-entrypoint.sh

ENTRYPOINT ["edugain-entrypoint.sh"]
CMD ["edugain-analyze"]
