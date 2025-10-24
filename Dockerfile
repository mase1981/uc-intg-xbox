FROM python:3.11-slim-bullseye

WORKDIR /app

RUN apt-get update && apt-get install -y git build-essential

COPY driver.json driver.json
COPY requirements.txt requirements.txt
COPY ./uc_intg_xbox ./uc_intg_xbox

RUN pip3 install --no-cache-dir --upgrade -r requirements.txt

ADD . .

ENV UC_DISABLE_MDNS_PUBLISH="false"
ENV UC_MDNS_LOCAL_HOSTNAME=""
ENV UC_INTEGRATION_INTERFACE="0.0.0.0"
ENV UC_INTEGRATION_HTTP_PORT="9094"
ENV UC_CONFIG_HOME="/config"
LABEL org.opencontainers.image.source=https://github.com/mase1981/uc-intg-xbox

CMD ["python3", "-u", "-m", "uc_intg_xbox.driver"]