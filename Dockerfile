FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MOZ_HEADLESS=1 \
    FIREFOX_BINARY=/usr/bin/firefox-esr \
    POSTIDS_FILE=/data/postids.txt

ARG TARGETARCH
ARG GECKODRIVER_VERSION=0.36.0

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        firefox-esr \
        wget \
    && case "${TARGETARCH}" in \
         amd64) GECKO_ARCH=linux64 ;; \
         arm64) GECKO_ARCH=linux-aarch64 ;; \
         *) echo "Unsupported architecture: ${TARGETARCH}" && exit 1 ;; \
       esac \
    && wget -q "https://github.com/mozilla/geckodriver/releases/download/v${GECKODRIVER_VERSION}/geckodriver-v${GECKODRIVER_VERSION}-${GECKO_ARCH}.tar.gz" \
        -O /tmp/geckodriver.tar.gz \
    && tar -xzf /tmp/geckodriver.tar.gz -C /usr/local/bin \
    && chmod +x /usr/local/bin/geckodriver \
    && rm /tmp/geckodriver.tar.gz \
    && apt-get purge -y wget \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY Config.py reddit_response.py msg_monitor.py docker-entrypoint.sh ./
RUN sed -i 's/\r$//' docker-entrypoint.sh \
    && chmod +x docker-entrypoint.sh \
    && mkdir -p /data

VOLUME ["/data"]

ENTRYPOINT ["./docker-entrypoint.sh"]
