#!/usr/bin/env sh
# Lightweight entrypoint that defaults to edugain-analyze but allows overriding.
set -e

if [ "$#" -eq 0 ]; then
  set -- edugain-analyze
fi

exec "$@"
