# Debian Bookworm ≈ Raspberry Pi OS userland. Desk image, not the animal.
FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-venv python3-pip ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/lucy/src
COPY . .
RUN python3 -m venv /opt/lucy/.venv \
    && /opt/lucy/.venv/bin/pip install --no-cache-dir -e ".[dev]"

ENV PATH="/opt/lucy/.venv/bin:$PATH"
CMD ["bash", "scripts/verify.sh"]
