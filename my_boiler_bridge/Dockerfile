ARG BUILD_FROM=ghcr.io/hassio-addons/base:15.0.4
FROM ${BUILD_FROM}

# Install Python dependencies
RUN apk add --no-cache python3 py3-pip
RUN pip3 install paho-mqtt

# Copy files
COPY boiler_bridge.py /app/boiler_bridge.py
COPY run.sh /run.sh
RUN chmod +x /run.sh

CMD [ "/run.sh" ]
