import os
import requests
from .utils import console
from dotenv import load_dotenv, set_key

class API:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("API_KEY")

        if "PANEL_ENDPOINT" not in os.environ:
            set_key(dotenv_path=".env",
                    key_to_set="PANEL_ENDPOINT",
                    value_to_set=console.input("[green] What is the url of your panel?[/] (e.g. panel.camilio13.com): "))
            
            load_dotenv(override=True)

        if "SERVER_ID" not in os.environ:
            set_key(dotenv_path=".env",
                    key_to_set="SERVER_ID",
                    value_to_set=console.input("[green] What is your server ID?[/] (e.g. panel.camilio13.com/server/[bold blue]937284kf[/]): "))

            load_dotenv(override=True)

        self.server_id = os.getenv("SERVER_ID")
        self.panel_endpoint = os.getenv("PANEL_ENDPOINT")
        self.url = f"https://{self.panel_endpoint}/api/client/servers/{self.server_id}"

    def get_websocket_creds(self):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        response = requests.get(url=f"{self.url}/websocket", headers=headers)

        data = response.json()["data"]
        token = data["token"]
        socket_url = data["socket"]
        
        return token, socket_url