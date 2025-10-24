#!/bin/bash
set -e

echo "Démarrage du pont chaudière TCP..."

# Export des variables de configuration
export TCP_HOST="$(bashio::config 'tcp_host')"
export TCP_PORT="$(bashio::config 'tcp_port')"
export MQTT_HOST="$(bashio::config 'mqtt_host')"
export MQTT_PORT="$(bashio::config 'mqtt_port')"
export MQTT_USER="$(bashio::config 'mqtt_user')"
export MQTT_PASSWORD="$(bashio::config 'mqtt_password')"

echo "Configuration: TCP $TCP_HOST:$TCP_PORT, MQTT $MQTT_USER@$MQTT_HOST:$MQTT_PORT"

python3 /app/boiler_bridge.py