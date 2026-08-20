import json
import random
import asyncio
import websockets
from rich.markup import escape
from .mods import Mods
from .utils import console
from .players import Players
from .settings import Settings
from mcstatus import JavaServer
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, RichLog, Input, Label, Button

class TUI(App):
    AUTO_FOCUS="#console-input"
    SCREENS = {
        "settings": Settings,
        "mods": Mods,
        "players": Players
    }
    TITLE = "Monicraft"
    SUB_TITLE = "Console & Server Monitoring"
    CSS = """
    Screen {
        width: 100%;
        height: 100%;
        margin: 0;
        padding: 0;
    }
    
    Header {
       height: 3;
       align: center middle;
       background: darkgreen;
    }
    
    #body {
        height: 1fr;
    }
    
    #sidebar {
        width: 1fr;
        min-width: 25;
        max-width: 40;
        align: center top;
        background: #232e24;
        padding: 1;
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
        scrollbar-visibility: hidden;
    }
    
    #console-input {
        padding: 1;
        border: none;
        align: center middle;
        background: #232e24;
    }
    
    #chat-mode-button {
        min-width: 5;
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
        width: 100%;
        height: auto;
        margin-top: 1;
        padding: 1;
        border: inner #455446;
        background: #3a473b;
        text-align: center;
    }
    
    #power-buttons {
        align: center middle;
        width: 100%;
        height: auto;
    }
    .power-button {
        border: none;
        min-width: 5;
        height: 3;
        padding: 0 1;
        background: #3a473b;
        margin: 0 1;
        align: center middle;
    }
    .power-button:hover {
        background: #485749;
    }
    
    #nav-buttons {
        width: 100%;
        margin: 1;
        align: center bottom;
    }
    .nav-button {
        border: none;
        min-width: 9;
        height: 3;
        padding: 0 1;
        background: #3a473b;
        margin: 0 1;
        align: center middle;
        content-align: center middle;
    }
    .nav-button:hover {
        background: #485749;
    }
    
    #kill-button.confirm {
        background: red;
    }
    #kill-button.confirm:hover {
        background: darkred;
    }
    """
    BINDINGS = [("q", "quit", "exit")]
    
    def __init__(self, api_client, **kwargs):
        super().__init__(**kwargs)
        self.api = api_client
        self.ws = None
        self.chat_mode = False
        self.query_enabled = True
        self.status_server = None
        self.query_server = None
        self.server_state = None
        self.dummy_server = True if self.api.__class__.__name__ == "DummyAPI" else False
        self.api.app = self
    
    def compose(self):
        yield Header(show_clock=True, name="Monicraft", icon="")
        with Horizontal(id="body"):
            with Vertical(id="sidebar"):
                with Horizontal(id="power-buttons"):
                    yield Button("▶\uFE0E", id="start-button", classes="power-button")
                    yield Button("↻\uFE0E", id="restart-button", classes="power-button")
                    yield Button("■\uFE0E", id="stop-button", classes="power-button")
                    yield Button("☠\uFE0E", id="kill-button", classes="power-button")
                yield Label("Connecting to server...", classes="stats", id="server-status")
                yield Label("Connecting to server...", classes="stats", id="ram-usage")
                yield Label("Connecting to server...", classes="stats", id="cpu-usage")
                with Horizontal(id="nav-buttons"):
                    yield Button(label="⚙\uFE0E", id="settings-button", classes="nav-button")
                    yield Button(label="⚒\uFE0E", id="mods-button", classes="nav-button")
                    yield Button(label="☺\uFE0E", id="players-button", classes="nav-button")
            with Vertical(id="console"):
                yield RichLog(id="console-log", highlight=True, markup=True)
                with Horizontal(id="input-box"):
                    yield Button(label="✉\uFE0E", id="chat-mode-button")
                    yield Input(id="console-input", placeholder="Type a minecraft command to send it to the server...")
                    
    async def on_mount(self):        
        # Get the server address and set the title
        if self.dummy_server:
           self.title = "Monicraft (dummy)"
           self.sub_title = "Dummy Server"

        # Define the elements as variables for easy access
        self.console_log = self.query_one("#console-log", RichLog)
        self.console_input = self.query_one("#console-input", Input)
        self.server_status = self.query_one("#server-status", Label)
        self.ram_usage = self.query_one("#ram-usage", Label)
        self.cpu_usage = self.query_one("#cpu-usage", Label)
        
        # Tweak the created components
        for button in self.query(Button):
            button.can_focus = False
        
        # Start the background workers
        if not self.api.is_configured:
            self.notify(severity="warning",
                        title="Credentials not filled in.",
                        message="You've not filled in your server's credentials yet, you can do this manually in the .env file or simply fill them in in the settings menu.",
                        timeout=15
            )
        
        self.run_worker(self.connect_ws, thread=False)
        self.run_worker(self.data_loop, thread=False)
        
    async def on_unmount(self):
        if self.ws:
            await self.ws.close()
        
    async def connect_ws(self):
        if self.dummy_server:
            self.ws = None
            self.run_worker(self.stream_dummy_data, thread=False)
            self.console_log.write("[green]Succesfully connected to the dummy server![/]")
            return

        while True:
            try:
                token, socket_url = await self.api.get_websocket_creds()
                origin = f"https://{self.api.panel_endpoint}"
                        
                self.ws = await websockets.connect(socket_url, origin=origin)
                
                auth_message = {
                    "event": "auth",
                    "args": [token]
                }
                
                await self.ws.send(json.dumps(auth_message))
                
                self.run_worker(self.stream_data, thread=False)
                
                self.console_log.write("[green]Successfully connected to the server![/]")
                
                return
            except Exception as e:
                self.notify(title="Couldn't connect to server!",
                            message=f"Server connection could not be established. Retrying in 5 seconds...",
                            severity="error",
                            timeout=6.0
                )
                
                # Wait 5 seconds until next try
                await asyncio.sleep(5)
    
    async def stream_data(self):        
        try:   
            async for m in self.ws:
                data = json.loads(m)
                
                if data.get("event") == "console output":
                    for i in data.get("args"):
                        self.console_log.write(escape(i))
                        
                if data.get("event") == "stats":
                    stats = json.loads(data.get("args")[0])
                    
                    server_status = stats.get("state")
                    self.server_state = server_status
                    server_status_color = "bold green" if server_status == "running" else "bold red"
                    ram_usage = stats.get('memory_bytes') / (1024 ** 3)
                    ram_limit = stats.get("memory_limit_bytes") / (1024 ** 3)
                    cpu_percent = stats.get("cpu_absolute")
                    
                    
                    self.server_status.update(f"Server status: [{server_status_color}]{server_status}[/]")
                    self.ram_usage.update(f"RAM: [green]{ram_usage:.2f}[/]/[green]{ram_limit:.2f}[/] GB")
                    self.cpu_usage.update(f"CPU: {cpu_percent}%")
            
        except Exception as e:
            self.console_log.write(f"[bold red]Server connection lost: {e}[/]")
            self.notify(title="Server Connection error",
                        message=f"Server connection lost: {e}",
                        severity="error",
                        timeout=10.0
                        )
            
            # Try reconnecting, this will loop every 5 seconds if creds are wrong.
            self.run_worker(self.connect_ws, thread=False)
            
    async def find_server(self):
        self.server_ip, self.server_port = await self.api.get_server_address()
        if self.server_ip and self.server_port:
            self.server = JavaServer.lookup(f"{self.server_ip}:{self.server_port}")
        else:
            self.notify(severity="error",
                        title="Failed to get server ip or port!",
                        message="There was a problem while getting the server port and ip from the server."
            )
                        
    async def send_command(self, command: str):
        if self.dummy_server:
            self.console_log.write(f"Sent command to dummy server: [bold blue]{command}[/]")
            return
        
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
            self.notify(title="Command couldn't be send!",
                        message=f"The command could not been sent to the server: {e}",
                        severity="error",
                        timeout=10.0
            )
            
    async def send_power_action(self, action: str):
        if self.dummy_server:
            self.console_log.write(f"Power action sent to dummy server: [bold blue]{action}[/]")
            return
        
        if not self.ws:
            await self.connect_ws()
        
        try:
            payload = {
                "event": "set state",
                "args": [action]
            }
            
            await self.ws.send(json.dumps(payload))
        
        except Exception as e:
            self.console_log.write(f"[bold red] Power action couldn't be sent: {e}[/]")        
            
            
    async def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "console-input":
            command = event.value.strip()
            if command == "settings":
                self.push_screen("settings")
                event.input.value = ""
                return
            elif command == "mods":
                self.push_screen("mods")
                event.input.value = ""
                return
            
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
        
        if event.button.id == "start-button":
            await self.send_power_action(action="start")
        elif event.button.id == "restart-button":
            await self.send_power_action(action="restart")
        elif event.button.id == "stop-button":
            await self.send_power_action(action="stop")   
        elif event.button.id == "kill-button":
            if "confirm" not in event.button.classes:
                self.notify(title="Are you sure you want to kill the server?",
                            message=f"This can lead to data loss or corruption. Press again to confirm.",
                            severity="error",
                            timeout=10.0
                )
                event.button.add_class("confirm")
                self.set_timer(10.0, lambda: event.button.remove_class("confirm"))
            else:
                await self.send_power_action(action="kill")
                event.button.remove_class("confirm")
        
        if event.button.id == "mods-button":
            self.push_screen("mods")
        elif event.button.id == "settings-button":
            self.push_screen("settings")
        elif event.button.id == "players-button":
            self.push_screen("players")
            
    async def update_server_status(self):
        if self.dummy_server:
            return
                
        # Check if server has queries enabled, if not, use status
        if self.query_enabled:
            try:
                self.query_server = await self.server.async_query()
                self.sub_title = f"{self.server_ip}:{self.server_port} (Minecraft {self.query_server.software.version})"
                return
            except Exception:
                self.query_enabled = False
                self.query_server = None
                self.notify(title="Failed to get query!",
                            message=f"Failed to get a query from the server. You can turn this on in your server.properties by setting enable-query to true. Leaving this off may lead to inaccurate player statistics.",
                            severity="warning",
                            timeout=10.0
                )     
              
        try:
            self.status_server = await self.server.async_status()
            self.sub_title = f"{self.server_ip}:{self.server_port} (Minecraft {self.status_server.version.name})"
        except Exception as e:
            self.status_server = None
            self.notify(title="Error while pinging server stats",
                        message=f"An error occurred while pinging the server: {e}",
                        severity="error",
                        timeout=10.0
            )

    
    async def data_loop(self):
        while True:
            if self.api.is_configured:
                if getattr(self, "server", None) is None and not self.dummy_server:
                    await self.find_server()
                    if getattr(self, "server", None):
                        await self.update_server_status()
                elif self.server_state == "running":                    
                    await self.update_server_status()
            await asyncio.sleep(10)
            
    async def stream_dummy_data(self):
        try:
            while True:   
                server_status = "running"
                server_status_color = "bold green" if server_status == "running" else "bold red"
                ram_usage =  random.uniform(1.5, 10.0)
                ram_limit =  10.0
                cpu_percent = random.uniform(0.5, 100.0)
                
                self.server_status.update(f"Server status: [{server_status_color}]{server_status}[/]")
                self.ram_usage.update(f"RAM: [green]{ram_usage:.2f}[/]/[green]{ram_limit:.2f}[/] GB")
                self.cpu_usage.update(f"CPU: {cpu_percent:.2f}%")
                
                await asyncio.sleep(2)
            
        except Exception as e:
            self.console_log.write(f"[bold red]Server connection lost: {e}[/]")
            self.notify(title="Server Connection error",
                        message=f"Server connection lost: {e}",
                        severity="error",
                        timeout=10.0
                        )
            
            # Try reconnecting, this will loop every 5 seconds if creds are wrong.
            self.run_worker(self.connect_ws, thread=False)