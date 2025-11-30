###
# Multi-stage Dockerfile with two targets:
#  - `dev` : slim development image with source mounted via volume and uvicorn --reload
#  - `prod`: production image that copies only necessary files and runs uvicorn
###

########################################
########################################
# Wheelhouse stage: prebuild wheels for production deps
########################################
FROM python:3.13-alpine AS wheelhouse

WORKDIR /wheels

# Build dependencies required to compile wheels
RUN apk add --no-cache build-base gcc musl-dev python3-dev

COPY requirements-prod.txt /app/requirements-prod.txt

# Build wheels for production requirements into /wheels. These wheels are
# architecture-specific; building them here and copying them into the
# builder avoids rebuilding on the final image and allows offline install.
RUN python -m pip install --upgrade pip setuptools wheel \ 
 && python -m pip wheel --wheel-dir /wheels -r /app/requirements-prod.txt


########################################
# Builder stage: create virtualenv and install from wheelhouse
########################################
FROM python:3.13-alpine AS builder

WORKDIR /app

# Copy prebuilt wheels from the wheelhouse stage
COPY --from=wheelhouse /wheels /wheels
COPY requirements-prod.txt /app/requirements-prod.txt

# Create a virtualenv and install all production dependencies from the
# wheelhouse (no network). This keeps build-time toolchain in earlier
# stages only.
RUN python -m venv /opt/venv \
 && /opt/venv/bin/pip install --upgrade pip setuptools wheel \
 && /opt/venv/bin/pip install --no-index --find-links=/wheels -r /app/requirements-prod.txt

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app


########################################
# Dev stage: slim image with mounted source (no build tools)
########################################
FROM python:3.13-alpine AS dev

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
FROM python:3.13-alpine AS prod

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