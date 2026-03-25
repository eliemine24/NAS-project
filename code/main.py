# ============
# === MAIN ===
# ============

from router import Router
from interface import Interface
from generate_classes import *
from write_config import *
from drag_n_drop_bot import find_repository_names, drag_and_drop
from generer_plan_adressage import generer_plan_adressage
import os

if os.name == 'nt':
    PROJECT_NAME = str(input("Nom du dossier contenant le projet : "))
    LPATH = find_local_path() +"\\"                        # chemin du script
    HPATH = LPATH.rstrip('\\').rsplit('\\', 1)[0]          # chemin du projet
    MAIN_DEST = HPATH + "\\project-files\\dynamips"         # destination générale des .cfg
    FILE_NAME = "code\\intent_file.json"
    INTENT = json_to_dict(FILE_NAME)             # fichier d'intention
    IPPROTOCOL = int(input("Quel protocol ip utilisez-vous ? (4 ou 6): "))

else:
    LPATH = find_local_path() +"/"                        # chemin du script
    HPATH = LPATH.rstrip('/').rsplit('/', 1)[0]           # chemin du projet
    MAIN_DEST = HPATH + "/project-files/dynamips"         # destination générale des .cfg
    FILE_NAME = "intent_file_2_encore_plus_gros_reseau.json"
    INTENT = json_to_dict(FILE_NAME)             # fichier d'intention
    PROJECT_NAME = "projet_test"    #str(input("Nom du dossier contenant le projet : "))

print("--- pathes ---")
print(f"LPATH : {LPATH}")
print(f"HPATH : {HPATH}\n")

generer_plan_adressage(INTENT)

# génération des routeurs et interfaces
router_list, as_list = generate_network_classes("test.json")

# affichage 
"""
for r in router_list:
    print(f"{r.name} (AS {r.AS_name}) | {r.ID} | {r.nb_int}")
    for i in r.liste_int:
        print(f"  {i.name} {i.address} {i.protocol} neighbors: {i.neighbors_address}")
"""

# écriture cfg 
for r in router_list:
    outfile = LPATH+r.name+ ".cfg"
    write_config(r, outfile, router_list, as_list,IPPROTOCOL)

# drag n drop
REPONAMES = find_repository_names(router_list, PROJECT_NAME, HPATH)
print("--- reponames ---")
print(REPONAMES)

drag_and_drop(LPATH, HPATH, PROJECT_NAME, REPONAMES)