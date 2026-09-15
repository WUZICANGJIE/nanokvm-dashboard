FROM python:3.13-slim-bookworm AS builder
COPY --from=ghcr.io/astral-sh/uv:0.12.11 /uv /usr/local/bin/uv
WORKDIR /build
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
RUN uv export --frozen --no-dev --no-emit-project --format requirements-txt -o requirements.txt \
    && uv build --wheel \
    && uv pip install --python /usr/local/bin/python --prefix /install \
        --require-hashes -r requirements.txt \
    && uv pip install --python /usr/local/bin/python --prefix /install \
        --no-deps dist/*.whl

FROM python:3.13-slim-bookworm
LABEL org.opencontainers.image.title="NanoKVM Dashboard" \
      org.opencontainers.image.description="Local-first NanoKVM dashboard with mDNS discovery" \
      org.opencontainers.image.source="https://github.com/WUZICANGJIE/nanokvm-dashboard" \
      org.opencontainers.image.licenses="MIT"
RUN apt-get update && apt-get install -y --no-install-recommends gosu tini \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /data
COPY --from=builder /install /usr/local
COPY --chmod=755 docker/entrypoint.sh /entrypoint.sh
ENV DATA_DIR=/data PORT=8080 PUID=99 PGID=100 \
    PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
EXPOSE 8080
VOLUME ["/data"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','8080')+'/healthz', timeout=3)"
ENTRYPOINT ["/usr/bin/tini", "--", "/entrypoint.sh"]
