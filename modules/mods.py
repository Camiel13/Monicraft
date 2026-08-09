import os
from concurrent.futures import ThreadPoolExecutor
from rich.markup import escape
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Button, DataTable

class Mods(Screen):
    AUTO_FOCUS="#mods-table"
    CSS = """
    Button {
        margin: 1;
        border: none;
        min-height: 3;
        min-width: 8;
        content-align: center middle;
    }
    #mods-table {
        width: 100%;
        height: 1fr;
    }
    """
    
    @property
    def api(self):
        return self.app.api
    
    def compose(self):
        yield Header(name="Mods", show_clock=True)
        yield Button(label="<", id="back-button")
        yield DataTable(id="mods-table")
        
    def on_mount(self):
        self.table = self.query_one("#mods-table")
        self.table.add_columns("Mod", "Size (MB)", "Last changed on")
        self.build_table()
        
        for button in self.query(Button):
            button.can_focus = False
    
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "back-button":
            self.dismiss()
            
    def build_table(self):
        mods_data = self.api.get_mods()
        
        for mod in mods_data:
            attr = mod["attributes"]
            name = attr["name"]
            size = attr["size"] / (1024 ** 2)
            last_changed = attr["modified_at"][:10]
            self.table.add_row(name, size, last_changed)
