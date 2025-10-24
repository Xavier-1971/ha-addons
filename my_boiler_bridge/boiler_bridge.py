import socket
import time
import json
import os
import sys
from datetime import datetime
import paho.mqtt.client as mqtt

print("Boiler TCP Bridge démarré")

def envoyer_trame_tcp(adresse, port, trame, mqtt_client):
    try:
        with socket.create_connection((adresse, port), timeout=5) as client_socket:
            trame_complete = "08" + ''.join(f"{ord(c):02x}" for c in trame) + "0d"
            client_socket.sendall(bytes.fromhex(trame_complete))
            print(f"[{datetime.now()}] Trame envoyée : {trame}")
            reponse = client_socket.recv(1024)
            if reponse:
                reponse_str = reponse.decode(errors='ignore')
                print(f"[{datetime.now()}] Réponse : {reponse_str}")
                
                # Publier sur MQTT pour Home Assistant
                mqtt_client.publish("homeassistant/sensor/boiler/state", json.dumps({
                    "timestamp": datetime.now().isoformat(),
                    "trame": trame,
                    "response": reponse_str,
                    "raw_hex": reponse.hex()
                }))
                return reponse_str
    except Exception as e:
        print(f"Erreur de connexion : {e}")
        return None

def on_message(client, userdata, msg):
    tcp_host, tcp_port = userdata
    topic = msg.topic
    payload = msg.payload.decode()
    
    if topic == "boiler/switch/set":
        print(f"Commande switch reçue: {payload}")
        if payload == "ON":
            print("Démarrage chaudière...")
            envoyer_trame_tcp(tcp_host, tcp_port, "J30253000000000001", client)
            client.publish("boiler/switch/state", "ON", retain=True)
        else:
            print("Arrêt chaudière...")
            envoyer_trame_tcp(tcp_host, tcp_port, "J30254000000000001", client)
            client.publish("boiler/switch/state", "OFF", retain=True)
    
    elif topic == "homeassistant/number/boiler_temp/set":
        temp = int(float(payload))
        trame = f"B20180000000000{temp:03d}"
        envoyer_trame_tcp(tcp_host, tcp_port, trame, client)  # envoi consigne
        client.publish("homeassistant/number/boiler_temp/state", str(temp), retain=True)

def main():
    options = json.loads(os.environ.get('OPTIONS', '{}'))
    print(f"Configuration chargée: {len(options)} paramètres")
    
    # Lecture depuis les variables d'environnement (exportées par run.sh)
    tcp_host = os.environ.get('TCP_HOST', '192.168.1.16')
    tcp_port = int(os.environ.get('TCP_PORT') or '8899')
    mqtt_host = os.environ.get('MQTT_HOST') or 'core-mosquitto'
    mqtt_port = int(os.environ.get('MQTT_PORT') or '1883')
    mqtt_user = os.environ.get('MQTT_USER', '')
    mqtt_password = os.environ.get('MQTT_PASSWORD', '')
    
    print(f"Variables d'environnement MQTT: {[k for k in os.environ.keys() if 'MQTT' in k]}")
    
    print(f"Configuration: TCP {tcp_host}:{tcp_port}, MQTT {mqtt_host}:{mqtt_port}, User: {mqtt_user}")
    sys.stdout.flush()
    
    print("Création client MQTT...")
    sys.stdout.flush()
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    client = mqtt.Client()
    print("Client MQTT créé")
    sys.stdout.flush()
    
    def on_connect(client, userdata, flags, rc):
        print(f"Connexion MQTT: code {rc}")
        sys.stdout.flush()
    
    client.user_data_set((tcp_host, tcp_port))
    client.on_message = on_message
    client.on_connect = on_connect
    
    # Configuration authentification MQTT
    if mqtt_user and mqtt_password:
        client.username_pw_set(mqtt_user, mqtt_password)
        print(f"Authentification MQTT configurée pour: {mqtt_user}")
    else:
        print(f"Pas d'authentification MQTT (user: '{mqtt_user}', pwd: {'***' if mqtt_password else 'vide'})")
        # Essai sans authentification
        print("Tentative de connexion sans authentification...")
    sys.stdout.flush()
    
    print("Callbacks configurés")
    sys.stdout.flush()
    
    print("Connexion à MQTT...")
    sys.stdout.flush()
    try:
        client.connect(mqtt_host, mqtt_port, 60)
        client.loop_start()
        print("Connecté à MQTT")
        sys.stdout.flush()
    except Exception as e:
        print(f"Erreur connexion MQTT: {e}")
        print("Tentative avec 'localhost'...")
        sys.stdout.flush()
        try:
            client.connect('localhost', mqtt_port, 60)
            client.loop_start()
            print("Connecté à MQTT via localhost")
            sys.stdout.flush()
        except Exception as e2:
            print(f"Erreur connexion localhost: {e2}")
            sys.stdout.flush()
            return
    
    # Attendre que la connexion soit stable
    time.sleep(2)
    print("Connexion MQTT stabilisée")
    sys.stdout.flush()
    
    # Switch ON/OFF
    switch_config = {
        "name": "Boiler Power",
        "command_topic": "boiler/switch/set",
        "state_topic": "boiler/switch/state",
        "unique_id": "boiler_power_switch",
        "device": {
            "identifiers": ["boiler_device"],
            "name": "Boiler",
            "manufacturer": "Custom",
            "model": "TCP Bridge"
        }
    }
    print("Publication configuration switch...")
    sys.stdout.flush()
    result1 = client.publish("homeassistant/switch/boiler_power_switch/config", json.dumps(switch_config), retain=True)
    result2 = client.publish("boiler/switch/state", "OFF", retain=True)
    print(f"Switch configuré - Résultats: {result1.rc}, {result2.rc}")
    sys.stdout.flush()
    
    # Number pour consigne température (plus simple que climate)
    temp_config = {
        "name": "Boiler Temperature",
        "command_topic": "homeassistant/number/boiler_temp/set",
        "state_topic": "homeassistant/number/boiler_temp/state",
        "min": 40,
        "max": 80,
        "step": 1,
        "unit_of_measurement": "°C",
        "unique_id": "boiler_temp",
        "device": {"identifiers": ["boiler_tcp_bridge"], "name": "Boiler", "manufacturer": "Custom"}
    }
    print("Publication configuration temperature...")
    sys.stdout.flush()
    client.publish("homeassistant/number/boiler_temp/config", json.dumps(temp_config), retain=True)
    client.publish("homeassistant/number/boiler_temp/state", "50", retain=True)
    print("Temperature configurée")
    sys.stdout.flush()
    
    print("Souscription aux topics...")
    sys.stdout.flush()
    client.subscribe("boiler/switch/set")
    client.subscribe("homeassistant/number/boiler_temp/set")
    print("Souscriptions actives")
    sys.stdout.flush()
    
    print("Démarrage de la boucle MQTT...")
    sys.stdout.flush()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    print("Lancement de main()")
    sys.stdout.flush()
    try:
        main()
    except Exception as e:
        print(f"Erreur dans main(): {e}")
        sys.stdout.flush()
        import traceback
        traceback.print_exc()
