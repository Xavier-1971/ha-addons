ARG BUILD_FROM=ghcr.io/hassio-addons/base:15.0.4
FROM ${BUILD_FROM}

COPY run.sh /run.sh
RUN chmod +x /run.sh

CMD [ "/run.sh" ]
