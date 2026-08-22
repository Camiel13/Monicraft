import nbtlib
import asyncio
from .utils import format_tag
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Input, Label, Button, DataTable
from .popup import GamemodePopUp, MessagePopUp, KickBanPopUp, StatsPopUp

class Players(Screen):
    AUTO_FOCUS="#player-table"
    CSS = """
    Header {
       height: 3;
       align: center middle;
       background: darkgreen;
    }    
    
    Button {
        margin: 1;
        border: none;
        min-height: 3;
        min-width: 8;
        content-align: center middle;
    }
    #back-button, #refresh-button {
        width: 8;
        min-width: 8;
    }
    #include-offline-button.on {
        background: green;
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
        yield Header(name="Player Manager", show_clock=True, icon="")
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
            
    
    async def on_mount(self):
        # Create the toggle and cache for offline players
        self.offline_included = False
        self.offline_player_cache = {}
        
        # Making the table with the right columns
        self.table = self.query_one("#player-table", DataTable)
        self.table.add_columns("Name", "Status", "Health", "Hunger", "XP Level", "Position", "Dimension", "Gamemode")
        
        # Build the table
        self.run_worker(self.data_loop, thread=False)
        
        # Make the buttons not focusable
        for button in self.query(Button):
            button.can_focus = False
    
    
    def get_online_player_names(self):
        if self.app.query_server and self.app.query_server.players.list:
            return set(self.app.query_server.players.list)
        elif self.app.status_server and self.app.status_server.players.sample:
            return {player.name for player in self.app.status_server.players.sample}
        return set()
            
    async def build_table(self):
        previous_row = self.table.cursor_row if self.table.row_count > 0 else 0
        
        if self.app.dummy_server:
            player_name, nbt_data = self.app.api.get_dummy_player_data()
            self.table.clear()
            self.add_player_to_table(nbt_data=nbt_data, name=player_name, is_online=True)
            return
            
        try:
            # Get all the online players as a set and get all the players that ever played
            online_names = self.get_online_player_names()
            all_players = list(self.app.api.player_cache.values())   
            
            # Find out what players needs to be updated
            players_to_update = [] # Will contain player objects
            for player in all_players:
                player.online = player.name in online_names
                
                if player.online or (self.offline_included and player.nbt_data is None):
                    players_to_update.append(player)
            
            # Update the nbt data when needed 
            if players_to_update:
                if len(players_to_update) > 230:
                    raise Exception("Too many players need to be updated, would exceed rate limits.")
                
                tasks = [self.app.api.get_player_data(name=p.name, uuid=p.uuid) for p in players_to_update]
                nbt_data_list = await asyncio.gather(*tasks)
                
                for player, nbt in zip(players_to_update, nbt_data_list):
                    if nbt is not None:
                        player.nbt_data = nbt
            
            # Get the players that need to be displayed
            if self.offline_included:
                display_players = all_players
            else:
                display_players = [p for p in all_players if p.online]    
            display_players.sort(key=lambda p: (not p.online, p.name.lower()))
            
            # Rebuild the table and display the right players
            self.table.clear()
            for player in display_players:
                self.add_player_to_table(
                    name=player.name,
                    nbt_data=player.nbt_data,
                    is_online=player.online
                )
            
            # Select the previously selected row
            try:
                self.table.move_cursor(row=previous_row)
            except Exception:
                self.notify(severity="warning",
                            title="Previously selected user went offline!",
                            message=f"The previously selected user logged off. To see them, enable Include Offline Players.")
        except Exception as e:
            self.notify(severity="error",
                        title="Failed to build the table!",
                        message=f"Failed to build the table: {e}.")

    async def data_loop(self):
        while True:
            await self.build_table()
            await asyncio.sleep(self.app.player_update_interval)
                
    def add_player_to_table(self, name: str, nbt_data, is_online: bool):
        if not nbt_data:
            self.table.add_row(name, "?", "?", "?", "?", "?", "?", "?")
            return
        
        health = float(nbt_data["Health"])
        hunger = int(nbt_data['foodLevel'])
        xp_level = int(nbt_data['XpLevel'])
        pos = list(nbt_data['Pos'])
        dimension = format_tag(nbt_data['Dimension'])
        
        gamemode_number = int(nbt_data["playerGameType"])
        if gamemode_number == 0:
            gamemode = "Survival"
        elif gamemode_number == 1:
            gamemode = "Creative"
        elif gamemode_number == 2:
            gamemode = "Adventure"
        elif gamemode_number == 3:
            gamemode = "Spectator"
            
        status = "Online" if is_online else "Offline"
        
        self.table.add_row(
            name,
            status,
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
                self.selected_row = self.table.cursor_row
                row_data = self.table.get_row_at(self.selected_row)
                
                player_name = row_data[0]
                gamemode = row_data[7]
                online = True if row_data[1] == "Online" else False
                
                if event.button.id == "stats-button":
                    self.app.push_screen(StatsPopUp(player_name=player_name))
                elif event.button.id == "message-button":
                    if online:
                        self.app.push_screen(MessagePopUp(player_name=player_name))
                    else:
                        self.notify(severity="error",
                                    title="You can't message an offline player!",
                                    message=f"You're not able to message a player when they're not online.",
                                    timeout=3.0            
                        )     
                elif event.button.id == "kick-button":
                    if online:
                        self.app.push_screen(KickBanPopUp(player_name=player_name, action="kick"))
                    else:
                        self.notify(severity="error",
                                        title="You can't kick an offline player!",
                                        message=f"You're not able to kick a player when they're not online.",
                                        timeout=3.0            
                        )       
                elif event.button.id == "ban-button":
                    self.app.push_screen(KickBanPopUp(player_name=player_name, action="ban"))
                elif event.button.id == "gamemode-button":
                    if online:
                        async def on_popup_close(changed: bool):
                            if changed:
                                await self.refresh_data()
                        
                        self.app.push_screen(GamemodePopUp(player_name=player_name, current_gamemode=gamemode), on_popup_close)
                    else:
                        self.notify(severity="error",
                                    title="You can't change gamemode for an offline player!",
                                    message=f"You're not able to change the gamemode of a player when they're not online.",
                                    timeout=3.0            
                        )  
                
        if event.button.id == "refresh-button":
            await self.refresh_data()
            
        if event.button.id == "include-offline-button":
            self.offline_included = not self.offline_included
            
            if self.offline_included:
                event.button.add_class("on")
            else:
                event.button.remove_class("on")
            
            await self.build_table()
                
    async def refresh_data(self):
        await self.app.send_command("save-all")
        await asyncio.sleep(0.5)
        await self.app.update_server_status()
        await self.build_table()