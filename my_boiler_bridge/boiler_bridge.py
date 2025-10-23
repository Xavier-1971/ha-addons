import socket
import time
import json
import os
from datetime import datetime
import paho.mqtt.client as mqtt

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
    
    if topic == "homeassistant/switch/boiler_power/set":
        if payload == "ON":
            envoyer_trame_tcp(tcp_host, tcp_port, "J30253000000000001", client)  # mise en marche
            client.publish("homeassistant/switch/boiler_power/state", "ON", retain=True)
        else:
            envoyer_trame_tcp(tcp_host, tcp_port, "J30254000000000001", client)  # arrêt
            client.publish("homeassistant/switch/boiler_power/state", "OFF", retain=True)
    
    elif topic == "homeassistant/number/boiler_temp/set":
        temp = int(float(payload))
        trame = f"B20180000000000{temp:03d}"
        envoyer_trame_tcp(tcp_host, tcp_port, trame, client)  # envoi consigne
        client.publish("homeassistant/number/boiler_temp/state", str(temp), retain=True)

def main():
    options = json.loads(os.environ.get('OPTIONS', '{}'))
    tcp_host = options.get('tcp_host')
    tcp_port = options.get('tcp_port')
    mqtt_host = options.get('mqtt_host', 'core-mosquitto')
    mqtt_port = options.get('mqtt_port', 1883)
    
    client = mqtt.Client()
    client.user_data_set((tcp_host, tcp_port))
    client.on_message = on_message
    client.connect(mqtt_host, mqtt_port, 60)
    
    # Switch ON/OFF
    switch_config = {
        "name": "Boiler Power",
        "command_topic": "homeassistant/switch/boiler_power/set",
        "state_topic": "homeassistant/switch/boiler_power/state",
        "unique_id": "boiler_power",
        "device": {"identifiers": ["boiler_tcp_bridge"], "name": "Boiler", "manufacturer": "Custom"}
    }
    client.publish("homeassistant/switch/boiler_power/config", json.dumps(switch_config), retain=True)
    client.publish("homeassistant/switch/boiler_power/state", "OFF", retain=True)
    
    # Number pour consigne température (plus simple que climate)
    temp_config = {
        "name": "Boiler Temperature",
        "command_topic": "homeassistant/number/boiler_temp/set",
        "state_topic": "homeassistant/number/boiler_temp/state",
        "min": 30,
        "max": 80,
        "step": 1,
        "unit_of_measurement": "°C",
        "unique_id": "boiler_temp",
        "device": {"identifiers": ["boiler_tcp_bridge"], "name": "Boiler", "manufacturer": "Custom"}
    }
    client.publish("homeassistant/number/boiler_temp/config", json.dumps(temp_config), retain=True)
    client.publish("homeassistant/number/boiler_temp/state", "50", retain=True)
    
    client.subscribe("homeassistant/switch/boiler_power/set")
    client.subscribe("homeassistant/number/boiler_temp/set")
    
    client.loop_forever()

if __name__ == "__main__":
    main()
