# Agent-managed runtime. One operator per isolated deployment and data volume.
# Browser stays sandboxed by default; no Google/CAPTCHA bypass flags are added.
FROM node:22-bookworm-slim AS node
FROM python:3.12-slim-bookworm
COPY --from=node /usr/local/bin/node /usr/local/bin/node
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium chromium-sandbox xvfb x11vnc novnc websockify ffmpeg fonts-liberation ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir -r /app/requirements.txt \
    && useradd --create-home --uid 1000 vso && mkdir -p /data && chown vso:vso /data
COPY . /app
USER vso
ENV VSO_DATA_DIR=/data VSO_REMOTE_BROWSER=1 VSO_CHROME=/usr/bin/chromium \
    VSO_PYTHON=/usr/local/bin/python VSO_NOVNC_ROOT=/usr/share/novnc VSO_STATE_BACKEND=sqlite
EXPOSE 8787
CMD ["python", "-m", "vso", "serve", "--host", "0.0.0.0"]
