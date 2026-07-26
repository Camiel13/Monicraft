import os
import hashlib
import requests
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
