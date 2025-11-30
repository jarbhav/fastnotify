###
# Multi-stage Dockerfile with two targets:
#  - `dev` : slim development image with source mounted via volume and uvicorn --reload
#  - `prod`: production image that copies only necessary files and runs uvicorn
###

########################################
# Builder stage: build wheels / virtualenv
########################################
FROM python:3.13-slim AS builder

WORKDIR /app

# Install system packages needed for building wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    python3-venv \
    curl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

# Create a virtualenv and install all dependencies into it. This keeps
# build-time compilation and heavy tooling out of the final runtime image.
RUN python -m venv /opt/venv \
 && /opt/venv/bin/pip install --upgrade pip setuptools wheel \
 && /opt/venv/bin/pip install --no-cache-dir -r /app/requirements.txt

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app


########################################
# Dev stage: slim image with mounted source (no build tools)
########################################
FROM python:3.13-slim AS dev

WORKDIR /app

# Copy only the runtime site-packages from the builder's virtualenv.
# No build tools (gcc, build-essential) — keeps image small.
COPY --from=builder /opt/venv/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

EXPOSE 8000

# Source code is mounted as a volume during development, so we don't COPY it.
# uvicorn --reload watches the mounted /app directory for changes.
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


########################################
# Prod stage: copy only site-packages from builder
########################################
FROM python:3.13-slim AS prod

WORKDIR /app

# Copy only the runtime site-packages from the builder's virtualenv into
# the system site-packages of the runtime image. This keeps the final image
# small and avoids compiling wheels during the final image build.
# Note: we rely on the same Python minor version in builder and prod images.
COPY --from=builder /opt/venv/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages

# Copy application source into the image (no development-only files)
COPY . /app

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Use python -m uvicorn so we don't rely on virtualenv console entrypoints
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]