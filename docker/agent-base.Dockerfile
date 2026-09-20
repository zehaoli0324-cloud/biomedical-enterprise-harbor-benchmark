# Minimal base image for adapters that run inside the Docker backend.
# Build with: docker build -f docker/agent-base.Dockerfile -t research-benchmark-agent:py311 .
FROM python:3.11-slim

RUN useradd --create-home --uid 1000 --shell /bin/sh benchmark
WORKDIR /workspace
USER benchmark

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    BENCHMARK_NETWORK_POLICY=none

ENTRYPOINT ["/bin/sh"]
