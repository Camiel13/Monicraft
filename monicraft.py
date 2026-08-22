from modules.api import API, DummyAPI
from modules.tui import TUI

class Monicraft:
    def __init__(self, is_dummy: bool):
        self.api = API() if not is_dummy else DummyAPI()
        self.tui = TUI(api_client=self.api)
                
    def start_dashboard(self):
        self.tui.run()