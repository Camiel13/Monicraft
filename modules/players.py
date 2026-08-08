import nbtlib
import asyncio
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Input, Label, Button, DataTable

class Players(Screen):
    AUTO_FOCUS="#mods-table"
    CSS = """
    Button {
        margin: 1;
        border: none;
        min-height: 3;
        min-width: 8;
        content-align: center middle;
    }
    """
    
    def compose(self):
        yield Header(name="Player Manager", show_clock=True)
        yield Button(label="<", id="back-button")
        yield DataTable(id="player-table")
    
    def on_mount(self):
        self.table = self.query_one("#player-table")
        self.table.add_columns("Name", "Health", "Hunger", "XP Level", "Position", "Dimension", "Gamemode")
        
        # Build the table
        self.run_worker(self.build_table, thread=False)
        
        for button in self.query(Button):
            button.can_focus = False
            
    async def build_table(self):
        if self.app.query_server and self.app.query_server.players.names:
            for player in self.app.query_server.players.names:
                player_uuid = self.app.api.get_player_uuid(name=player)
                nbt_data = self.app.api.get_player_data(uuid=player_uuid)
                self.add_player_to_table(nbt_data, player)    
        elif self.app.status_server and self.app.status_server.players.sample:
            for player in self.app.status_server.players.sample:
                nbt_data = self.app.api.get_player_data(uuid=player.id)
                self.add_player_to_table(nbt_data, player.name)
        else:
            await asyncio.sleep(5)
            self.build_table()
                
    def add_player_to_table(self, nbt_data, name: str):
        health = float(nbt_data["Health"])
        hunger = int(nbt_data['foodLevel'])
        xp_level = int(nbt_data['XpLevel'])
        pos = list(nbt_data['Pos'])
        dimension = nbt_data['Dimension'].split(":")[1].replace("_", " ").title()
        
        gamemode_number = int(nbt_data["playerGameType"])
        if gamemode_number == 0:
            gamemode = "survival"
        elif gamemode_number == 1:
            gamemode = "creative"
        elif gamemode_number == 2:
            gamemode = "adventure"
        elif gamemode_number == 3:
            gamemode = "spectator"
        
        self.table.add_row(
            name,
            str(health),
            str(hunger),
            str(xp_level),
            f"{pos[0]}, {pos[1]}, {pos[2]}",
            dimension,
            gamemode
        )
        
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "back-button":
            self.dismiss()