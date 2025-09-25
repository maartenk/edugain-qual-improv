# Multi-stage Docker build for eduGAIN Quality Improvement Tools
# Optimized for security, size, and performance

# Stage 1: Build stage
FROM python:3.11-slim-bookworm AS builder

# Set build arguments
ARG BUILD_DATE
ARG VERSION
ARG VCS_REF

# Set environment variables for build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app user and directories
RUN groupadd --system --gid 1000 appuser && \
    useradd --system --uid 1000 --gid appuser --create-home --shell /bin/bash appuser

# Copy requirements first for better Docker layer caching
COPY requirements.txt /tmp/requirements.txt

# Install Python dependencies
RUN python -m pip install --upgrade pip && \
    pip install --user --no-warn-script-location -r /tmp/requirements.txt

# Stage 2: Runtime stage
FROM python:3.11-slim-bookworm AS runtime

# Set runtime labels
LABEL maintainer="eduGAIN Quality Improvement Project" \
      description="Tools for analyzing eduGAIN metadata quality" \
      version="${VERSION:-unknown}" \
      build-date="${BUILD_DATE}" \
      vcs-ref="${VCS_REF}" \
      org.opencontainers.image.title="eduGAIN Quality Improvement Tools" \
      org.opencontainers.image.description="Python tools for analyzing eduGAIN federation metadata" \
      org.opencontainers.image.version="${VERSION:-unknown}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/maartenk/edugain-qual-improv"

# Set runtime environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH=/home/appuser/.local/bin:$PATH \
    USER=appuser \
    UID=1000 \
    GID=1000

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create app user (same as build stage)
RUN groupadd --system --gid $GID $USER && \
    useradd --system --uid $UID --gid $USER --create-home --shell /bin/bash $USER

# Copy Python packages from builder stage
COPY --from=builder --chown=$USER:$USER /root/.local /home/$USER/.local

# Create app directory and set ownership
RUN mkdir -p /app && chown -R $USER:$USER /app

# Switch to app user
USER $USER
WORKDIR /app

# Copy application files
COPY --chown=$USER:$USER seccon_nosirtfi.py .
COPY --chown=$USER:$USER privacy_security_analysis.py .
COPY --chown=$USER:$USER requirements.txt .
COPY --chown=$USER:$USER CLAUDE.md README.md* ./

# Create data directory for outputs
RUN mkdir -p /app/data /app/reports

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python seccon_nosirtfi.py --help > /dev/null || exit 1

# Default command shows help
CMD ["python", "seccon_nosirtfi.py", "--help"]

# Metadata for introspection
RUN echo "Build info:" > /app/BUILD_INFO && \
    echo "Version: ${VERSION:-unknown}" >> /app/BUILD_INFO && \
    echo "Build Date: ${BUILD_DATE}" >> /app/BUILD_INFO && \
    echo "VCS Ref: ${VCS_REF}" >> /app/BUILD_INFO && \
    echo "Python: $(python --version)" >> /app/BUILD_INFO && \
    echo "Packages:" >> /app/BUILD_INFO && \
    pip list >> /app/BUILD_INFO
