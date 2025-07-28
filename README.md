# HTTPS Tunnel

This project creates a simple HTTPS tunnel to forward SSH connections through a WebSocket server running behind Nginx on port 443.

## Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. (Optional) Run `edge_installer.py` on your server to install Nginx and the tunnel service.

## Usage


Run the client to establish a reverse SSH tunnel. The tunnel forwards your local SSH port (22) to a port on the edge server (default 2022):
```bash
python3 client.py
```
The client connects to the configured edge server over HTTPS and exposes your local SSH server. Any host that connects to `edge_server:2022` will reach your local port 22.


## License

This project is licensed under the MIT License.

