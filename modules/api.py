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
        self.player_cache = {} # will contain {"owijfgwkjnefkjnrgoenrgijnekjnge": Player()}
        
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
        
    async def init_caches(self):
        usercache = await self.get_usercache()
        await self.cache_uuids(usercache=usercache)
        
        for name, uuid in self.uuid_cache.items():
            self.player_cache[uuid] = Player(name=name, uuid=uuid)
            
    async def test_connection(self) -> tuple[bool, str]:
        if not self.is_configured:
            return False, "Credentials not filled in."
        try:
            response = await self.client.get(f"{self.url}/websocket")
            if response.status_code == 200:
                return True, "A connection was successfully established."
            elif response.status_code == 401:
                return False, "You haven't filled in your server's credentials yet, you can do this by simply filling them in in the settings menu."
            elif response.status_code == 403:
                return False, "You have insufficient permissions to access the API."
            elif response.status_code == 404:
                return False, "Server ID was not found, double check it in your settings."
            else:
                return False, f"Server returned error code: {response.status_code}."
        except Exception as e:
            return False, f"Could not reach server panel: {e}."
 

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
                            message=f"An error occurred while getting the address: {response.status_code}, {response.text}"
        )
            return None, None
        
    async def get_usercache(self):
        response = await self.client.get(
            url=f"{self.url}/files/contents",
            params={"file": "usercache.json"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            self.app.notify(severity="error",
                            title="Failed to get user cache!",
                            message=f"An error occurred while getting the user cache: {response.status_code}, {response.text}"
            )
            return None
        
    async def cache_uuids(self, usercache):
        if not usercache:
            return
        
        # Cache all the users in usercache.json
        for item in usercache:
                self.uuid_cache[item["name"]] = item["uuid"]
                
    async def get_player_uuid(self, name: str) -> str:
        if name in self.uuid_cache.keys():
            return self.uuid_cache[name]
        
        usercache = await self.get_usercache()
        await self.cache_uuids(usercache=usercache)
        
        # Get the uuid for the given name
        uuid = self.uuid_cache.get(name)
        return uuid
        
    async def get_player_data(self, uuid=None, name=None) -> object:        
        if not uuid and not name:
            return
        
        if not uuid:
            uuid = await self.get_player_uuid(name=name)

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
                            message=f"An error occurred while getting the user data: {response.status_code}, {response.text}"
            )
            return None
        
    async def get_player_stats(self, uuid: str):
        response = await self.client.get(
            url=f"{self.url}/files/contents",
            params={"file": f"world/stats/{uuid}.json"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            self.app.notify(severity="error",
                            title="Failed to get user stats!",
                            message=f"An error occurred while getting the user stats: {response.status_code}, {response.text}"
            )
            return None
        
    async def get_recent_players(self):
        usercache = await self.get_usercache()
        await self.cache_uuids(usercache=usercache)
        
        data = [{"name": item["name"], "uuid": item["uuid"]} for item in usercache]
        return data     
        
class DummyAPI:
    def __init__(self):
        self.server_id = "131313"
        self.panel_endpoint = "panel.doesnotexist.com"
        self.api_key = "ptlc_On32iooISJSNnoj3oFJn5ONinfe3noJ5n34om55" # not a real api key, silly
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        self.player_cache = {}
        
    async def init_caches(self):
        pass
        
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
    
    def get_dummy_stats(self):
        dummy_player_stats = {
            "stats": {
                "minecraft:custom": {
                    "minecraft:play_time": 72000,
                    "minecraft:walk_one_cm": 250000,
                    "minecraft:sprint_one_cm": 120000,
                    "minecraft:jump": 340,
                    "minecraft:damage_dealt": 1500,
                    "minecraft:damage_taken": 450,
                    "minecraft:deaths": 3,
                    "minecraft:mob_kills": 48
                },
                "minecraft:killed": {
                    "minecraft:zombie": 24,
                    "minecraft:skeleton": 12,
                    "minecraft:creeper": 7,
                    "minecraft:spider": 5
                },
                "minecraft:mined": {
                    "minecraft:stone": 150,
                    "minecraft:iron_ore": 35,
                    "minecraft:coal_ore": 60,
                    "minecraft:diamond_ore": 8
                },
                "minecraft:crafted": {
                    "minecraft:torch": 64,
                    "minecraft:iron_pickaxe": 2,
                    "minecraft:crafting_table": 1
                },
                "minecraft:used": {
                    "minecraft:iron_pickaxe": 180,
                    "minecraft:torch": 45
                },
                "minecraft:broken": {
                    "minecraft:stone_pickaxe": 2
                },
                "minecraft:picked_up": {
                    "minecraft:cobblestone": 150,
                    "minecraft:raw_iron": 35
                },
                "minecraft:dropped": {
                    "minecraft:dirt": 20
                }
            },
            "DataVersion": 3465
        }
        return dummy_player_stats
    
    async def test_connection(self):
        return True, "Successfully connected to dummy server."
    
    
class Player:
    def __init__(self, name: str, uuid:str):
        self.name = name
        self.uuid = uuid
        self.nbt_data = None
        self.online = None