import nbtlib
import asyncio
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Input, Label, Button, DataTable
from .popup import GamemodePopUp, MessagePopUp, KickBanPopUp, StatsPopUp

class Players(Screen):
    AUTO_FOCUS="#player-table"
    CSS = """
    Button {
        margin: 1;
        border: none;
        min-height: 3;
        min-width: 8;
        content-align: center middle;
    }
    #player-table {
        width: 100%;
        height: 1fr;
    }
    #header-buttons {
        height: auto;
        dock: top;
    }
    #footer {
        dock: bottom;
        height: auto;
    }
    """
    
    def compose(self):
        yield Header(name="Player Manager", show_clock=True)
        with Horizontal(id="header-buttons"):
            yield Button(label="<", id="back-button")
            yield Button(label="↻", id="refresh-button")
            yield Button(label="Include Offline Players", id="include-offline-button")
        yield DataTable(id="player-table")
        with Horizontal(id="footer"):
            yield Button(label="Stats", id="stats-button")
            yield Button(label="Message", id="message-button")
            yield Button(label="Kick", id="kick-button")
            yield Button(label="Ban", id="ban-button")
            yield Button(label="Gamemode", id="gamemode-button")
            
    
    def on_mount(self):
        self.table = self.query_one("#player-table")
        self.table.add_columns("Name", "Health", "Hunger", "XP Level", "Position", "Dimension", "Gamemode")
        
        # Build the table
        self.run_worker(self.data_loop, thread=False)
        
        for button in self.query(Button):
            button.can_focus = False
            
    async def build_table(self):
        self.table.clear()
        
        if self.app.dummy_server:
            player_name, nbt_data = self.app.api.get_dummy_player_data()
            self.add_player_to_table(nbt_data=nbt_data, name=player_name)
            return
            
        if self.app.query_server and self.app.query_server.players.list:
            for player in self.app.query_server.players.list:
                try: 
                    player_uuid = await self.app.api.get_player_uuid(name=player)
                    nbt_data = await self.app.api.get_player_data(uuid=player_uuid)
                    self.add_player_to_table(nbt_data, player)
                except Exception as e:
                    self.notify(severity="error",
                                title="Failed to get players through query!",
                                message=f"Failed to get players through query: {e}.")
        elif self.app.status_server and self.app.status_server.players.sample:
            try:
                for player in self.app.status_server.players.sample:
                    nbt_data = await self.app.api.get_player_data(uuid=player.id)
                    self.add_player_to_table(nbt_data, player.name)
            except Exception as e:
                self.notify(severity="error",
                            title="Failed to get players through ping!",
                            message=f"Failed to get players through ping: {e}.")

    async def data_loop(self):
        while True:
            await self.build_table()
            await asyncio.sleep(10)
                
    def add_player_to_table(self, nbt_data, name: str):
        health = float(nbt_data["Health"])
        hunger = int(nbt_data['foodLevel'])
        xp_level = int(nbt_data['XpLevel'])
        pos = list(nbt_data['Pos'])
        dimension = nbt_data['Dimension'].split(":")[1].replace("_", " ").title()
        
        gamemode_number = int(nbt_data["playerGameType"])
        if gamemode_number == 0:
            gamemode = "Survival"
        elif gamemode_number == 1:
            gamemode = "Creative"
        elif gamemode_number == 2:
            gamemode = "Adventure"
        elif gamemode_number == 3:
            gamemode = "Spectator"
        
        self.table.add_row(
            name,
            str(round(health, 1)),
            str(round(hunger, 1)),
            str(xp_level),
            f"{int(pos[0])}, {int(pos[1])}, {int(pos[2])}",
            dimension,
            gamemode
        )
        
    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "back-button":
            self.dismiss()
            
        if event.button.id in ["stats-button", "message-button", "kick-button", "ban-button", "gamemode-button"]:
            if self.table.row_count > 0:
                selected_row = self.table.cursor_row
                row_data = self.table.get_row_at(selected_row)
                
                player_name = row_data[0]
                gamemode = row_data[6]
                
                if event.button.id == "stats-button":
                    self.app.push_screen(StatsPopUp(player_name="Camilio13"))
                elif event.button.id == "message-button":
                    self.app.push_screen(MessagePopUp(player_name=player_name))
                elif event.button.id == "kick-button":
                    self.app.push_screen(KickBanPopUp(player_name=player_name, action="kick"))
                elif event.button.id == "ban-button":
                    self.app.push_screen(KickBanPopUp(player_name=player_name, action="ban"))
                elif event.button.id == "gamemode-button":
                    async def on_popup_close(changed: bool):
                        if changed:
                            await self.refresh_data()
                    
                    self.app.push_screen(GamemodePopUp(player_name=player_name, current_gamemode=gamemode), on_popup_close)
                
        if event.button.id == "refresh-button":
            await self.refresh_data()
            
        if event.button.id == "include-offline-button":
            pass # TODO: ADD LOGIC TO INCLUDE OFFLINE PLAYERS
            
    async def refresh_data(self):
        await self.app.send_command("/save-all")
        await asyncio.sleep(0.5)
        await self.app.update_server_status()
        await self.build_table()