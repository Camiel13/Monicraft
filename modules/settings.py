import os
from textual.screen import Screen
from dotenv import load_dotenv, set_key
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Header, RichLog, Input, Label, Button

class Settings(Screen):
    AUTO_FOCUS = "#api_key"
    CSS="""
    Header {
        height: 3;
        align: center middle;
        background: darkgreen;
    }
    .creds-box, .setting-box {
        padding: 1;
        margin: 1 2;
        height: auto;
    }
    Input {
        margin-top: 1;
        margin-left: -1;
    }
    Input:focus {
        border: none;
        padding: 1;
        padding-left: 2;
    }
    Button {
        margin: 1;
        border: none;
        min-height: 3;
        min-width: 8;
        content-align: center middle;
    }
    #back-button {
        width: 8;
        min-width: 8;
        margin: 1 2;
    }
    #button-bar {
        align: right bottom;
        width: 100%;
        height: auto;
        dock: bottom;
    }
    #reset-button {
        background: red;
        color: black;
    }
    """
    @property
    def api(self):
        return self.app.api
    
    def compose(self):
        # The ID of the input matches the name of the attribute in the API class
        yield Header(name="Settings", show_clock=True, icon="")
        yield Button(label="<", id="back-button")
        with VerticalScroll(id="settings-scroll", can_focus=False):
            with Vertical(classes="creds-box"):
                yield Label("[bold  green]API Key[/]")
                yield Input(placeholder="e.g. ptlc_d7F9aK3mL2nO8pQ1rT5uV4wX9zY6sB2eG8hI0jK5", id="api_key")
            with Vertical(classes="creds-box"):
                yield Label("[bold  green]Panel Endpoint[/]")
                yield Input(placeholder="e.g. panel.camilio13.com", id="panel_endpoint")
            with Vertical(classes="creds-box"):
                yield Label("[bold green]Server ID[/]")
                yield Input(placeholder="e.g. panel.camilio13.com/server/937284kf", id="server_id")
            with Vertical(classes="setting-box"):
                yield Label("[bold blue]Server Ping Interval (updates online player list)[/]")
                yield Input(placeholder="e.g. 10 (seconds)", id="server_ping_interval")
            with Vertical(classes="setting-box"):
                yield Label("[bold blue]Player Update Interval (updates online player data)[/]")
                yield Input(placeholder="e.g. 30 (seconds)", id="player_update_interval")
            with Vertical(classes="setting-box"):
                yield Label("[bold blue]Chat Mode Prefix[/]")
                yield Input(placeholder="e.g. Admin Camilio13 > ", id="chat_mode_prefix")
            with Horizontal(id="button-bar"):
                yield Button(label="Save", id="save-button")
                yield Button(label="Reset", id="reset-button")
    
    def on_mount(self):
        self.update_inputs()
                
        for button in self.query(Button):
            button.can_focus = False
                
    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "back-button":
            self.save_creds()
            self.save_settings()
            self.dismiss()
        
        if event.button.id == "save-button":
            self.save_creds()
            self.save_settings()
            
        if event.button.id == "reset-button":
            # Make sure you don't reset your .env while in dummy mode (yeah, this happened to me)
            if self.app.dummy_server:
                return
            
            for input_box in self.query(".creds-box Input"):
                setattr(self.api, input_box.id, "")
                set_key(".env", input_box.id.upper(), "")
            
            self.notify(severity="error",
                        title="Deleted credentials!",
                        message="If you clicked this by accident, you're pretty unlucky quite honestly.")

            self.update_inputs()
            
    def save_creds(self):
        # Make sure the dummy details don't get saved to the .env (yup, this also happened to me)
        if self.app.dummy_server:
            return
        
        for input_box in self.query(".creds-box Input"):
            if hasattr(self.api, input_box.id):
                setattr(self.api, input_box.id, input_box.value)
                set_key(".env", input_box.id.upper(), input_box.value)
                
        self.api.init_client()
        
        self.notify(severity="information",
                    title="Saved changes!",
                    message="Your changes have been written to the .env file!")
        
    def save_settings(self):
        for input_box in self.query("#server_ping_interval, #player_update_interval"):
            val = input_box.value.strip()
            if val.isdigit():
                try:
                    setattr(self.app, input_box.id, int(input_box.value))
                except Exception:
                    self.notify(severity="error",
                                title="Invalid value!",
                                message=f"Entered invalid value for {input_box.id.strip("#").replace("_", " ")}")
        
        for input_box in self.query("#chat_mode_prefix"):
            try:
                setattr(self.app, input_box.id, input_box.value)
            except Exception:
                self.notify(severity="error",
                            title="Invalid value!",
                            message=f"Entered invalid value for {input_box.id.strip("#").replace("_", " ")}")
                        
    def update_inputs(self):
        for input_box in self.query(".creds-box Input"):
            if hasattr(self.api, input_box.id):
                input_box.value = getattr(self.api, input_box.id) or ""
        
        for input_box in self.query(".setting-box Input"):
            input_box.value = str(getattr(self.app, input_box.id)) or ""