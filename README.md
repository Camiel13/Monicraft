# Monicraft
Monicraft is a TUI-based application that runs right inside your terminal. It makes it easier to monitor your rented or self-hosted Minecraft server that runs on Pterodactyl panel (or some forked versions of it). It relies on websockets and requests to the REST API to make the app fast and responsive. It gathers it's information by using the [mcstatus](https://github.com/py-mine/mcstatus) python library and inspects NBT data with the [nbtlib](https://github.com/vberlier/nbtlib) python library.

## Features
- **Real-Time Console Monitoring:** The server console is directly streamed into your terminal and formatted with a `RichLog` widget.
- **Command Execution:** Minecraft commands can be sent directly to the server. The command will be exectued on the server and the command and it's output will appear in the **console**.
- **Power Actions:** The server can be easily started, stopped, restarted and killed by using the **Power Buttons** in the sidebar.
- **Resource Monitoring:** The CPU usage, RAM usage, server state, disk usage and network inbound/outbound are shown in the sidebar and are activly updated through websockets.
- **Chat Mode:** Removes the annoying `say ` prefix you have to type in front of every command if you just want to message. You're able to change prefixes through the **settings**.
- **Settings Page:** A simple interface for initializing and changing your enviroment variables (used to connect to the server). You can also change the prefix of your **chat mode** and the interval of data loops.
- **Mod Page:** A table where where all installed mods are shown, together with their size (in MB) and the date it was last changed.
- **Player Manager:**
    - **Player List:** An overview of all the players on the server.
    - **Include Offline Player Toggle:** Toggle the visibility of offline players in the **player list**. This data is cached in memory to make sure data for offline players is not fetched every time data is updated for online players.
    - **Kicking and Banning:** Kick or ban people by simply selecting them and adding a reason for the kick/ban. (*kick: online; ban: offline/online*)
    - **Message Players:** Send private in-game messages to players without alerting the whole server. (*online*)
    - **Change Gamemodes:** Change player's gamemode by selecting it in a pop-up. The gamemode they're currently in will not show up. (*online*)
    - **Statistics Viewer:** View all the stats of any player: General stats (play time, deaths, etc.), Entities (amount of entities killed) and Items (crafted, mined, used, broken, picked up, dropped). (*online/offline*)

# Installation Guide
## Installation through binary
Download the right binary for your operating system from the [v1.0.0 Release](https://github.com/Camiel13/Monicraft/releases/tag/v1.0.0) and run the following commands:

Windows:
```shell
# Start the program
.\monicraft-windows.exe

# Or start the program in dummy mode
.\monicraft-windows.exe --dummy
```

Linux:
```bash
# Make executable and start the program
chmod +x monicraft-linux
./monicraft-linux

# Or start the program in dummy mode
./monicraft-linux --dummy
```

## Installation from source
To compile it from source you will have to run the following commands:

Windows:
```shell
git clone https://github.com/Camiel13/Monicraft.git
cd Monicraft

# Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the program
python main.py

# Or start the program in dummy mode
python main.py --dummy
```

Linux:
```bash
git clone https://github.com/Camiel13/Monicraft.git
cd Monicraft

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the program
python3 main.py

# Or start the program in dummy mode
python3 main.py --dummy
```

# Configuration
You can configure your server credentials either directly in the **Settings** menu inside the app, or by creating a `.env` file in the root directory:

```env
API_KEY="ptlc_xxxxxxxxxxxxxxxxxxxxxxxx"
PANEL_ENDPOINT="panel.yourdomain.com"
SERVER_ID="698408ad"
```

# AI declaration
I used AI to get familiar with python libraries used in my project by asking it how it's used what the the common use cases are. I also used AI to debug weird behaviour caused by Textual CSS. All the code **AND TEXT** is written by me and nothing is copied over or written directly into my files by AI.