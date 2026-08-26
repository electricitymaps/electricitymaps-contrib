FROM mcr.microsoft.com/devcontainers/python:1-3.10-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends libgl1 \
    && rm -rf /var/lib/apt/lists/*
