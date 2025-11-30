###
# Multi-stage Dockerfile with two targets:
#  - `dev` : development image with source mounted via volume and uvicorn --reload
#  - `prod`: production image that copies only necessary files and runs uvicorn
###

########################################
# Base stage: common dependencies
########################################
FROM python:3.13-slim as base

WORKDIR /app

# Install system packages needed for building some Python wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential \
	gcc \
	curl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt

# Install runtime dependencies into the base image (cached layer)
RUN pip install --no-cache-dir -r /app/requirements.txt

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app


########################################
# Dev stage: uses base image but leaves source editable (for mounts)
########################################
FROM base as dev

# In dev we keep the working dir and expect the developer to mount the project
# into the container (e.g. with docker-compose volumes). We include uvicorn
# and run it with --reload for hot-reload capabilities.

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


########################################
# Prod stage: copy only necessary files and run optimized server
########################################
FROM base as prod

# Copy application source into the image (no development-only files)
COPY . /app

EXPOSE 8000

# In production you may want to use a more robust process manager or
# multiple workers. For simplicity we start uvicorn here; in real
# deployments consider gunicorn + uvicorn workers.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
