# =============================
# === Fonctions utilitaires ===
# =============================

from router import Router
from interface import Interface
from AS import AS
import os
import json

def find_local_path():
    """Trouve l'emplacement local du programme et l'exporte."""
    local_path = os.path.dirname(os.path.abspath(__file__))
    return local_path


# =====================================
# === Génération des classes réseau ===
# =====================================

def json_to_dict(in_file):
    """Convertit un fichier JSON en dictionnaire Python."""
    with open(in_file, 'r') as f:
        data = json.load(f)
    return data


def generate_network_classes(int_file):
    """Lit le fichier d'intention et crée toutes les classes nécessaires."""
    intent = json_to_dict(int_file)
    router_list = []
    as_list = []

    # génération des routers
    for as_name, as_obj in intent["Structure"].items():
        for router_name, router_info in as_obj["ROUTERS"].items():
            #génération du router
            new_router = generate_router(router_name, router_info)
            #ajout du nom d'AS au router
            new_router.AS_name = as_obj["AS_NAME"]
            for interface_name, interface_info in router_info["INTERFACES"].items():
                new_router.liste_int.append(
                    generate_interface(interface_name, interface_info, as_obj)
                )
            router_list.append(new_router)
    
    # génération des AS
    for as_name, as_relations in intent["Intent"].items():
        if as_name != "EBGP_ADDRESSING_RANGE":
            new_as = generate_AS(as_relations,intent)
            as_list.append(new_as)

    return router_list, as_list


def generate_router(router_name, router_info):
    """Génère un router à partir d'un dictionnaire d'infos du router en question"""
    router = Router(
        router_name,                    #nom du router (string)
        router_info["ROUTER_ID"],       #ID du router  (string)
        len(router_info["INTERFACES"])  #nombre d'interfaces (int)
    )
    return router


def generate_interface(interface_name, interface_info, as_obj):
    """Génère les classes Interface associées à un routeur."""
    interface = Interface(interface_name)

    # configuration à partir des infos
    interface.address = interface_info.get("ADDRESS", "")
    for neighbor in interface_info.get("NEIGHBORS_ADDRESS", []):
        interface.neighbors_address.append(neighbor)
    #ajout des protocols à l'interface créé si il n'y en a pas déjà un
    if "PROTOCOL" not in interface_info:
        interface.protocol_list.append(as_obj["PROTOCOL"])
    #ajouter EBGP en protocol si il y a un parametre "protocol" dans l'intent file
    else:
        interface.protocol_list.append(interface_info.get("PROTOCOL",""))
    #ajout du cout du lien si l'interface communique en ospf
    if "COST" in interface_info:
        interface.cost = interface_info.get("COST", "")
    return interface

def generate_AS(as_relations,intent):
    """Génère les classes AS"""
    As = AS(as_relations.get("AS_NAME", ""))
    # ajoute chaque relation PEER à l'AS
    if "PEERS" in as_relations:
        for p in as_relations.get("PEERS", []):
            As.peers.append(intent["Intent"][p]["AS_NAME"])
    # ajoute chaque relation PROVIDER à l'AS
    if "PROVIDERS" in as_relations:
        for p in as_relations.get("PROVIDERS", []):
            As.providers.append(intent["Intent"][p]["AS_NAME"])
    # ajoute chaque relation CLIENT à l'AS
    if "CLIENTS" in as_relations:
        for c in as_relations.get("CLIENTS", []):
            As.clients.append(intent["Intent"][c]["AS_NAME"])
    return As

# =======================
# === TESTS FONCTIONS ===
# =======================
# (ça fonctionne)
"""
local_path = find_local_path()
print(f"local path : {local_path}")

router_list, as_list = generate_network_classes(local_path + "/intent_file.json")

for r in router_list:
    print(f"{r.name} (AS {r.AS_name}) | {r.ID} | {r.nb_int}")
    for i in r.liste_int:
        print(f"  {i.name} {i.address} {i.protocol_list} neighbors: {i.neighbors_address}")

for a in as_list:
    print(f"{a.name} peers : {a.peers}, clients : {a.clients}, providers : {a.providers}")
"""