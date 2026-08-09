import io
import os
import nbtlib
import hashlib
import requests
import gzip
from .utils import console
from dotenv import load_dotenv, set_key

class API:
    def __init__(self):
        load_dotenv()
        self.server_id = os.getenv("SERVER_ID")
        self.panel_endpoint = os.getenv("PANEL_ENDPOINT")
        self.api_key = os.getenv("API_KEY")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        
    @property
    def url(self):
        return f"https://{self.panel_endpoint}/api/client/servers/{self.server_id}"

    def get_websocket_creds(self):
        response = requests.get(url=f"{self.url}/websocket", headers=self.headers)

        data = response.json()["data"]
        token = data["token"]
        socket_url = data["socket"]
        
        return token, socket_url
  
    def get_mods(self):
        response = requests.get(
            url=f"{self.url}/files/list",
            headers=self.headers,
            params={"directory": "/mods"}
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["data"]

    """    
    def get_versions(self):
        response = requests.get(
            url=f"{self.url}/startup",
            headers=self.headers,
        )
        
        if response.status_code == 200:
            items = response.json().get("data")
        else:
            self.notify(severity="error",
                        title="Failed to get version data!",
                        message=f"An error occured while getting the version data: {response.status_code}")
            return
    """
    
    def get_server_address(self):
        response = requests.get(
            url=f"{self.url}/network/allocations",
            headers = self.headers
        )

        if response.status_code == 200:
            data = response.json().get("data")
            alloc = next(item["attributes"] for item in data if item["attributes"]["is_default"])
            ip, port = alloc["ip"], alloc["port"]
            return ip, port
        else:
            self.notify(severity="error",
                        title="Failed to get server address!",
                        message=f"An error occured while getting the address: {response.status_code}, {response.text}")
            return None, None
    
    def get_player_uuid(self, name: str) -> str:
        response = requests.get(
            url=f"{self.url}/files/contents",
            headers=self.headers,
            params={"file": "usercache.json"}
        )
        
        if response.status_code == 200:
            usercache = response.json()
            uuid = next(item["uuid"] for item in usercache if item["name"] == name)
            return uuid
        else:
            self.notify(severity="error",
                        title="Failed to get user cache!",
                        message=f"An error occured while getting the user cache: {response.status_code}, {response.text}")
            return None

        
    def get_player_data(self, name=None, uuid=None) -> object:
        if not uuid:
            uuid = self.get_player_uuid(name)
        
        response = requests.get(
            url=f"{self.url}/files/contents",
            headers=self.headers,
            params={"file": f"world/playerdata/{uuid}.dat"}
        )
        
        if response.status_code == 200:
            temp_file = io.BytesIO(response.content)
            with gzip.GzipFile(fileobj=temp_file) as gz:
                nbt_data = nbtlib.File.from_fileobj(gz)
            return nbt_data
        else:
            self.notify(severity="error",
                        title="Failed to get user data!",
                        message=f"An error occured while getting the user data: {response.status_code}, {response.text}")
            return None