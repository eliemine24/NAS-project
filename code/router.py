

class Router():
    """
    Docstring for router
    """
    def __init__(self, name, ID, nb_interfaces):
        self.name = name
        self.ID = ID
        self.nb_int = nb_interfaces
        self.liste_int=[]
        self.AS_name = ""

    def __str__(self):
        return f"router name : {self.name} (AS {self.AS_name}) | router ID : {self.ID} | interfaces : {self.nb_int}"