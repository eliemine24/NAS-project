# ==========================
# Écriture des configurations
# ==========================

from router import Router
from interface import Interface
from datetime import datetime
import ipaddress


def write_config(router, out_file, router_list, as_list, IPprotocol,rd_incrementer=0):
    """Écrit la configuration complète d'un routeur dans un fichier .cfg."""
    conf = open(out_file, 'w')
    write_header(conf, router, IPprotocol)
    if rd_incrementer != 0:
        write_vrf_definition(conf,router,as_list,rd_incrementer)
    write_interfaces_config(conf, router, as_list, IPprotocol,rd_incrementer)
    found = False
    for i in router.liste_int:
        if "EBGP" in i.protocol_list and not found:
            write_bgp_config(conf, router, router_list, IPprotocol)
            write_ipv4_address_family(conf, router, router_list, as_list, IPprotocol)
            write_ipv6_address_family(conf, router, router_list, as_list, IPprotocol)
            found = True

    write_end(conf, router, IPprotocol)
    conf.close()
    return out_file

def write_vrf_definition(conf,router,as_list,rd_incrementer):
    for a in as_list:
        if a.name == router.AS_name:
            for key in a.vpn_clients.keys():
                conf.write(f"""vrf definition {key}\n""")
                conf.write(f""" rd 100:{rd_incrementer}\n""")
                rd_incrementer += 10
                conf.write(f""" route-target export {a.vpn_clients[key]["RT"]}\n""")
                conf.write(f""" route-target import {a.vpn_clients[key]["RT"]}\n""")
                conf.write(""" !\n""")
                conf.write(""" address-family ipv4\n""")
                conf.write(""" exit-address-family\n""")
                conf.write("""!\n""")


def write_header(conf, router, IPprotocol):
    """Écrit l'en-tête de la configuration du routeur."""
    # Récupère la date de modification sous le bon format
    date = datetime.now().strftime('%I:%M:%S UTC %a %b %d %Y')
    conf.write(f"""!
! Last configuration change at {date}
!
version 15.2
service timestamps debug datetime msec
service timestamps log datetime msec
!
hostname {router.name}
!
boot-start-marker
boot-end-marker
!
!
!
no aaa new-model
no ip icmp rate-limit unreachable
ip cef
!
!
!
!
!
!
no ip domain lookup
{"no "if IPprotocol == 4 else ""}ipv6 unicast-routing
{"no "if IPprotocol == 4 else ""}ipv6 cef
!
!
multilink bundle-name authenticated
!
!
!
!
!
!
!
!
!
ip tcp synwait-time 5
! 
!
!
!
!
!
!
!
!
!
!
!
""")

def write_end(conf, router, IPprotocol):
    protocol = "OSPF"
    # Vérifie si le protocole de l'AS est RIP, sinon garde OSPF
    for int in router.liste_int:
        if "RIP" in int.protocol_list:
            protocol = "RIP"
    # Configurations RIP
    if protocol == "RIP":
        conf.write(f"""{"ipv6 " if IPprotocol == 6 else ""}router rip maison
 redistribute connected\n""")
    # Configurations OSPF
    else: 
        conf.write(f"""{"ipv6 " if IPprotocol == 6 else ""}router ospf 10
 router-id {router.ID}\n""")
    conf.write("""!
!
!
!
control-plane
!
!
line con 0
 exec-timeout 0 0
 privilege level 15
 logging synchronous
 stopbits 1
line aux 0
 exec-timeout 0 0
 privilege level 15
 logging synchronous
 stopbits 1
line vty 0 4
 login
!
!
end\n""")

# =============================
# ======== Interfaces =========
# =============================

def write_interfaces_config(conf, router,as_list, IPprotocol,rd_incrementer):
    """Écrit la configuration de toutes les interfaces du routeur."""
    for interface in router.liste_int:
        if interface.name == 'LOOPBACK0':
            write_loopback0(conf, interface, IPprotocol)
        elif 'G' in interface.name :
            write_GE(conf, interface,as_list, IPprotocol,rd_incrementer)
        else:
            write_FE(conf, interface,as_list, IPprotocol,rd_incrementer)


def write_loopback0(conf, interface, IPprotocol):
    """Écrit la configuration d'une interface loopback0."""
    conf.write(f"""interface {interface.name}
 no shutdown\n""")
    if IPprotocol == 6:
        conf.write(f""" no ip address
 ipv6 address {interface.address}
 ipv6 enable\n""")
    else:
        mask = str(ipaddress.IPv4Interface(interface.address).netmask)
        conf.write(f""" ip address {interface.address.split('/')[0]+" "+mask}\n""")
    if "OSPF" in interface.protocol_list :
        conf.write(f""" {"ipv6 " if IPprotocol == 6 else "ip "}ospf 10 area 0\n""")
    elif "RIP" in interface.protocol_list:
        conf.write(f""" {"ipv6 " if IPprotocol == 6 else "ip "}rip maison enable\n""")
    conf.write("""!\n""")


def write_FE(conf, interface,as_list, IPprotocol,rd_incrementer):
    """Écrit la configuration d'une interface FastEthernet."""
    conf.write(f"""interface {interface.name}
 negotiation auto
 duplex full
 no shutdown
""")
    if IPprotocol == 6:
        conf.write(f""" no ip address 
 ipv6 enable
 ipv6 address {interface.address}\n""")
    else:
        mask = str(ipaddress.IPv4Interface(interface.address).netmask)
        conf.write(f""" ip address {interface.address.split('/')[0]+" "+mask}\n""")
    # Configs OSPF
    if "OSPF" in interface.protocol_list :
        conf.write(f""" {"ipv6 " if IPprotocol == 6 else "ip "}ospf 10 area 0\n""")
        conf.write(""" mpls ip\n""")
        # Gère les couts si il y en a
        if interface.cost != "":
            conf.write(f""" {"ipv6 " if IPprotocol == 6 else "ip "}ospf cost {interface.cost}\n""")
    # Configs RIP
    elif "RIP" in interface.protocol_list:
        conf.write(f""" {"ipv6 " if IPprotocol == 6 else "ip "}rip maison enable\n""")
    conf.write(f"""!\n""")


def write_GE(conf, interface,as_list, IPprotocol,rd_incrementer):
    """Écrit la configuration d'une interface GigaEthernet."""
    conf.write(f"""interface {interface.name}
 negotiation auto
 no shutdown
""")
    if IPprotocol == 6:

        conf.write(f""" no ip address 
 ipv6 enable
 ipv6 address {interface.address}\n""")
        
    else:
        # if rd_incrementer != 0:
        #     for a in as_list:
        #         if a == interface.AS_name
        mask = str(ipaddress.IPv4Interface(interface.address).netmask)
        conf.write(f""" ip address {interface.address.split('/')[0]+" "+mask}\n""")

    # Configs OSPF
    if "OSPF" in interface.protocol_list :
        conf.write(f""" {"ipv6 " if IPprotocol == 6 else "ip "}ospf 10 area 0\n""")
        conf.write(""" mpls ip\n""")
        # Gère les couts si il y en a
        if interface.cost != "":
            conf.write(f""" {"ipv6 " if IPprotocol == 6 else "ip "}ospf cost {interface.cost}\n""")
    # Configs RIP
    elif "RIP" in interface.protocol_list:
        conf.write(f""" {"ipv6 " if IPprotocol == 6 else "ip "}rip maison enable\n""")
    conf.write(f"""!\n""")


# =============================
# === Protocoles de routage ===
# =============================

def write_bgp_config(conf, router,router_list, IPprotocol):
    """Écrit la configuration BGP du routeur."""
    conf.write(f"""!
router bgp {router.AS_name}
 bgp router-id {router.ID}
 bgp log-neighbor-changes{"\n no bgp default ipv4-unicast" if IPprotocol == 6 else ""}
""")
    for interface in router.liste_int:
        if interface.name == "LOOPBACK0":
            conf.write("""""")
            for neighbor in interface.neighbors_address:
                conf.write(f""" neighbor {neighbor.split('/', 1)[0]} remote-as {router.AS_name}
 neighbor {neighbor.split('/', 1)[0]} update-source {interface.name}
""")
        else:
            for protocol in interface.protocol_list:
                
                if protocol == "EBGP":
                    
                    #va chercher l'as-name du routeur voisin
                    for router_temp in router_list:
                        for temp_interface in router_temp.liste_int:
                            if temp_interface.address in interface.neighbors_address:
                                conf.write(f""" neighbor {temp_interface.address.split('/', 1)[0]} remote-as {router_temp.AS_name}
""")
    conf.write(f""" !\n""")

def write_ipv4_address_family(conf, router, router_list, as_list, IPprotocol):
    """Écrit la configuration address-family IPv4."""
    conf.write(""" address-family ipv4\n""")
    if IPprotocol == 4:
        #on va chercher toutes les interfaces et configurer BGP sur chacun d'entre eux: EBGP pour les interfaces en bordure et IBGP pour les loopbacks
        network_done = False
        for interface in router.liste_int:

            #si on a du EBGP on va network les réseaux de son AS qui ne sont pas des loopbacks
            if "EBGP" in interface.protocol_list:
                #si on a pas encore network les réseaux de l'AS, on le fait une fois
                if not network_done:
                    #on initialise une liste pour stocker les réseaux qui existent dans l'AS
                    list_as_networks = []
                    #on cherche dans tout les routeurs du réseau toutes les interfaces de chaque routeur afin de trouver tous les réseaux de l'AS
                    for routers in router_list:
                        for interfaces in routers.liste_int:
                            #on formate l'adresse pour récupérer seulement son réseau
                            réseau_interface_base = ipaddress.IPv4Interface(interfaces.address).network

                            #si le réseau n'a pas déjà été vu et qu'il appartient à notre AS et que ce n'est pas un réseau de loopback alors on le network.
                            if réseau_interface_base not in list_as_networks and router.AS_name == routers.AS_name and interfaces.name != "LOOPBACK0":
                                list_as_networks.append(réseau_interface_base)
                                mask = str(ipaddress.IPv4Interface(list_as_networks[-1]).netmask)
                                conf.write(f"""  network {str(list_as_networks[-1]).split('/')[0] + " mask " + mask}\n""")
                    network_done = True
                #si on a du EBGP on configure les neighbors de l'interface et on active next-hop-self
                for neighbor in interface.neighbors_address:
                    conf.write(f"""  neighbor {neighbor.split('/', 1)[0]} activate\n""")
                    conf.write(f"""  neighbor {neighbor.split('/', 1)[0]} next-hop-self\n""")

            #sinon si on a une interface de loopback alors on configure l'IBGP avec toutes les autres adresses de loopback
            elif interface.name == "LOOPBACK0":
                for neighbor in interface.neighbors_address:
                    conf.write(f"""  neighbor {neighbor.split('/', 1)[0]} activate\n""")
                    
        # Write local preference based on relationship type (client=200, peer=90, provider=80)
        for inter in router.liste_int:
            if len(inter.neighbors_address) == 0:
                continue    # sortir si ya pas de voisins
            
            voisin = inter.neighbors_address[0] # un seul voisin par interface
            if "EBGP" not in inter.protocol_list:
                continue
            routeur_voisin = None
            
            # Find the neighbor router by its interface address
            for r in router_list:
                for i in r.liste_int:
                    if i.address.split('/', 1)[0] == voisin.split('/', 1)[0]:   # enlever le mask bien vu
                        routeur_voisin = r
                        #print(routeur_voisin)
                        break
                if routeur_voisin:
                    break   # ne pas continuer si on a trouvé le router voisin
            
            if not routeur_voisin:
                continue
            
            # Find the AS of the neighbor router
            as_router_voisin = None
            for current_as in as_list:
                if current_as.name == routeur_voisin.AS_name:
                    as_router_voisin = current_as
                    break
            
            if not as_router_voisin:
                continue
            
            # Check relationship: is current router a PROVIDER, PEER, or CLIENT of neighbor AS?
            if router.AS_name in as_router_voisin.providers:
                conf.write(f"""  neighbor {voisin.split('/', 1)[0]} route-map client in\n""")
            elif router.AS_name in as_router_voisin.peers:
                conf.write(f"""  neighbor {voisin.split('/', 1)[0]} route-map peer in\n""")
            elif router.AS_name in as_router_voisin.clients:
                conf.write(f"""  neighbor {voisin.split('/', 1)[0]} route-map provider in\n""")
    conf.write(""" exit-address-family
!
ip forward-protocol nd
!
!
no ip http server
no ip http secure-server
!
!
route-map client permit 10
 set local-preference 200
!
route-map provider permit 10
 set local-preference 80
!
route-map peer permit 10
 set local-preference 90
!
!\n""")


def write_ipv6_address_family(conf, router, router_list, as_list, IPprotocol):
    """Écrit la configuration address-family IPv6."""
    if IPprotocol == 6:
    
        conf.write(""" address-family ipv6\n""")
    
        #on va chercher toutes les interfaces et configurer BGP sur chacun d'entre eux: EBGP pour les interfaces en bordure et IBGP pour les loopbacks
        
        for interface in router.liste_int:

            #si on a du EBGP on va network les réseaux de son AS qui ne sont pas des loopbacks
            if "EBGP" in interface.protocol_list:

                #on initialise une liste pour stocker les réseaux qui existent dans l'AS
                list_as_networks = []
                #on cherche dans tout les routeurs du réseau toutes les interfaces de chaque routeur afin de trouver tous les réseaux de l'AS
                for routers in router_list:
                    for interfaces in routers.liste_int:
                        #on formate l'adresse pour récupérer seulement son réseau
                        réseau_interface_base = ipaddress.IPv6Interface(interfaces.address).network

                        #si le réseau n'a pas déjà été vu et qu'il appartient à notre AS et que ce n'est pas un réseau de loopback alors on le network.
                        if réseau_interface_base not in list_as_networks and router.AS_name == routers.AS_name and interfaces.name != "LOOPBACK0":
                            list_as_networks.append(réseau_interface_base)
                            conf.write(f"""  network {list_as_networks[-1]}\n""")

                #si on a du EBGP on configure les neighbors de l'interface et on active next-hop-self
                for neighbor in interface.neighbors_address:
                    conf.write(f"""  neighbor {neighbor.split('/', 1)[0]} activate\n""")
                    conf.write(f"""  neighbor {neighbor.split('/', 1)[0]} next-hop-self\n""")

            #sinon si on a une interface de loopback alors on configure l'IBGP avec toutes les autres adresses de loopback
            # elif interface.name == "LOOPBACK0":
            #     for neighbor in interface.neighbors_address:
            #         conf.write(f"""  neighbor {neighbor.split('/', 1)[0]} activate\n""")
                    
        # Write local preference based on relationship type (client=200, peer=90, provider=80)
        for inter in router.liste_int:
            if len(inter.neighbors_address) == 0:
                continue    # sortir si ya pas de voisins
            
            voisin = inter.neighbors_address[0] # un seul voisin par interface
            if "EBGP" not in inter.protocol_list:
                continue
            routeur_voisin = None
            
            # Find the neighbor router by its interface address
            for r in router_list:
                for i in r.liste_int:
                    if i.address.split('/', 1)[0] == voisin.split('/', 1)[0]:   # enlever le mask bien vu
                        routeur_voisin = r
                        #print(routeur_voisin)
                        break
                if routeur_voisin:
                    break   # ne pas continuer si on a trouvé le router voisin
            
            if not routeur_voisin:
                continue
            
            # Find the AS of the neighbor router
            as_router_voisin = None
            for current_as in as_list:
                if current_as.name == routeur_voisin.AS_name:
                    as_router_voisin = current_as
                    break
            
            if not as_router_voisin:
                continue
            
            # Check relationship: is current router a PROVIDER, PEER, or CLIENT of neighbor AS?
            if router.AS_name in as_router_voisin.providers:
                conf.write(f"""  neighbor {voisin.split('/', 1)[0]} route-map client in\n""")
            elif router.AS_name in as_router_voisin.peers:
                conf.write(f"""  neighbor {voisin.split('/', 1)[0]} route-map peer in\n""")
            elif router.AS_name in as_router_voisin.clients:
                conf.write(f"""  neighbor {voisin.split('/', 1)[0]} route-map provider in\n""")     
        conf.write(""" exit-address-family
!
ip forward-protocol nd
!
!
no ip http server
no ip http secure-server
!
!
route-map client permit 10
 set local-preference 200
!
route-map provider permit 10
 set local-preference 80
!
route-map peer permit 10
 set local-preference 90
!
!\n""")