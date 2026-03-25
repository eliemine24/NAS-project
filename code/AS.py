


class AS():
    
    def __init__(self, ASname):
        self.name = ASname
        self.peers = []
        self.clients = []
        self.providers = []
    
    def __str__(self):
        return f" AS name : {self.name} | peers : {self.peers} | clients : {self.clients} | providers : {self.providers}"