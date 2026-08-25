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
        width: 10;
        min-width: 5;
        height: 3;
        background: #3a473b;
        border: none;
        margin: 0;
        content-align: center middle;
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
        margin: 1 0;
        padding: 1;
        border: round #455446;
        border-title-align: center;
        border-title-color: #88c090;
        background: #3a473b;
        content-align: center middle;
    }
    
    #power-buttons {
        align: center middle;
        width: 100%;
        height: auto;
    }
    .power-button {
        border: none;
        width: 7;
        min-width: 7;
        height: 3;
        background: #3a473b;
        margin: 0 1;
        content-align: center middle;
    }
    .power-button:hover {
        background: #485749;
    }
    
    #nav-buttons {
        width: 100%;
        margin: 1 0;
        align: center bottom;
    }
    .nav-button {
        border: none;
        width: 1fr;
        min-width: 9;
        height: 3;
        background: #3a473b;
        margin: 0 1;
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
        self.api.app = self

        # Dummy server toggle
        self.dummy_server = True if self.api.__class__.__name__ == "DummyAPI" else False

        # Server information variables
        self.ws = None
        self.chat_mode = False
        self.query_enabled = True
        self.status_server = None
        self.query_server = None
        self.server_state = None
        
        # Changeable settings
        self.chat_mode_prefix = "> "
        self.server_ping_interval = 10
        self.player_update_interval = 30
        
    
    def compose(self):
        yield Header(show_clock=True, name="Monicraft", icon="")
        with Horizontal(id="body"):
            with Vertical(id="sidebar"):
                with Horizontal(id="power-buttons"):
                    yield Button("▶", id="start-button", classes="power-button")
                    yield Button("↻", id="restart-button", classes="power-button")
                    yield Button("■", id="stop-button", classes="power-button")
                    yield Button("✕", id="kill-button", classes="power-button")
                yield Label("Connecting to server...", classes="stats", id="server-status")
                yield Label("Connecting to server...", classes="stats", id="ram-usage")
                yield Label("Connecting to server...", classes="stats", id="cpu-usage")
                yield Label("Connecting to server...", classes="stats", id="disk-usage")
                yield Label("Connecting to server...", classes="stats", id="network-usage")
                with Horizontal(id="nav-buttons"):
                    yield Button(label="ᴄꜰɢ", id="settings-button", classes="nav-button")
                    yield Button(label="ᴍᴏᴅ", id="mods-button", classes="nav-button")
                    yield Button(label="ᴘʟʏʀ", id="players-button", classes="nav-button")
            with Vertical(id="console"):
                yield RichLog(id="console-log", highlight=True, markup=True)
                with Horizontal(id="input-box"):
                    yield Button(label=">>", id="chat-mode-button")
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
        self.disk_usage = self.query_one("#disk-usage", Label)
        self.network_usage = self.query_one("#network-usage", Label)
        
        self.server_status.border_title = "Status"
        self.ram_usage.border_title = "RAM"
        self.cpu_usage.border_title = "CPU"
        self.disk_usage.border_title = "Disk"
        self.network_usage.border_title = "Network"
        
        # Tweak the created components
        for button in self.query(Button):
            button.can_focus = False
        
        # Start the background workers and check the connection
        self.connection_established, message = await self.api.test_connection()
        
        if self.connection_established:
            try:
                await self.api.init_caches()
            except Exception as e:
                self.notify(severity="error",
                            title="Failed to initialize caches!",
                            message=f"Could not reach server: {e}")    
                
            self.notify(severity="information",
                        title="Connection successful!", 
                        message=message,
                        timeout=5
            )
        else:
            self.notify(severity="error",
                        title="Connection failed!",
                        message=message,
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
            self.console_log.write("[green]Successfully connected to the dummy server![/]")
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
                    disk_usage = stats.get("disk_bytes") / (1024 ** 3)
                    network_inbound = stats["network"].get("rx_bytes") / (1024 ** 2)
                    network_outbound = stats["network"].get("tx_bytes") / (1024 ** 2)
                    
                    self.server_status.update(f"[{server_status_color}]{server_status.upper()}[/]")
                    self.ram_usage.update(f"[green]{ram_usage:.2f}[/]/[green]{ram_limit:.2f}[/] GB")
                    self.cpu_usage.update(f"{cpu_percent:.2f}%")
                    self.disk_usage.update(f"{disk_usage:.2f} GB")
                    self.network_usage.update(f"{network_inbound:.2f}/{network_outbound:.2f} MB")
            
        except Exception as e:
            self.ws = None
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
            self.notify(severity="error",
                        title="Command failed!",
                        message="Command could not be sent, no server connection esthablished.")
            return
            
        try:
            command = f"say {self.chat_mode_prefix + command}" if self.chat_mode else command
            
            payload = {
                "event": "send command",
                "args": [command]
            }
            
            await self.ws.send(json.dumps(payload))
            
        except Exception as e:
            self.console_log.write(f"[bold red] Command couldn't be sent: {e}[/]")
            self.notify(title="Command could not be sent!",
                        message=f"The command could not be sent to the server: {e}",
                        severity="error",
                        timeout=10.0
            )
            
    async def send_power_action(self, action: str):
        if self.dummy_server:
            self.console_log.write(f"Power action sent to dummy server: [bold blue]{action}[/]")
            return
        
        if not self.ws:
            self.notify(severity="error",
                        title="Power action failed!",
                        message="Power action could not be sent, no server connection esthablished.")
            return
        
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
            if self.connection_established:
                try:
                    if getattr(self, "server", None) is None and not self.dummy_server:
                        await self.find_server()
                        if getattr(self, "server", None):
                            await self.update_server_status()
                    elif self.server_state == "running":                    
                        await self.update_server_status()
                except Exception:
                    pass
            await asyncio.sleep(self.server_ping_interval)
            
    async def stream_dummy_data(self):
        try:
            while True:   
                server_status = "running"
                server_status_color = "bold green" if server_status == "running" else "bold red"
                ram_usage =  random.uniform(1.5, 10.0)
                ram_limit =  10.0
                cpu_percent = random.uniform(0.5, 100.0)
                
                self.server_status.update(f"[{server_status_color}]{server_status.upper()}[/]")
                self.ram_usage.update(f"[green]{ram_usage:.2f}[/]/[green]{ram_limit:.2f}[/] GB")
                self.cpu_usage.update(f"{cpu_percent:.2f}%")
                self.disk_usage.update(f"{random.uniform(5.0, 20.0):.2f} GB")
                self.network_usage.update(f"{random.uniform(0.5, 10.0):.2f}/{random.uniform(1.0, 30.0):.2f} MB")
                
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