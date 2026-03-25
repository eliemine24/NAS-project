# =======================
# === DRAG & DROP BOT ===
# =======================

# place les fichier de config dans l'arborescence du projet gsn
# on considère que le script se situe dans un dossier parallèle 
# ./
#   code/
#        scripts, intent_file, etc
#   projet_gns/
#              config_files, etc

from generate_classes import find_local_path, json_to_dict
from datetime import datetime
import os
import shutil #librairie pour la gestion de fichiers




# Récupérer les noms imbuvables des dossier de config
def find_repository_names(routers_list, project_name, general_path):
    repo_names = {}
    # Path: ~local/ + projet_test/ + projet_test.gns3
    gns3_file = os.path.join(general_path, project_name, f"{project_name}.gns3")
    project_dict = json_to_dict(gns3_file)
    
    nodes = project_dict.get("topology", {}).get("nodes", [])
    
    for router in routers_list:
        for node in nodes:
            if node.get("name") == router.name:
                repo_name = node.get("node_id")
                if repo_name:
                    repo_names[router.name] = [repo_name, node.get("properties").get("dynamips_id")]
                break
    return repo_names

# Déplacer un fichier fichier file depuis l'emplacement du script jusqu'à l'emplacement final
def place_file(file, project_path, gns_path, dest_router_folder, final_file, project_name):
    
    #On crée des chemins proprement pour ne pas avoir de propblèmes si on passe de Linux à Windows
    source = os.path.join(project_path, file)
    destination = os.path.join(gns_path,project_name, "project-files","dynamips", dest_router_folder, "configs", final_file)
    shutil.move(source, destination)


# Lit le dictionnaire de find_repository_names et puis place les bons fichiers de config dans le bons dossiers

def drag_and_drop(project_path, gns_path, project_name,  repo_names) :

    for router_name, dest_router_folder in repo_names.items() :
        
        file = router_name+".cfg"
        final_file = "i" + str(dest_router_folder[1]) + "_startup-config" +".cfg"
        place_file(file, project_path, gns_path, dest_router_folder[0], final_file, project_name)