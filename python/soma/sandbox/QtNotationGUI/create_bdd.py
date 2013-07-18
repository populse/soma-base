from catidb import CatiDB

class CreateBDD():
    _instance=None
        
    @staticmethod
    def get_instance():
        if CreateBDD._instance is None:
            CreateBDD._instance=CatiDB('user', 'Passe, le mot.')
            #CreateBDD._instance=CatiDB('admin', 'a')
            return CreateBDD._instance
        else:
            return CreateBDD._instance
