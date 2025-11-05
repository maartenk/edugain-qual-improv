#!/usr/bin/env bash

set -euo pipefail

DOCKER_COMPOSE_BIN="${DOCKER_COMPOSE:-docker compose}"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker CLI not found in PATH. Please install Docker Desktop or the docker engine." >&2
  exit 1
fi

if ! ${DOCKER_COMPOSE_BIN} version >/dev/null 2>&1; then
  echo "Docker Compose V2 is required (expected '${DOCKER_COMPOSE_BIN}')." >&2
  exit 1
fi

if [[ $# -gt 0 ]]; then
  ${DOCKER_COMPOSE_BIN} run --rm cli "$@"
else
  ${DOCKER_COMPOSE_BIN} run --rm cli
fi
