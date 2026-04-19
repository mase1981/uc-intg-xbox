FROM python:3.11-slim-bullseye
WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir --upgrade -r requirements.txt
RUN mkdir -p /config
COPY . .
ENV UC_DISABLE_MDNS_PUBLISH="false"
ENV UC_MDNS_LOCAL_HOSTNAME=""
ENV UC_INTEGRATION_INTERFACE="0.0.0.0"
ENV UC_INTEGRATION_HTTP_PORT="9090"
ENV UC_CONFIG_HOME="/config"
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
LABEL org.opencontainers.image.source=https://github.com/mase1981/uc-intg-xbox
LABEL org.opencontainers.image.description="Xbox Integration for Unfolded Circle Remote"
LABEL org.opencontainers.image.licenses=MPL-2.0
CMD ["python3", "-u", "-m", "uc_intg_xbox"]
