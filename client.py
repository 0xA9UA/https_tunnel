import asyncio
import websockets
import json
import socket

# Replace this with the edge server domain and tunnel path
EDGE_SERVER = "wss://your-domain.com/tunnel"
AUTH_TOKEN = "your-secure-token"  # Token for authentication

async def register_reverse_ssh(ws, local_ssh_port):
    # Send the reverse port registration message to the server
    registration_message = {
        "action": "register_reverse",
        "remote_port": local_ssh_port
    }
    await ws.send(json.dumps(registration_message))
    print(f"Reverse SSH port {local_ssh_port} registered successfully.")

async def handle_ssh_tunnel(ws, local_ssh_port):
    """Handles the bi-directional tunnel between WebSocket and local SSH."""
    # Create a TCP socket to the local SSH server (port 22)
    local_ssh_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    local_ssh_socket.connect(('127.0.0.1', 22))  # Connect to local SSH port

    # Open a read-write loop between the WebSocket and local SSH
    while True:
        # Wait for data from WebSocket (client side)
        ws_data = await ws.recv()
        # Forward data to the local SSH socket
        local_ssh_socket.sendall(ws_data)

        # Wait for data from the local SSH socket (SSH server side)
        ssh_data = local_ssh_socket.recv(4096)
        if not ssh_data:
            break
        # Forward the response to the WebSocket (client side)
        await ws.send(ssh_data)

    local_ssh_socket.close()

async def main():
    # Connect to the edge server WebSocket
    async with websockets.connect(EDGE_SERVER, extra_headers={"Authorization": AUTH_TOKEN}) as ws:
        # Register reverse SSH port
        await register_reverse_ssh(ws, 2022)  # Replace 2022 with desired port
        print("Starting SSH tunnel...")
        # Forward data between WebSocket and local SSH server
        await handle_ssh_tunnel(ws, 2022)

if __name__ == "__main__":
    asyncio.run(main())
