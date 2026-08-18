import io
import os
import nbtlib
import random
import hashlib
import httpx
import gzip
from dotenv import load_dotenv, set_key

class API:
    def __init__(self):
        load_dotenv()
        self.server_id = os.getenv("SERVER_ID")
        self.panel_endpoint = os.getenv("PANEL_ENDPOINT")
        self.api_key = os.getenv("API_KEY")
        self.uuid_cache = {} # will contain {"Steve": "owijfgwkjnefkjnrgoenrgijnekjnge"}
        
        self.init_client()
        
    @property
    def url(self):
        return f"https://{self.panel_endpoint}/api/client/servers/{self.server_id}"
    
    @property
    def is_configured(self):
        return bool(self.api_key and self.server_id and self.panel_endpoint)
    
    def init_client(self):
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        self.client = httpx.AsyncClient(headers=self.headers, timeout=3.0)

    async def get_websocket_creds(self):
        response = await self.client.get(
            url=f"{self.url}/websocket",
            
        )

        data = response.json()["data"]
        token = data["token"]
        socket_url = data["socket"]
        
        return token, socket_url
  
    async def get_mods(self):
        response = await self.client.get(
            url=f"{self.url}/files/list",
            params={"directory": "/mods"}
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["data"]

    """    
    async def get_versions(self):
        response = await self.client.get(
            url=f"{self.url}/startup",
        )
        
        if response.status_code == 200:
            items = response.json().get("data")
        else:
            self.notify(severity="error",
                        title="Failed to get version data!",
                        message=f"An error occured while getting the version data: {response.status_code}")
            return
    """
    
    async def get_server_address(self):
        response = await self.client.get(
            url=f"{self.url}/network/allocations",
        )

        if response.status_code == 200:
            data = response.json().get("data")
            alloc = next(item["attributes"] for item in data if item["attributes"]["is_default"])
            ip, port = alloc["ip"], alloc["port"]
            return ip, port
        else:
            self.app.notify(severity="error",
                        title="Failed to get server address!",
                        message=f"An error occured while getting the address: {response.status_code}, {response.text}")
            return None, None
    
    async def get_player_uuid(self, name: str) -> str:
        if name in self.uuid_cache.keys():
            return self.uuid_cache[name]
        
        response = await self.client.get(
            url=f"{self.url}/files/contents",
            params={"file": "usercache.json"}
        )
        
        if response.status_code == 200:
            usercache = response.json()
            # Cache all the users in usercache.json
            for item in usercache:
                self.uuid_cache[item["name"]] = item["uuid"]
            
            # Get the uuid for the given name
            uuid = next(item["uuid"] for item in usercache if item["name"] == name)
            return uuid
        else:
            self.app.notify(severity="error",
                        title="Failed to get user cache!",
                        message=f"An error occured while getting the user cache: {response.status_code}, {response.text}")
            return None

        
    async def get_player_data(self, name=None, uuid=None) -> object:
        if not uuid:            
            uuid = await self.get_player_uuid(name)
        
        response = await self.client.get(
            url=f"{self.url}/files/contents",
            params={"file": f"world/playerdata/{uuid}.dat"}
        )
        
        if response.status_code == 200:
            temp_file = io.BytesIO(response.content)
            with gzip.GzipFile(fileobj=temp_file) as gz:
                nbt_data = nbtlib.File.from_fileobj(gz)
            return nbt_data
        else:
            self.app.notify(severity="error",
                        title="Failed to get user data!",
                        message=f"An error occured while getting the user data: {response.status_code}, {response.text}")
            return None
        
    async def get_stats(self, uuid: str):
        response = await self.client.get(
            url=f"{self.url}/files/contents",
            params={"file": f"world/stats/{uuid}.json"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
        
        
class DummyAPI:
    def __init__(self):
        self.server_id = "131313"
        self.panel_endpoint = "panel.doesnotexist.com"
        self.api_key = "ptlc_On32iooISJSNnoj3oFJn5ONinfe3noJ5n34om55" # not a real api key, silly
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        
    @property
    def url(self):
        return f"https://{self.panel_endpoint}/api/client/servers/{self.server_id}"
    
    @property
    def is_configured(self):
        return True
    
    def get_dummy_player_data(self):
        dimensions = ["minecraft:overworld", "minecraft:the_nether", "minecraft:end"]
        nbt_data = {
            "Health": random.uniform(10.0, 20.0),
            "foodLevel": random.uniform(10.0, 20.0),
            "XpLevel": random.randint(0, 50),
            "Pos": [random.uniform(0.0, 10000.0) for i in range(3)],
            "Dimension": random.choice(dimensions),
            "playerGameType": 0
        }
        players = [
            "Steve",
            "Alex",
            "Noor",
            "Sunny",
            "Ari",
            "Zuri",
            "Makena",
            "Kai",
            "Efe"
        ]
        player_name = f"{random.choice(players)}{str(random.randint(11, 99))}"
        
        return player_name, nbt_data
        
    async def get_mods(self):
        return []