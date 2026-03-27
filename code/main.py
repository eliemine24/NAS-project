# ============
# === MAIN ===
# ============

from router import Router
from interface import Interface
from generate_classes import *
from write_config import *
from drag_n_drop_bot import find_repository_names, drag_and_drop
from generer_plan_adressage import ecrire_plan_adressage
import os

if os.name == 'nt':     # for windows os
    PROJECT_NAME = str(input("Nom du dossier contenant le projet : "))
    LPATH = find_local_path() +"\\"                        # chemin du script
    HPATH = LPATH.rstrip('\\').rsplit('\\', 1)[0]          # chemin du projet
    FILE_NAME = "code\\pingu.json"
    INTENT = json_to_dict(FILE_NAME)             # fichier d'intention

else:
    LPATH = find_local_path() +"/"                        # chemin du script
    HPATH = LPATH.rstrip('/').rsplit('/', 1)[0]+"/"           # chemin du projet
    FILE_NAME = "pingu.json"                               # intent file's name
    INTENT = json_to_dict(FILE_NAME)             # fichier d'intention
    PROJECT_NAME = "projet_test"    #str(input("Nom du dossier contenant le projet : "))


print("--- pathes ---")
print(f"LPATH : {LPATH}")
print(f"HPATH : {HPATH}\n")
print("--------------")

IPPROTOCOL = 4 #int(input("Quel protocol ip utilisez-vous ? (4 ou 6): "))

ecrire_plan_adressage(FILE_NAME)

# génération des routeurs et interfaces
router_list, as_list = generate_network_classes(LPATH+"test.json")

# affichage 
"""
for r in router_list:
    print(f"{r.name} (AS {r.AS_name}) | {r.ID} | {r.nb_int}")
    for i in r.liste_int:
        print(f"  {i.name} {i.address} {i.protocol} neighbors: {i.neighbors_address}")
"""

# écriture cfg 
rd_incrementer = 100
for r in router_list:
    outfile = LPATH+r.name+ ".cfg"
    routeur_bordure = False
    for int in r.liste_int:
        if "EBGP" in int.protocol_list:
            routeur_bordure = True
    
    if routeur_bordure:
        for a in as_list:
            if a.name == r.AS_name:
                if a.vpn_clients != {}:
                    write_config(r, outfile, router_list, as_list,IPPROTOCOL,rd_incrementer)
                    rd_incrementer += 10*len(a.vpn_clients.keys()) # on augmente le nombre du rd incrementer par rapport au nombre de route VPN que le PE a
                else:
                    write_config(r, outfile, router_list, as_list,IPPROTOCOL)
    else:
        write_config(r, outfile, router_list, as_list,IPPROTOCOL)  
    

# drag n drop
REPONAMES = find_repository_names(router_list, PROJECT_NAME, HPATH)
print("--- reponames ---")
for repo in REPONAMES.items() : print(repo)

drag_and_drop(LPATH, HPATH, PROJECT_NAME, REPONAMES)