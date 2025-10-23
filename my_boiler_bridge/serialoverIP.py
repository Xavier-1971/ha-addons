import socket
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.panel import Panel
from datetime import datetime

console = Console()

def lire_trames(fichier):
    """Lit les trames et leurs descriptions depuis un fichier texte."""
    trames = []
    with open(fichier, 'r') as f:
        for ligne in f:
            trame, description = ligne.strip().split(",", 1)
            trames.append((trame, description))
    return trames

def envoyer_trame_tcp(adresse, port, trame):
    """Envoie une trame à un serveur TCP."""
    try:
        with socket.create_connection((adresse, port), timeout=5) as client_socket:
            trame_complete = "08" + ''.join(f"{ord(c):02x}" for c in trame) + "0d"
            #trame_complete =''.join(f"{ord(c):02x}" for c in trame)
            client_socket.sendall(bytes.fromhex(trame_complete))
            console.print(Panel(f"[bold blue]Trame envoyée :[/bold blue] [yellow]{trame}[/yellow]", title="Statut"))
            
            # Lire la réponse
            reponse = client_socket.recv(1024)
            if reponse:
                reponse_decoded = reponse.decode(errors='ignore')
                console.print(Panel(f"[bold green]Réponse reçue :[/bold green] [yellow]{reponse_decoded}[/yellow]", title="Réponse"))
                return reponse_decoded
            else:
                console.print("[yellow]Aucune réponse reçue.[/yellow]")
    except (socket.timeout, socket.error) as e:
        console.print(f"[red]Erreur de connexion : {e}[/red]")

def enregistrer_historique(trame, reponse, fichier="historique_tcp.txt"):
    """Enregistre la trame envoyée et la réponse reçue dans un fichier d'historique."""
    with open(fichier, 'a') as f:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{now} - Trame envoyée: {trame}\n")
        if reponse:
            f.write(f"{now} - Réponse reçue: {reponse}\n")
        else:
            f.write(f"{now} - Aucune réponse reçue\n")
        f.write("-" * 40 + "\n")

def afficher_trames(trames):
    """Affiche les trames disponibles sous forme de table avec description."""
    table = Table(title="Trames Disponibles")
    table.add_column("Numéro", style="cyan", justify="right")
    table.add_column("Trame", style="magenta")
    table.add_column("Description", style="green")

    for idx, (trame, description) in enumerate(trames, start=1):
        table.add_row(str(idx), trame, description)

    console.print(table)

def main():
    
    
    # Paramètres du serveur TCP
    adresse = "192.168.1.16"
    port = 8899
    
    while True:
        # Charger les trames
        trames = lire_trames("frames.txt")
        # Afficher les trames disponibles
        afficher_trames(trames)
        
        # Demander quelle trame envoyer
        choix = int(Prompt.ask("Entrez le numéro de la trame à envoyer (0 pour quitter)"))
        
        if choix == 0:
            console.print("[blue]Fin de l'envoi des trames.[/blue]")
            break
        elif 1 <= choix <= len(trames):
            trame, _ = trames[choix - 1]
            reponse = envoyer_trame_tcp(adresse, port, trame)
            enregistrer_historique(trame, reponse)
        else:
            console.print("[red]Choix invalide.[/red]")

if __name__ == "__main__":
    main()
