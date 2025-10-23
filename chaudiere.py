import socket
import time
from datetime import datetime

def envoyer_trame_tcp(adresse, port, trame):
    try:
        with socket.create_connection((adresse, port), timeout=5) as client_socket:
            trame_complete = "08" + ''.join(f"{ord(c):02x}" for c in trame) + "0d"
            client_socket.sendall(bytes.fromhex(trame_complete))
            print(f"[{datetime.now()}] Trame envoyée : {trame}")
            reponse = client_socket.recv(1024)
            if reponse:
                print(f"[{datetime.now()}] Réponse : {reponse.decode(errors='ignore')}")
    except Exception as e:
        print(f"Erreur de connexion : {e}")

def main():
    adresse = "192.168.1.16"
    port = 8899
    trame = "I30004000000000000"  # exemple : lecture état chaudière
    while True:
        envoyer_trame_tcp(adresse, port, trame)
        time.sleep(60)  # intervalle en secondes

if __name__ == "__main__":
    main()
