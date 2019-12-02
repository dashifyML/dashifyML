
class ServerStorage:
    def __init__(self):
        self.storage_dict = dict()


    def insert(self, session_id: str, key: str, data: object):
        if session_id not in self.storage_dict:
            self.storage_dict[session_id] = {}
        self.storage_dict[session_id][key] = data

    def get(self, session_id: str, key: str):
        if session_id not in self.storage_dict or key not in self.storage_dict[session_id]:
            return None
        else:
            return self.storage_dict[session_id][key]


server_storage = ServerStorage()

