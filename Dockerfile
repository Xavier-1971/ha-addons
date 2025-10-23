ARG BUILD_FROM=ghcr.io/hassio-addons/base-python:latest
FROM ${BUILD_FROM}

# Copie des fichiers du module
COPY run.sh /app/run.sh
COPY chaudiere.py /app/chaudiere.py

# Définir le répertoire de travail
WORKDIR /app

# Rendre le script exécutable
RUN chmod a+x /app/run.sh

# Commande de démarrage
CMD ["/app/run.sh"]
