FROM python:3.13-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set apt variables to avoid interactive mode
ENV  DEBIAN_FRONTEND=noninteractive
# DL4006 info: Set the SHELL option -o pipefail before RUN with a pipe in it.
SHELL  ["/bin/bash", "-o", "pipefail", "-c"]

# Update the list of packages, install minimal packages
RUN  apt-get update \
    && apt-get install --no-install-recommends -y \
    apt-utils \
    curl \
    ca-certificates \
    libssl-dev \
    build-essential \
    libjpeg62-turbo-dev \
    zlib1g-dev
# Clean apt to minimize size of image
RUN  apt-get clean
RUN  rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable

COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable

FROM python:3.13-slim
COPY --from=builder /app/.venv /app/.venv

WORKDIR /app
COPY asgi.py /app
COPY accueil /app/accueil
ENTRYPOINT [".venv/bin/sanic", "asgi:app", "--host=0.0.0.0", "--port=8000", "--single-process", "--no-motd"]
