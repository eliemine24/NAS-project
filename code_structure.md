# CODE STRUCTURE

### CRÉATION DES CLASSES 
- ouverture / lecture du fichier d'intention
- récupération des noms des routeurs (+ vérification du nb) et (création d'une liste de classes ?)
- (vérification des liens)
- configuration des routeurs = rédaction des .cfg de chaque routeur et placement dans l'arborescence

### CONFIGURATION D'UN ROUTEUR = RÉDACTION DES `.cfg`:
- récupération des infos générales du routeur : noms, nb d'interfaces, protocole(s)
- récupération des infos de chaque interfaces :  @ip, protocol, voisins
- pour chaque routeur : vérifier les protocoles (BGP/OSPF/RIP)
- à chaque fois, stockage dans les classes de noms correspondants
- copie du `.cfg` du router
- modification du `.cfg` à partir des infos récupérées 
- placement du `.cfg` dans l'arborescence (attention les noms dans l'arborescence sont anonymes)

### RÉDACTION DU `.cfg` :
- header
- liste des interfaces
- liste des routers par protocole
- router et règles bgp

### Classes

- `router` : name, interfaces_number, interfaces_list, protocols_list
- `interface` : name, address, neighbors_address, protocol
- `AS` : name, providers, peers, clients

### Fonctions

#### générer_plan_adressage

* **`charger_json_en_dict(chemin_fichier)`** : Charge un fichier JSON depuis le disque et le retourne sous forme de dictionnaire Python, avec gestion des erreurs de lecture.

* **`sauvegarder_dict_en_json(dictionnaire, chemin_destination)`** : Sauvegarde un dictionnaire Python dans un fichier JSON formaté (indenté, UTF-8), en affichant le statut de l’opération.

* **`extraire_num(nom)`** : Extrait et retourne le nombre présent dans une chaîne de caractères (utile pour identifier des numéros de routeurs ou d’interfaces).

* **`initialiser_topologie(donnees_intent)`** : Analyse le fichier d’intention et initialise les structures globales `AS_CONFIG` et `EBGP_CONFIG` avec les plages IPv6, sous-réseaux et routeurs de chaque AS.

* **`creer_registre_dynamique(donnees_intent)`** : Génère un registre d’adressage IPv6 en attribuant dynamiquement des adresses aux interfaces et loopbacks des routeurs, en distinguant les liens intra-AS et inter-AS (eBGP).

* **`generer_plan_adressage(intention)`** : Construit le plan d’adressage IPv6 final à partir de l’intention et des configurations générées, prêt à être exporté ou utilisé par des générateurs de configuration.

#### generate_classes.py

* **`find_local_path()`** : Détermine et retourne le chemin absolu du dossier où se trouve le script.

* **`json_to_dict(in_file)`** : Lit un fichier JSON et le convertit en dictionnaire Python.

* **`generate_network_classes(int_file)`** : Lit le fichier d’intention réseau (fichier généré au préalable par `generer_plan_adressage.py` et génère l’ensemble des objets `Router` et `AS` nécessaires à partir de sa structure.

* **`generate_router(router_name, router_info)`** : Crée et retourne un objet `Router` à partir des informations décrivant un routeur (nom, ID, interfaces).

* **`generate_interface(interface_name, interface_info, as_obj)`** : Crée et configure un objet `Interface` à partir des informations d’interface (adresse, voisins, protocoles, coût).

* **`generate_AS(as_relations, intent)`** : Crée un objet `AS` et renseigne ses relations (peers, providers, clients) à partir du fichier d’intention.

#### write_config.py

* **`write_config(router, out_file, router_list, as_list)`** : Génère et écrit la configuration complète d’un routeur dans un fichier `.cfg`, en appelant toutes les autres fonctions d'écriture (vois ensuite)

* **`write_header(conf, router)`** : Écrit l’en-tête de la configuration Cisco du routeur (version, services, hostname, IPv6, paramètres globaux).

* **`write_end(conf, router)`** : Écrit la fin de la configuration, incluant la configuration du protocole de routage intra-AS (OSPF ou RIP) et les paramètres de lignes (console, vty).

* **`write_interfaces_config(conf, router)`** : Parcourt toutes les interfaces du routeur et appelle la fonction appropriée selon leur type (Loopback, FastEthernet, GigabitEthernet).

* **`write_loopback0(conf, interface)`** : Écrit la configuration d’une interface Loopback0, avec l’adressage IPv6 et l’activation du protocole de routage associé (OSPF ou RIP).

* **`write_FE(conf, interface)`** : Écrit la configuration d’une interface FastEthernet, incluant l’adressage IPv6, OSPF/RIP et les coûts OSPF éventuels.

* **`write_GE(conf, interface)`** : Écrit la configuration d’une interface GigabitEthernet, similaire à FastEthernet mais adaptée à ce type d’interface.

* **`write_bgp_config(conf, router, router_list)`** : Écrit la configuration BGP globale du routeur, configure les voisins iBGP via les loopbacks et les voisins eBGP sur les interfaces de bordure.

* **`write_ipv4_address_family(conf)`** : Écrit la section BGP `address-family ipv4`, sans activation de routes IPv4.

* **`write_ipv6_address_family(conf, router, router_list, as_list)`** : Écrit la section BGP `address-family ipv6`, configure les réseaux annoncés, les voisins iBGP/eBGP, le `next-hop-self` et les politiques de préférence locale selon les relations AS (client, peer, provider).
