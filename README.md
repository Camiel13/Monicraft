# Monicraft
---
Monicraft is a TUI-based application that makes it easier to monitor your rented or self-hosted Minecraft servers that run on the Pterodactyl panel (or some forked versions of it). It communicates through websockets and requests to the REST API to make it fast and responsive.

## Features
---
- **Real-Time Console Monitoring:** The server console is streamed directly into your interface and formatted with `RichLog`.
- **Command Execution:** Minecraft commands can be sent to the server, the server will execute them and the output will appear in the **console**.
- **Power Actions:** Power buttons allow you to start, stop, restart or kill your server whenever it's needed.
- **Resource Monitoring:** The sidebar shows the state, CPU usage and RAM usage of the server in real-time through websockets.
- **Chat Mode:** Makes it possible to just type messages, instead of having to add *say* to your command every time you want to send a message to your server.
- **Settings Page:** An interactive settings page where you're able to change your environment variables, which are then safely stored in `.env`. 
- **Mod Page:** An organized page where all the installed mods are shown, together with their size and the date and time they were last changed.
- **Player Manager:**
    - **Player List:** An overview of all the players on the server.
    - **Include Offline Player Toggle:** A toggle which toggles the visibility of offline players in the **Player List**.
    - **Kicking and Banning:** Ban or kick the selected player in the **Player List** with the option to add a reason. *kicking: online, banning: online/offline*
    - **Message Players:** Send private in-game messages to individual players without broadcasting to the entire server. *online*
    - **Change Gamemodes:** Change players' gamemodes easily through a clean selection pop-up.
    - **Statistics Viewer:** View all the stats of any player: General stats (play time, deaths, etc.), Entities (amount of entities killed) and Items (crafted, mined, used, broken, picked up, dropped). *online/offline*

---
# TODO:
!- Fix a bug where you suddenly select the first row of the table after rebuilding it
- Create a cache for offline players
- Add disk usage resource data
- Settings: Changing the loop delay
- Settings: Chat mode and message prefixes
- Make the GitHub workflow files
- Make an installation guide in the README