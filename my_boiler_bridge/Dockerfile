ARG BUILD_FROM=ghcr.io/hassio-addons/base:15.0.4
FROM ${BUILD_FROM}

# Install Python dependencies and bashio
RUN apk add --no-cache python3 py3-pip bash jq curl
RUN pip3 install --break-system-packages paho-mqtt
RUN curl -J -L -o /tmp/bashio.tar.gz "https://github.com/hassio-addons/bashio/archive/v0.16.2.tar.gz"
RUN mkdir /tmp/bashio
RUN tar zxvf /tmp/bashio.tar.gz --strip 1 -C /tmp/bashio
RUN mv /tmp/bashio/lib /usr/lib/bashio
RUN ln -s /usr/lib/bashio/bashio /usr/bin/bashio

# Copy files
COPY boiler_bridge.py /app/boiler_bridge.py
COPY run.sh /run.sh
RUN chmod +x /run.sh

CMD [ "/run.sh" ]
