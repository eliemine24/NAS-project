

class Interface():
    """
    Docstring for interface
    """

    def __init__(self, name):
        self.name = name
        self.address = ""
        self.neighbors_address = []
        self.protocol_list = []
        self.cost = ""

    def __str__(self):
        print(f"interface name : {self.name} \ninterface address : {self.address} \ninterface protocol : {self.protocol}")