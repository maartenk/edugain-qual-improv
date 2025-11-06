ARG DEVENV_PYTHON=3.11

FROM python:${DEVENV_PYTHON}-alpine AS builder

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apk add --no-cache \
    bash \
    build-base \
    ca-certificates \
    curl \
    git \
    libffi-dev \
    openssl-dev

WORKDIR /src

# Copy project metadata first for better layer caching
COPY pyproject.toml README.md requirements.txt requirements-runtime.txt ./
COPY scripts ./scripts
COPY analyze.py ./analyze.py
COPY src ./src
COPY tests ./tests

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"
RUN pip install --upgrade pip setuptools wheel

ARG INSTALL_EXTRAS=tests
RUN pip install -e .[${INSTALL_EXTRAS}]

FROM python:${DEVENV_PYTHON}-alpine AS runtime

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:${PATH}"

RUN apk add --no-cache \
    bash \
    ca-certificates \
    curl \
    git \
    libffi \
    openssl

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /src /app

CMD ["python", "analyze.py"]
