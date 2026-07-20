import os
from .api import API
from textual.screen import Screen
from dotenv import load_dotenv, set_key
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, RichLog, Input, Label, Button

class Settings(Screen):
    AUTO_FOCUS = "#api_key"
    CSS="""
        .creds-box {
            padding: 2;
            margin: 3;
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
        #button-bar {
            align: right bottom;
            width: 100%;
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
        yield Header(name="Settings", show_clock=True)
        yield Button(label="<", id="back-button")
        with Vertical(classes="creds-box"):
            yield Label("[bold  green]API Key[/]")
            yield Input(placeholder="e.g. ptlc_d7F9aK3mL2nO8pQ1rT5uV4wX9zY6sB2eG8hI0jK5", id="api_key")
        with Vertical(classes="creds-box"):
            yield Label("[bold  green]Panel Endpoint[/]")
            yield Input(placeholder="e.g. panel.camilio13.com", id="panel_endpoint")
        with Vertical(classes="creds-box"):
            yield Label("[bold green]Server ID[/]")
            yield Input(placeholder="e.g. panel.camilio13.com/server/[bold blue]937284kf[/]", id="server_id")
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
            self.dismiss()
        
        if event.button.id == "save-button":
            self.save_creds()
            
        if event.button.id == "reset-button":
            for input_box in self.query(Input):
                setattr(self.api, input_box.id, "")
                set_key(".env", input_box.id.upper(), "")
            
            self.notify(severity="error",
                        title="Deleted credentials!",
                        message="If you clicked this by accident, you're pretty unlucky quite honestly.")

            self.update_inputs()
            
    def save_creds(self):
        for input_box in self.query(Input):
            if hasattr(self.api, input_box.id):
                setattr(self.api, input_box.id, input_box.value)
                set_key(".env", input_box.id.upper(), input_box.value)
        
        self.notify(severity="information",
                    title="Saved changes!",
                    message="Your changes have been written to the .env file!")
        
    def update_inputs(self):
        for input_box in self.query(Input):
            if hasattr(self.api, input_box.id):
                input_box.value = getattr(self.api, input_box.id)
        
        