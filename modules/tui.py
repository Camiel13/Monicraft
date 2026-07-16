import json
import asyncio
import websockets
from .utils import console
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, RichLog, Input, Label, Button

class TUI(App):
    TITLE = "Monicraft"
    SUB_TITLE = "Console & Server Monitoring"
    CSS = """
    Header {
       height: 3;
       align: center middle;
    }
    
    #body {
        height: 1fr;
    }
    
    #sidebar {
        width: 1fr;
        align: center middle;
        text-align: center;
        background: #232e24;
    }
    
    #console {
        width: 4fr;
    }
    
    #input-box {
        width: 100%;
        height: 3;
    }
    
    #console-log {
        padding: 1;
        overflow-y: auto;
        background: #b4cfb6;
    }
    
    #console-input {
        padding: 1;
        border: none;
        align: center middle;
        background: #232e24;
    }
    
    #chat-mode-button {
        min-width: 7;
        height: 3;
        background: #3a473b;
        border: none;
        margin: 0;
    }
    #chat-mode-button:hover {
        background: #485749;
    }
    #chat-mode-button.activated {
        background: #52a157;
    }
    #chat-mode-button.activated:hover {
        background: #5aad5f;
    }
    
    .stats {
        min-width: 35;
        min-height: 6;
        margin: 5;
        padding: 3;
        border: inner #455446;
        background: #3a473b;
    }
    """
    BINDINGS = [("q", "quit", "exit")]
    
    def __init__(self, api_client, **kwargs):
        super().__init__(**kwargs)
        self.api = api_client
        self.ws = None
        self.chat_mode = False
    
    def compose(self):
        yield Header(show_clock=True, name="Monicraft", icon="")
        with Horizontal(id="body"):
            with Vertical(id="sidebar"):
                yield Label("Connecting to server...", classes="stats", id="server-status")
                yield Label("Connecting to server...", classes="stats", id="ram-usage")
                yield Label("Connecting to server...", classes="stats", id="cpu-usage")
            with Vertical(id="console"):
                yield RichLog(id="console-log", highlight=True, markup=True)
                with Horizontal(id="input-box"):
                    yield Button(label="✉", classes="button", id="chat-mode-button")
                    yield Input(id="console-input", placeholder="Type a minecraft command to send it to the server...")
                    
    async def on_mount(self):
        # Define the elements as variables for easy access
        self.console_log = self.query_one("#console-log", RichLog)
        self.console_input = self.query_one("#console-input", Input)
        self.server_status = self.query_one("#server-status", Label)
        self.ram_usage = self.query_one("#ram-usage", Label)
        self.cpu_usage = self.query_one("#cpu-usage", Label)
        
        # Tweak the created components
        self.query_one("#chat-mode-button", Button).can_focus = False
        
        # Put the cursor in the console input
        self.console_input.focus()
        
        # Start receiving data
        self.run_worker(self.stream_data, thread=False)
        
    async def on_unmount(self):
        if self.ws:
            self.ws.close()
        
    async def connect_ws(self):
        try:
            token, socket_url = self.api.get_websocket_creds()
            origin = f"https://{self.api.panel_endpoint}"
                    
            self.ws = await websockets.connect(socket_url, origin=origin)
            
            auth_message = {
                "event": "auth",
                "args": [token]
            }
            
            await self.ws.send(json.dumps(auth_message))
            
            self.console_log.write("[green]Succesfully connected to the server![/]")
            return True
        except Exception as e:
            self.console_log.write("[bold red]Couldn't connect to the server![/]")
    
    async def stream_data(self):        
        if not self.ws:
            self.console_log.write("[bold red]No connection with the server. Establishing now...[/]")
            await self.connect_ws()
                    
        try:   
            async for m in self.ws:
                data = json.loads(m)
                
                if data.get("event") == "console output":
                    for i in data.get("args"):
                        self.console_log.write(i)
                        
                if data.get("event") == "stats":
                    stats = json.loads(data.get("args")[0])
                    
                    server_status = stats.get("state")
                    server_status_color = "bold green" if server_status == "running" else "bold red"
                    ram_usage = stats.get('memory_bytes') / (1024 ** 3)
                    ram_limit = stats.get("memory_limit_bytes") / (1024 ** 3)
                    cpu_percent = stats.get("cpu_absolute")
                    
                    
                    self.server_status.update(f"Server status: [{server_status_color}]{server_status}[/]")
                    self.ram_usage.update(f"RAM: [green]{ram_usage:.2f}[/]/[green]{ram_limit:.2f}[/] GB")
                    self.cpu_usage.update(f"CPU: {cpu_percent}%")
            
        except Exception as e:
            self.console_log.write(f"[bold red]Server connection lost: {e}[/]")
            
            
    async def send_command(self, command: str):
        if not self.ws:
            await self.connect_ws()
            
        try:
            command = f"say {command}" if self.chat_mode else command
            
            payload = {
                "event": "send command",
                "args": [command]
            }
            
            await self.ws.send(json.dumps(payload))
            
        except Exception as e:
            self.console_log.write(f"[bold red] Command couldn't be sent: {e}[/]")
            
    async def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "console-input":
            command = event.value.strip()
            if command:
                event.input.value = "" # clear the text in the input
                await self.send_command(command)
                
    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "chat-mode-button":
            self.chat_mode = not self.chat_mode
            
            if self.chat_mode:
                event.button.add_class("activated")
            else:
                event.button.remove_class("activated")
                
            event.button.refresh()