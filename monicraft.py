import asyncio
from modules.api import API
from modules.tui import TUI
from modules.utils import console
from modules.settings import Settings

class Monicraft:
    def __init__(self):
        self.api = API()
        self.tui = TUI(api_client=self.api)
                
    def start_dashboard(self):
        self.tui.run()