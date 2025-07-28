# HTTPS Tunnel

This project creates a simple HTTPS tunnel to forward SSH connections through a WebSocket server.

## Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. (Optional) Run `edge_installer.py` on your server to install Nginx and the tunnel service.

## Usage

Run the client to establish a reverse SSH tunnel:
```bash
python3 client.py
```
The client connects to the configured edge server and exposes your local SSH server over WebSocket.

## License

This project is licensed under the MIT License.

