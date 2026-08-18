from textual.screen import ModalScreen
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Label, Button, Input, TabbedContent, TabPane

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
        width: 65;
        height: auto;
    }

    #title {
        dock: top;
        margin: 1 2;
    }
    Button {
        margin: 1 2;
        border: none;
        min-height: 3;
        min-width: 10;
        content-align: center middle;
        dock: bottom;
    }
    """
    
    def __init__(self, player_name: str, stats: dict, **kwargs):
        super().__init__(**kwargs)
        self.player_name = player_name
        self.stats = stats
    
    def compose(self):
        with Vertical(id="pop-up"):
            yield Label(f"Statistics for {self.player_name}", id="title")
            
            with TabbedContent:
                with TabPane("General", id="tab-general"):
                    yield DataTable(id="table-general")
                with TabPane("Mined", id="tab-mined"):
                    yield DataTable(id="table-mined")
                with TabPane("Killed", id="tab-killed"):
                    yield DataTable(id="table-killed")
                with TabPane("Crafted", id="tab-crafted"):
                    yield DataTable(id="table-crafted")
                    
            yield Button(label="Back", id="back-button")
            
    def on_mount(self):
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
            
        # Create the general tab and get the data
        table_gen = self.query_one("#table-general", DataTable)
        table_gen.add_columns("Statistics", "Value")
        gen_data = stats["minecraft:custom"]
        
        custom_stats = [
            ("Play Time", "minecraft:play_time", self.format_ticks),
            ("Deaths", "minecraft:deaths", self.format_num),
        ]
        
        # Fill in the important data
        for name, tag, formatter in custom_stats:
            table_gen.add_row(name, formatter(gen_data["tag"]))
        
    def format_ticks(self, ticks: int):
        if not ticks:
            return "0s"
        
        total_seconds = ticks // 20
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = (total_seconds % 3600) % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif hours < 0 and minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
        
    def format_cm(self, cm: int):
        if not cm:
            return "0 km"
        return f"{(cm / 1000):.2f} km"
    
    def format_num(self, val):
        return f"{val or 0}"
        
    def format_bar_num(self, val):
        return f"{val/2 or 0}"
        