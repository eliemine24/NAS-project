"""Module de génération de plans d'adressage IPv6 pour une topologie réseau.

Ce module gère la création automatique de plans d'adressage IPv6 pour les
routeurs et interfaces, basé sur une description d'intention (fichier JSON).
Il supporte les configurations intra-AS et inter-AS.
"""

import ipaddress
import json
import os
from generate_classes import json_to_dict

#VARIABLES GLOBALES

AS_CONFIG = {}  # Dictionnaire stockant les configurations des systèmes autonomes
EBGP_CONFIG = {}  # Dictionnaire stockant les configurations inter-AS (eBGP)


#FONCTIONS UTILES

def charger_json_en_dict(chemin_fichier):
    """Charge un fichier JSON et le retourne sous forme de dictionnaire.
    
    Args:
        chemin_fichier (str): Chemin vers le fichier JSON à charger.
        
    Returns:
        dict: Dictionnaire contenant les données JSON, ou None en cas d'erreur.
    """
    try:
        # Vérifier si le fichier existe avant de l'ouvrir
        if not os.path.exists(chemin_fichier):
            print(f"[-] Erreur : Fichier introuvable : {chemin_fichier}")
            return None
        # Ouvrir et parser le fichier JSON avec encodage UTF-8
        with open(chemin_fichier, 'r', encoding='utf-8') as fichier:
            return json.load(fichier)
    except Exception as e:
        # Gérer les erreurs de lecture/parsing
        print(f"[-] Erreur lecture JSON : {e}")
        return None

def sauvegarder_dict_en_json(dictionnaire, chemin_destination):
    """Sauvegarde un dictionnaire dans un fichier JSON.
    
    Args:
        dictionnaire (dict): Dictionnaire à sauvegarder.
        chemin_destination (str): Chemin de destination pour le fichier JSON.
        
    Note:
        Le fichier est sauvegardé avec une indentation de 4 espaces et sans
        conversion ASCII pour préserver les caractères spéciaux.
    """
    try:
        # Ouvrir le fichier en mode écriture avec encodage UTF-8
        with open(chemin_destination, 'w', encoding='utf-8') as fichier:
            # Sauvegarder le dictionnaire avec indentation et sans conversion ASCII
            json.dump(dictionnaire, fichier, indent=4, ensure_ascii=False)
        print(f"[+] Succès : Sauvegarde dans {chemin_destination}")
    except Exception as e:
        # Afficher les erreurs potentielles
        print(f"[-] Erreur sauvegarde : {e}")

def extraire_num(nom):
    """Extrait le nombre d'une chaîne de caractères.
    
    Args:
        nom (str): Chaîne contenant des chiffres et d'autres caractères.
        
    Returns:
        int: Le nombre extrait ou 0 si aucun chiffre n'est trouvé.
    """
    # Filtrer tous les caractères non-numériques
    chiffres = ''.join(filter(str.isdigit, nom))
    # Retourner le nombre ou 0 si aucun chiffre trouvé
    return int(chiffres) if chiffres else 0

#GENERATION

def initialiser_topologie(donnees_intent):
    """Analyse l'intention et remplit les variables globales AS_CONFIG et EBGP_CONFIG.
    
    Cette fonction initialise les structures de données globales en analysant
    la description d'intention fournie. Elle crée les configurations IPv6 pour
    chaque système autonome et pour les liaisons inter-AS (eBGP).
    
    Args:
        donnees_intent (dict): Dictionnaire contenant la description de la topologie
                              avec la clé 'Structure' contenant les AS.
                              
    Raises:
        Affiche un message d'erreur si la clé 'Structure' est absente.
        
    Side Effects:
        Modifie les variables globales AS_CONFIG et EBGP_CONFIG.
    """
    global AS_CONFIG, EBGP_CONFIG
    
    # Récupérer la structure principale du fichier d'intention
    structure = donnees_intent.get("Structure", {})
    if not structure:
        print("[-] ERREUR : La clé 'Structure' est absente du fichier JSON !")
        return

    # Récupérer la liste des systèmes autonomes
    as_list = list(structure.keys())
    # Adresse IPv4 de base pour les AS (0x100 en héxa) - utilisée si pas de plage spécifiée
    base_ip = 0x100 
    
    # Récupérer la data Intent pour les configurations globales
    intent_data = donnees_intent.get("Intent", {})
    
    # Créer une entrée AS_CONFIG pour chaque système autonome
    for i, id_as in enumerate(as_list):
        as_data = structure[id_as]
        
        # Vérifier si une plage d'adressage est spécifiée pour cet AS
        if "ADDRESSING_RANGE" in as_data:
            # Utiliser la plage spécifiée dans le JSON
            prefixe_str = as_data["ADDRESSING_RANGE"]
            print(f"[+] AS {id_as}: Utilisation de la plage d'adressage spécifiée: {prefixe_str}")
        else:
            # Générer un préfixe IPv6 unique pour cet AS
            prefixe_str = f"{hex(base_ip + i)[2:]}::/24"
            print(f"[+] AS {id_as}: Génération automatique de la plage: {prefixe_str}")
        
        reseau_principal = ipaddress.IPv4Network(prefixe_str)
        
        # Stocker les informations du réseau principal et ses sous-réseaux
        AS_CONFIG[id_as] = {
            "NOM_AS": as_data.get("AS_NAME"),
            "PROTOCOLE": as_data.get("PROTOCOL"),
            "RESEAU": reseau_principal,
            "SOUS_RESEAUX": list(reseau_principal.subnets(new_prefix=32)),  # Découper en /64
            "ROUTEURS": list(as_data.get("ROUTERS", {}).keys())
        }
    
    # Créer une configuration pour les liaisons inter-AS (eBGP)
    # Vérifier si une plage eBGP est spécifiée globalement
    if "EBGP_ADDRESSING_RANGE" in intent_data:
        prefixe_ebgp_str = intent_data["EBGP_ADDRESSING_RANGE"]
        print(f"[+] Liaisons eBGP: Utilisation de la plage spécifiée: {prefixe_ebgp_str}")
    else:
        prefixe_ebgp_str = "255:0:0:0/24"
        print(f"[+] Liaisons eBGP: Génération automatique de la plage: {prefixe_ebgp_str}")
    
    reseau_ebgp = ipaddress.IPv4Network(prefixe_ebgp_str)
    EBGP_CONFIG["INTER_AS"] = {
        "RESEAU": reseau_ebgp,
        "SOUS_RESEAUX": list(reseau_ebgp.subnets(new_prefix=32))  # Découper en /64
    }
    print(f"[+] Topologie initialisée avec {len(AS_CONFIG)} AS.")

def creer_registre_dynamique(donnees_intent):
    """Crée un registre dynamique d'adressage pour tous les routeurs et interfaces.
    
    Construit un dictionnaire contenant les adresses IPv6 attribuées à chaque
    interface de chaque routeur, en gérant les liaisons internes et inter-AS.
    
    Args:
        donnees_intent (dict): Dictionnaire contenant la structure de la topologie.
        
    Returns:
        dict: Registre avec la structure {routeur: {interface: adresse}}.
        
    Note:
        Utilise les configurations préalablement générées dans AS_CONFIG et EBGP_CONFIG.
    """
    registre = {}  # Dictionnaire pour stocker les adresses
    liens_vus = set()  # Ensemble pour éviter de traiter deux fois le même lien
    # Initialiser les index des sous-réseaux pour chaque AS
    index_lien_interne = {id_as: 1 for id_as in AS_CONFIG}
    index_ebgp = 1  # Index pour les sous-réseaux eBGP
    loopback_address_skip_number = 100 # on définit un nombre d'addresse à skip (à laissez pour les addresses de liens) quand on assigne les addresses de loopback.

    # Parcourir chaque système autonome
    for id_as, as_info in AS_CONFIG.items():
        # Parcourir chaque routeur du système autonome
        nmb_routeur = 1
        nmb_routeur_lb = 1
        for nom_r in as_info["ROUTEURS"]:
            # Initialiser l'entrée du routeur dans le registre
            registre.setdefault(nom_r, {})
            # Récupérer le réseau de loopback
            lb_net = as_info["SOUS_RESEAUX"][0]
            for nom_int, info_int in donnees_intent["Structure"][id_as]["ROUTERS"][nom_r]["INTERFACES"].items():
                if "PROTOCOL" in info_int and info_int["PROTOCOL"] == "EBGP":
                    # Assigner une adresse loopback au routeur si il est de bordure
                    registre[nom_r]["LOOPBACK0"] = f"{lb_net.hosts()[0]+loopback_address_skip_number+nmb_routeur_lb}/32"
                    nmb_routeur_lb += 1
                    break

            # Parcourir les interfaces du routeur
            interfaces = donnees_intent["Structure"][id_as]["ROUTERS"][nom_r]["INTERFACES"]
            for nom_int, info_int in interfaces.items():
                # Récupérer le voisin et l'interface voisine
                voisin = list(info_int["NEIGHBORS"].keys())[0]
                int_voisin = info_int["NEIGHBORS"][voisin]
                # Créer une paire triée pour identifier le lien de manière unique
                paire = tuple(sorted((nom_r, voisin)))
                # Traiter le lien seulement s'il n'a pas déjà été traité
                if paire not in liens_vus:
                    # Déterminer si c'est un lien eBGP ou interne
                    if info_int.get("PROTOCOL") == "EBGP":
                        # Utiliser un sous-réseau eBGP
                        net = EBGP_CONFIG["INTER_AS"]["SOUS_RESEAUX"][index_ebgp]
                        index_ebgp += 4
                    else:
                        # Utiliser un sous-réseau interne à l'AS
                        idx = index_lien_interne[id_as]
                        net = as_info["SOUS_RESEAUX"][idx]
                        index_lien_interne[id_as] += 4
                    
                    # Assigner les adresses aux deux extrémités du lien
                    registre[nom_r][nom_int] = f"{net.hosts()[0]}/30"
                    registre.setdefault(voisin, {})[int_voisin] = f"{net.hosts()[0]+1}/30"
                    # Marquer le lien comme traité
                    liens_vus.add(paire)
            nmb_routeur += 1
    return registre

def generer_plan_adressage(intention):
    """Génère le plan d'adressage complet à partir de l'intention.
    
    Crée une structure complète contenant l'adressage de tous les routeurs
    et interfaces, prêt à être utilisé par les générateurs de configuration.
    
    Args:
        intention (dict): Dictionnaire contenant la description de la topologie.
        
    Returns:
        dict: Plan d'adressage avec la structure {Structure: {AS: {ROUTERS: ...}}}.
        
    Note:
        Retourne un dictionnaire vide si AS_CONFIG n'a pas été initialisé.
    """
    # Vérifier que la topologie a été initialisée
    if not AS_CONFIG:
        print("[-] Erreur : AS_CONFIG est vide. L'initialisation a échoué.")
        return {"Intent": {}, "Structure": {}}

    # Générer le registre d'adressage (qui contient tous les adresses attribuées)
    registre = creer_registre_dynamique(intention)
    # Structure pour stocker le résultat final
    resultat = {"Intent": intention.get("Intent", {}), "Structure": {}}

    # Parcourir chaque système autonome
    nmb_routeur = 1
    for id_as, info_as in AS_CONFIG.items():
        # Initialiser l'entrée du système autonome
        resultat["Structure"][id_as] = {
            "AS_NAME": info_as["NOM_AS"],
            "PROTOCOL": info_as["PROTOCOLE"],
            "ROUTERS": {}
        }
        # Récupérer les routeurs source de l'intention
        routeurs_source = intention["Structure"][id_as]["ROUTERS"]

        # Parcourir chaque routeur une première fois pour trouver les routeurs de bordures
        routeur_bordure = []
        for nom_r, contenu_r in routeurs_source.items():
            for nom_int, info_int in contenu_r["INTERFACES"].items():
                if "PROTOCOL" in info_int and info_int["PROTOCOL"] == "EBGP":
                    routeur_bordure.append(nom_r)
                    break

        for nom_r, contenu_r in routeurs_source.items():

            # Créer la structure pour le routeur avec son ID
            r_data = {"ROUTER_ID": f"{nmb_routeur}.{nmb_routeur}.{nmb_routeur}.{nmb_routeur}", "INTERFACES": {}}

            # Parcourir les interfaces du routeur
            for nom_int, info_int in contenu_r["INTERFACES"].items():
                # Récupérer le voisin et son interface
                nom_v = list(info_int["NEIGHBORS"].keys())[0]
                int_v = info_int["NEIGHBORS"][nom_v]

                #si un cost spécial pour OSPF existe, l'ajouter dans la configuration de l'interface
                if "COST" in info_int.keys():

                    # Créer l'entrée de l'interface avec ses adresses
                    r_data["INTERFACES"][nom_int] = {
                        "ADDRESS": registre[nom_r][nom_int],
                        "NEIGHBORS_ADDRESS": [registre[nom_v][int_v]],
                        "COST": info_int["COST"]
                    }

                else:

                    # Créer l'entrée de l'interface avec ses adresses
                    r_data["INTERFACES"][nom_int] = {
                        "ADDRESS": registre[nom_r][nom_int],
                        "NEIGHBORS_ADDRESS": [registre[nom_v][int_v]]
                    }

                # Ajouter le protocole eBGP si applicable
                if "PROTOCOL" in info_int: r_data["INTERFACES"][nom_int]["PROTOCOL"] = "EBGP"
            
            if nom_r in routeur_bordure:
                # Récupérer les adresses loopback des autres routeurs de bordures du même AS
                autres_lb = []
                for a in info_as["ROUTEURS"]:
                    #on check si c'est des routeurs de bordures
                    if a != nom_r and a in routeur_bordure:
                        autres_lb.append(registre[a]["LOOPBACK0"])
                # Configurer l'interface loopback
                r_data["INTERFACES"]["LOOPBACK0"] = {
                    "ADDRESS": registre[nom_r]["LOOPBACK0"],
                    "NEIGHBORS_ADDRESS": autres_lb
                }
            # Ajouter le routeur au résultat
            resultat["Structure"][id_as]["ROUTERS"][nom_r] = r_data
            nmb_routeur += 1
    return resultat


def ecrire_plan_adressage(file_name):
    dossier = os.path.dirname(os.path.abspath(__file__))
    # Construire le chemin du fichier d'intention
    f_entree = os.path.join(dossier, file_name)

    # Charger le fichier d'intention JSON
    intent = charger_json_en_dict(f_entree)


    # Vérifier si le fichier a pu être chargé avec succès
    if intent:
        print(f"Clés trouvées à la racine du JSON : {list(intent.keys())}")
        
        # Vérifier la présence de la clé 'Structure' (majuscule ou minuscule)
        cle_structure = "Structure" if "Structure" in intent else "structure"
        
        if cle_structure in intent:
            print(f"Succès : Clé '{cle_structure}' trouvée !")
            # Initialiser la topologie (remplit AS_CONFIG et EBGP_CONFIG)
            initialiser_topologie(intent)
            # Générer le plan d'adressage complet
            mon_plan = generer_plan_adressage(intent)
            # Sauvegarder le résultat dans un fichier JSON
            sauvegarder_dict_en_json(mon_plan, "test.json")
        else:
            print("ERREUR CRITIQUE : Aucune clé 'Structure' ou 'structure' trouvée.")
            print("Voici le contenu du fichier pour t'aider :", intent)

