import socket
import time
import json
import os
from datetime import datetime
import paho.mqtt.client as mqtt  # type: ignore

def setup_mqtt_discovery(client):
    """Configure MQTT Discovery une seule fois au démarrage"""
    device_info = {
        "identifiers": ["boiler_tcp_bridge"],
        "name": "Boiler",
        "manufacturer": "Custom",
        "model": "TCP Bridge"
    }
    
    # Switch ON/OFF
    switch_config = {
        "name": "Boiler Power",
        "command_topic": "boiler/switch/set",
        "state_topic": "boiler/switch/state",
        "unique_id": "boiler_power_switch",
        "device": device_info
    }
    
    # Number pour consigne température
    temp_config = {
        "name": "Boiler Temperature",
        "command_topic": "boiler/temp/set",
        "state_topic": "boiler/temp/state",
        "min": 40,
        "max": 80,
        "step": 1,
        "unit_of_measurement": "°C",
        "unique_id": "boiler_temp",
        "device": device_info
    }
    
    # Capteur température eau
    water_temp_config = {
        "name": "Boiler Water Temperature",
        "state_topic": "boiler/water_temp/state",
        "unit_of_measurement": "°C",
        "device_class": "temperature",
        "unique_id": "boiler_water_temp",
        "device": device_info
    }
    
    # Capteur température fumée
    smoke_temp_config = {
        "name": "Boiler Smoke Temperature",
        "state_topic": "boiler/smoke_temp/state",
        "unit_of_measurement": "°C",
        "device_class": "temperature",
        "unique_id": "boiler_smoke_temp",
        "device": device_info
    }
    
    # Capteur code erreur
    error_config = {
        "name": "Boiler Error Code",
        "state_topic": "boiler/error/state",
        "unique_id": "boiler_error",
        "device": device_info
    }
    
    # Capteur étape d'allumage
    ignition_config = {
        "name": "Boiler Ignition Step",
        "state_topic": "boiler/ignition/state",
        "unique_id": "boiler_ignition",
        "device": device_info
    }
    
    print("Publication configurations MQTT Discovery...", flush=True)
    client.publish("homeassistant/switch/boiler_power_switch/config", json.dumps(switch_config), retain=True)
    client.publish("homeassistant/number/boiler_temp/config", json.dumps(temp_config), retain=True)
    client.publish("homeassistant/sensor/boiler_water_temp/config", json.dumps(water_temp_config), retain=True)
    client.publish("homeassistant/sensor/boiler_smoke_temp/config", json.dumps(smoke_temp_config), retain=True)
    client.publish("homeassistant/sensor/boiler_error/config", json.dumps(error_config), retain=True)
    client.publish("homeassistant/sensor/boiler_ignition/config", json.dumps(ignition_config), retain=True)
    
    # États initiaux
    client.publish("boiler/switch/state", "OFF", retain=True)
    client.publish("boiler/temp/state", "50", retain=True)
    client.publish("boiler/water_temp/state", "0", retain=True)
    client.publish("boiler/smoke_temp/state", "0", retain=True)
    client.publish("boiler/error/state", "0", retain=True)
    client.publish("boiler/ignition/state", "110", retain=True)
    print("MQTT Discovery configuré", flush=True)

def analyser_reponse(trame_envoyee, reponse, mqtt_client):
    """Analyse la réponse de la chaudière et publie les états réels"""
    if not reponse:
        return False
    
    reponse_clean = reponse.strip('\x08\r\n')
    
    # Commandes ON/OFF
    if trame_envoyee == "J30253000000000001" and reponse_clean == "I30253000000000000":
        mqtt_client.publish("boiler/switch/state", "ON", retain=True)
        print("Chaudière démarrée avec succès")
        return True
    elif trame_envoyee == "J30254000000000001" and reponse_clean == "I30254000000000000":
        mqtt_client.publish("boiler/switch/state", "OFF", retain=True)
        print("Chaudière arrêtée avec succès")
        return True
    

    
    # Consigne température (écriture)
    elif trame_envoyee.startswith("B201800000000000") and reponse_clean.startswith("A201800000000000"):
        temp_confirmee = int(reponse_clean[-3:])
        mqtt_client.publish("boiler/temp/state", str(temp_confirmee), retain=True)
        print(f"Consigne température confirmée : {temp_confirmee}°C")
        return True
    
    # Consigne température (lecture)
    elif trame_envoyee == "A20180000000000000" and reponse_clean.startswith("B201800000000000"):
        temp_actuelle = int(reponse_clean[-3:])
        mqtt_client.publish("boiler/temp/state", str(temp_actuelle), retain=True)
        print(f"Consigne température actuelle : {temp_actuelle}°C")
        return True
    
    # Température eau (I30017000000000000 -> J30017000000000XXX)
    elif trame_envoyee == "I30017000000000000" and reponse_clean.startswith("J30017000000000"):
        temp_eau = int(reponse_clean[-3:])
        mqtt_client.publish("boiler/water_temp/state", str(temp_eau), retain=True)
        print(f"Température eau : {temp_eau}°C")
        return True
    
    # Température fumée (I30005000000000000 -> J30005000000000XXX)
    elif trame_envoyee == "I30005000000000000" and reponse_clean.startswith("J30005000000000"):
        temp_fumee = int(reponse_clean[-3:])
        mqtt_client.publish("boiler/smoke_temp/state", str(temp_fumee), retain=True)
        print(f"Température fumée : {temp_fumee}°C")
        return True
    
    # Code erreur (I30002000000000000 -> J30002000000000XXX)
    elif trame_envoyee == "I30002000000000000" and reponse_clean.startswith("J30002000000000"):
        code_erreur = int(reponse_clean[-3:])
        mqtt_client.publish("boiler/error/state", str(code_erreur), retain=True)
        print(f"Code erreur : {code_erreur}")
        return True
    
    # Étape d'allumage (J30011000000000000 -> I30011000000000XXX)
    elif trame_envoyee == "J30011000000000000" and reponse_clean.startswith("I30011000000000"):
        etape_allumage = int(reponse_clean[-3:])
        mqtt_client.publish("boiler/ignition/state", str(etape_allumage), retain=True)
        
        # Déterminer l'état ON/OFF basé sur l'étape d'allumage
        if etape_allumage == 110:
            mqtt_client.publish("boiler/switch/state", "OFF", retain=True)
            print(f"Étape d'allumage {etape_allumage} - Chaudière à l'arrêt")
        else:
            mqtt_client.publish("boiler/switch/state", "ON", retain=True)
            print(f"Étape d'allumage {etape_allumage} - Chaudière en marche")
        return True
    
    print(f"Réponse non reconnue : {reponse_clean}")
    return False

def envoyer_trame_tcp(adresse, port, trame, mqtt_client):
    try:
        with socket.create_connection((adresse, port), timeout=3) as client_socket:
            trame_complete = "08" + ''.join(f"{ord(c):02x}" for c in trame) + "0d"
            client_socket.sendall(bytes.fromhex(trame_complete))
            print(f"[{datetime.now()}] Trame envoyée : {trame}")
            reponse = client_socket.recv(1024)
            if reponse:
                reponse_str = reponse.decode(errors='ignore')
                print(f"[{datetime.now()}] Réponse : {reponse_str}")
                
                # Analyser et exploiter la réponse
                analyser_reponse(trame, reponse_str, mqtt_client)
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
        else:
            print("Arrêt chaudière...")
            envoyer_trame_tcp(tcp_host, tcp_port, "J30254000000000001", client)
    
    elif topic == "boiler/temp/set":
        temp = int(float(payload))
        trame = f"B20180000000000{temp:03d}"
        print(f"Réglage consigne : {temp}°C")
        envoyer_trame_tcp(tcp_host, tcp_port, trame, client)

def main():
    # Lecture depuis les variables d'environnement (exportées par run.sh)
    tcp_host = os.environ.get('TCP_HOST', '192.168.1.16')
    tcp_port = int(os.environ.get('TCP_PORT') or '8899')
    mqtt_host = os.environ.get('MQTT_HOST') or 'core-mosquitto'
    mqtt_port = int(os.environ.get('MQTT_PORT') or '1883')
    mqtt_user = os.environ.get('MQTT_USER', '')
    mqtt_password = os.environ.get('MQTT_PASSWORD', '')
    
    print(f"Variables d'environnement MQTT: {[k for k in os.environ.keys() if 'MQTT' in k]}")
    
    print(f"Configuration: TCP {tcp_host}:{tcp_port}, MQTT {mqtt_host}:{mqtt_port}, User: {mqtt_user}", flush=True)
    
    print("Création client MQTT...", flush=True)
    # Utilisation de la nouvelle API MQTT
    try:
        # Nouvelle API VERSION2 (recommandée)
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    except (AttributeError, ImportError):
        # Fallback vers VERSION1 si VERSION2 non disponible
        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        except (AttributeError, ImportError):
            # Ancienne API (fallback final)
            client = mqtt.Client()
    print("Client MQTT créé", flush=True)
    
    def on_connect(client, userdata, flags, rc):
        print(f"Connexion MQTT: code {rc}", flush=True)
    
    client.user_data_set((tcp_host, tcp_port))
    client.on_message = on_message
    client.on_connect = on_connect
    
    # Configuration authentification MQTT
    if mqtt_user and mqtt_password:
        client.username_pw_set(mqtt_user, mqtt_password)
        print(f"Authentification MQTT configurée pour: {mqtt_user}", flush=True)
    else:
        print(f"Pas d'authentification MQTT (user: '{mqtt_user}', pwd: {'***' if mqtt_password else 'vide'})", flush=True)
        # Essai sans authentification
        print("Tentative de connexion sans authentification...", flush=True)
    
    print("Callbacks configurés", flush=True)
    print("Connexion à MQTT...", flush=True)
    
    try:
        client.connect(mqtt_host, mqtt_port, 60)
        client.loop_start()
        print("Connecté à MQTT", flush=True)
    except Exception as e:
        print(f"Erreur connexion MQTT: {e}", flush=True)
        print("Tentative avec 'localhost'...", flush=True)
        try:
            client.connect('localhost', mqtt_port, 60)
            client.loop_start()
            print("Connecté à MQTT via localhost", flush=True)
        except Exception as e2:
            print(f"Erreur connexion localhost: {e2}", flush=True)
            return
    
    # Attendre que la connexion soit stable
    time.sleep(2)
    print("Connexion MQTT stabilisée", flush=True)
    
    # Configuration MQTT Discovery (une seule fois)
    setup_mqtt_discovery(client)
    
    print("Souscription aux topics...", flush=True)
    client.subscribe("boiler/switch/set")
    client.subscribe("boiler/temp/set")
    
    print("Souscriptions actives", flush=True)
    print("Démarrage de la boucle MQTT...", flush=True)
    
    # Fonction pour interroger les capteurs
    def interroger_capteurs():
        print("Mise à jour des capteurs...", flush=True)
        envoyer_trame_tcp(tcp_host, tcp_port, "J30011000000000000", client)  # étape d'allumage pour état ON/OFF
        time.sleep(2)
        envoyer_trame_tcp(tcp_host, tcp_port, "I30002000000000000", client)  # code erreur
        time.sleep(2)
        envoyer_trame_tcp(tcp_host, tcp_port, "A20180000000000000", client)  # consigne actuelle
        time.sleep(2)
        envoyer_trame_tcp(tcp_host, tcp_port, "I30017000000000000", client)  # temp eau
        time.sleep(2)
        envoyer_trame_tcp(tcp_host, tcp_port, "I30005000000000000", client)  # temp fumée
        print("Capteurs mis à jour", flush=True)
    
    # Interrogation initiale
    interroger_capteurs()
    
    try:
        while True:
            time.sleep(60)  # Attendre 60 secondes
            interroger_capteurs()
    except KeyboardInterrupt:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    print("Lancement de main())", flush=True)
    try:
        main()
    except Exception as e:
        print(f"Erreur dans main(): {e}", flush=True)
        import traceback
        traceback.print_exc()
