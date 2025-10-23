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
    
    if topic == "homeassistant/switch/boiler/set":
        if payload == "ON":
            envoyer_trame_tcp(tcp_host, tcp_port, "J30253000000000001", client)  # mise en marche
        else:
            envoyer_trame_tcp(tcp_host, tcp_port, "J30254000000000001", client)  # arrêt
    
    elif topic == "homeassistant/climate/boiler/temperature/set":
        temp = int(float(payload))
        trame = f"B20180000000000{temp:03d}"
        envoyer_trame_tcp(tcp_host, tcp_port, trame, client)  # envoi consigne

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
        "command_topic": "homeassistant/switch/boiler/set",
        "state_topic": "homeassistant/switch/boiler/state",
        "unique_id": "boiler_power",
        "device": {"identifiers": ["boiler_tcp_bridge"], "name": "Boiler"}
    }
    client.publish("homeassistant/switch/boiler/config", json.dumps(switch_config), retain=True)
    
    # Climate (consigne température)
    climate_config = {
        "name": "Boiler Thermostat",
        "temperature_command_topic": "homeassistant/climate/boiler/temperature/set",
        "temperature_state_topic": "homeassistant/climate/boiler/temperature/state",
        "current_temperature_topic": "homeassistant/climate/boiler/current_temp",
        "min_temp": 30,
        "max_temp": 80,
        "temp_step": 1,
        "unique_id": "boiler_thermostat",
        "device": {"identifiers": ["boiler_tcp_bridge"], "name": "Boiler"}
    }
    client.publish("homeassistant/climate/boiler/config", json.dumps(climate_config), retain=True)
    
    client.subscribe("homeassistant/switch/boiler/set")
    client.subscribe("homeassistant/climate/boiler/temperature/set")
    
    client.loop_forever()

if __name__ == "__main__":
    main()
