from .utils import format_tag
from textual.screen import ModalScreen
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Label, Button, Input, TabbedContent, TabPane, DataTable

class GamemodePopUp(ModalScreen):
    AUTO_FOCUS="#label"
    CSS="""
    GamemodePopUp {
        align: center middle;
    }
    #pop-up {
        width: 65;
        height: auto;
    }
    
    Label {
        margin: 1 2;
        align: center middle;
    }
    
    #gamemode-buttons {
        height: auto;
        align: center middle;
        margin: 0 1;
    }
    #change-buttons {
        height: auto;
        align: center middle;
    }
    
    Button {
        margin: 1;
        border: none;
        min-height: 3;
        min-width: 10;
        content-align: center middle;
    }
    
    .gamemode-button.selected {
        background: green;
    }
    """
    
    def __init__(self, player_name: str, current_gamemode: str, **kwargs):
        super().__init__(**kwargs)
        self.player_name = player_name
        self.gamemode = current_gamemode
        self.gamemodes = ["Survival", "Creative", "Adventure", "Spectator"]
    
    def compose(self):
        with Vertical(id="pop-up"):
            yield Label(f"Set gamemode for {self.player_name}", id="label")
            with Horizontal(id="gamemode-buttons"):
                for gm in self.gamemodes:
                    if gm.lower() != self.gamemode.lower():
                        yield Button(label=gm, id=f"{gm}-button".lower(), classes="gamemode-button")
            with Horizontal(id="change-buttons"):
                yield Button(label="Apply", id="apply-button")
                yield Button(label="Cancel", id="cancel-button")
                
    def on_mount(self):
        for button in self.query(Button):
            button.can_focus = False
                
    async def on_button_pressed(self, event: Button.Pressed):
        if "gamemode-button" in event.button.classes:
            self.query(".gamemode-button").remove_class("selected")
            event.button.add_class("selected")
            
        elif event.button.id == "apply-button":
            selected_button = self.query(".selected")
            if selected_button:
                gamemode = str(selected_button.first().label).lower()
                await self.app.send_command(f"gamemode {gamemode} {self.player_name}")
                self.dismiss(True)
            else:
                self.notify(severity="error",
                            title="Select a gamemode!",
                            message="Select a gamemode before applying the changes.")
        
        elif event.button.id == "cancel-button":
            self.dismiss(False)
            
class MessagePopUp(ModalScreen):
    AUTO_FOCUS="#message-input"
    CSS="""
    MessagePopUp {
        align: center middle;
    }
    #pop-up {
        width: 65;
        height: auto;
    }
    
    #change-buttons {
        height: auto;
        align: center middle;
    }
    
    Label {
        margin: 1 2;
    }
    
    Input {
        margin: 0 1;
    }
    
    Button {
        margin: 1 2;
        border: none;
        min-height: 3;
        min-width: 10;
        content-align: center middle;
    }
    """
    
    def __init__(self, player_name: str, **kwargs):
        super().__init__(**kwargs)
        self.player_name = player_name
    
    def compose(self):
        with Vertical(id="pop-up"):
            yield Label(f"Send a message to {self.player_name}")
            yield Input(placeholder="Write a message...", id="message-input")
            with Horizontal(id="change-buttons"):
                yield Button(label="Send", id="send-button")
                yield Button(label="Cancel", id="cancel-button")
                
    def on_mount(self):
        for button in self.query(Button):
            button.can_focus = False
                
    async def on_button_pressed(self, event: Button.Pressed):            
        if event.button.id == "send-button":
            message = self.query_one("#message-input").value
            if message:
                await self.app.send_command(f'/tellraw {self.player_name} {{"text":"[Server ➔ You] > {message}"}}')
                self.dismiss()
            
        elif event.button.id == "cancel-button":
            self.dismiss()
            
    async def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "message-input":
            message = event.value
            if message:
                await self.app.send_command(f'/tellraw {self.player_name} {{"text":"[Server ➔ You] > {message}"}}')
                self.dismiss()
            
class KickBanPopUp(ModalScreen):
    AUTO_FOCUS="#reason-input"
    CSS="""
    KickBanPopUp {
        align: center middle;
    }
    #pop-up {
        width: 65;
        height: auto;
    }
    
    #change-buttons {
        height: auto;
        align: center middle;
    }
    
    Label {
        margin: 1 2;
    }
    
    Input {
        margin: 0 1;
    }
    
    Button {
        margin: 1 2;
        border: none;
        min-height: 3;
        min-width: 10;
        content-align: center middle;
    }
    #send-button {
        background: red;
        color: white;
    }
    """
    
    def __init__(self, player_name: str, action: str, **kwargs):
        super().__init__(**kwargs)
        self.player_name = player_name
        self.action = action.title()
    
    def compose(self):
        with Vertical(id="pop-up"):
            yield Label(f"{self.action} {self.player_name}")
            yield Input(placeholder=f"Write a reason for the {self.action}...", id="reason-input")
            with Horizontal(id="change-buttons"):
                yield Button(label=f"{self.action}", id="send-button")
                yield Button(label="Cancel", id="cancel-button")
                
    def on_mount(self):
        for button in self.query(Button):
            button.can_focus = False
                
    async def on_button_pressed(self, event: Button.Pressed):            
        if event.button.id == "send-button":
            reason = self.query_one("#reason-input").value
            if reason:
                await self.app.send_command(f'/{self.action.lower()} {self.player_name} {reason}')
                self.dismiss()
            
        elif event.button.id == "cancel-button":
            self.dismiss()
            
    async def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "reason-input":
            reason = event.value
            if reason:
                await self.app.send_command(f'/{self.action.lower()} {self.player_name} {reason}')
                self.dismiss()
                
class StatsPopUp(ModalScreen):
    CSS="""
    StatsPopUp {
        align: center middle;
    }
    #pop-up {
        width: 100;
        height: 80%;
    }

    #title {
        margin: 1 2;
        height: auto;
    }

    TabbedContent {
        height: 1fr;
    }
    ContentSwitcher {
        height: 1fr;
    }
    TabPane {
        height: 1fr;
        padding: 0;
    }
    DataTable {
        height: 1fr;
        padding: 1 2;
    }

    Button {
        margin: 1 2;
        border: none;
        height: 3;
        min-width: 10;
        content-align: center middle;
        background: black;
    }
    """
    
    def __init__(self, player_name: str, **kwargs):
        super().__init__(**kwargs)
        self.player_name = player_name

    
    def compose(self):
        with Vertical(id="pop-up"):
            yield Label(f"Statistics for {self.player_name}", id="title")
            
            with TabbedContent():
                with TabPane("General", id="tab-general"):
                    yield DataTable(id="table-general")
                with TabPane("Entities", id="tab-entities"):
                    yield DataTable(id="table-entities")
                with TabPane("Items", id="tab-items"):
                    yield DataTable(id="table-items")
                    
            yield Button(label="Back", id="back-button")
            
    async def on_mount(self):
        for button in self.query(Button):
            button.can_focus = False

        if self.app.dummy_server:
            self.stats = self.app.api.get_dummy_stats()
        else:
            uuid = await self.app.api.get_player_uuid(self.player_name)
            self.stats = await self.app.api.get_player_stats(uuid)
        
        if self.stats:
            stats = self.stats["stats"]
        else:
            self.notify(
                severity="error",
                title="No stats found",
                message="Pop-up was closed because no stats were found to show.",
                timeout=5.0
            )
            self.dismiss()
            return
        
        ##############################################
        # Create the general tab and fill in the data 
        ##############################################
        table_gen = self.query_one("#table-general", DataTable)
        table_gen.add_columns("Statistics", "Value")
        gen_data = stats.get("minecraft:custom", {})
        
        for tag, value in gen_data.items():        
            if "time" in tag:
                value = self.format_ticks(value)
                
            if "one_cm" in tag:
                tag = tag.replace("one_cm", "distance")
                value = self.format_cm(value)
                
            if "damage" in tag:
                value = self.format_damage(value)
            
            name = format_tag(tag)
            table_gen.add_row(name, value)
            
        ###############################################
        # Create the entities tab and fill in the data 
        ###############################################
        table_entities = self.query_one("#table-entities", DataTable)
        table_entities.add_columns("Entity", "Kills")
        entities_data = stats.get("minecraft:killed", {})
        
        sorted_entities = sorted(entities_data.items(), key=lambda mob: mob[1], reverse=True)
        for tag, value in sorted_entities:
            name = format_tag(tag)
            table_entities.add_row(name, value)

        ############################################
        # Create the items tab and fill in the data 
        ############################################
        table_items = self.query_one("#table-items", DataTable)
        table_items.add_columns("Item", "Crafted", "Mined", "Used", "Broken", "Picked up", "Dropped")
        
        crafted_data = stats.get("minecraft:crafted", {})
        mined_data = stats.get("minecraft:mined", {})
        used_data = stats.get("minecraft:used", {})
        broken_data = stats.get("minecraft:broken", {})
        picked_up_data = stats.get("minecraft:picked_up", {})
        dropped_data = stats.get("minecraft:dropped", {})
        
        all_items = set().union(
            crafted_data.keys(),
            mined_data.keys(),
            used_data.keys(),
            broken_data.keys(),
            picked_up_data.keys(),
            dropped_data.keys(),
        )
        sorted_items = sorted(all_items, key=lambda item: crafted_data.get(item, 0), reverse=True)
        
        for item in sorted_items:
            name = format_tag(item)
            crafted = crafted_data.get(item, 0)
            mined = mined_data.get(item, 0)
            used = used_data.get(item, 0)
            broken = broken_data.get(item, 0)
            picked_up = picked_up_data.get(item, 0)
            dropped = dropped_data.get(item, 0)
            
            table_items.add_row(
                name,
                crafted,
                mined,
                used,
                broken,
                picked_up,
                dropped
            )
        
    def format_ticks(self, ticks: int):
        if not ticks:
            return "0s"
        
        total_seconds = ticks // 20
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = (total_seconds % 3600) % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
        
    def format_cm(self, cm: int):
        if not cm:
            return "0 km"
        return f"{(cm / 100_000):.2f} km"
    
    def format_damage(self, damage: int):
        if not damage:
            return "0 [red]♥\uFE0E[/red]"
        
        hearts = damage / 20 # damage is saved in one factor of 10 bigger to give more precision
        return f"{hearts:.1f} [red]♥\uFE0E[/red]"    
    
    async def on_button_pressed(self, event: Button.Pressed):            
        if event.button.id == "back-button":
            self.dismiss()