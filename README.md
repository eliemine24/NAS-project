# Projet de NAS - 3TC : Automatisation de Services BGP/MPLS VPN

## Présentation du Projet
Ce projet, réalisé dans le cadre du cours NAS vise à automatiser le déploiement de services de connectivité avancés (VPN v4 et Internet) sur un cœur de réseau MPLS.

## Fonctionnalités Implémentées

### 1. Cœur de Réseau (Core)
* **Topologie :** Déploiement d'une architecture contenant des routeurs PE (Provider Edge) et P (Provider).
* **IGP (OSPF) :** Configuration automatique d'OSPFv2 pour le routage interne et la joignabilité des interfaces Loopback.
* **Transport MPLS :** Activation de LDP(Label Distribution Protocol) sur toutes les interfaces du cœur pour l'échange de labels.

### 2. Services BGP/MPLS VPN 
* **Architecture MP-BGP :** Mise en place de sessions iBGP entre les Loopbacks des routeurs PE pour la famille d'adresses VPNv4.
* **Isolation Client (VRF) :** Création et gestion de VRF pour assurer l'étanchéité totale entre les flux des différents clients.
* **Routage PE-CE :** Automatisation d'eBGP pour l'échange de routes entre le réseau de l'opérateur et les routeurs clients (CE).

### 3. Services Internet
Les routeurs PE (Provider Edge) sont capables de gérer simultanément :
* **Le trafic VPN MPLS** (étanche, via VRF) pour les clients.
* **Le trafic Internet IPv4 classique** via la table de routage globale.

## Utilisation 
Voici les étapes à suivre afin d'automatiser le routage de votre réseau :
1. Complétez le fichier d'intentions _pingu.json_ en indiquant les spécifications de votre réseau. 
2. Lancez le fichier _main.py_, ouvrez GNS3 et allumez vos routeurs.



