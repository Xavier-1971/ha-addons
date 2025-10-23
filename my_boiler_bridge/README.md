# Boiler TCP Bridge

Cet addon permet de faire le pont entre une chaudière connectée en TCP et MQTT pour Home Assistant.

## Configuration

- `tcp_host`: Adresse IP de la chaudière
- `tcp_port`: Port TCP de la chaudière (défaut: 8899)
- `mqtt_host`: Serveur MQTT (défaut: core-mosquitto)
- `mqtt_port`: Port MQTT (défaut: 1883)
- `mqtt_user`: Utilisateur MQTT (optionnel)
- `mqtt_password`: Mot de passe MQTT (optionnel)

## Installation

1. Ajoutez ce dépôt dans Home Assistant
2. Installez l'addon "Boiler TCP Bridge"
3. Configurez les paramètres
4. Démarrez l'addon