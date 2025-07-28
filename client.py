import asyncio
import json
import socket

import websockets

# Replace this with the edge server domain and tunnel path
EDGE_SERVER = "wss://your-domain.com/tunnel"
AUTH_TOKEN = "your-secure-token"  # Token for authentication


async def register_reverse_ssh(ws, remote_port):
    """Register a remote port for the reverse SSH tunnel."""
    registration_message = {
        "action": "register_reverse",
        "remote_port": remote_port,
    }
    await ws.send(json.dumps(registration_message))
    print(f"Reverse SSH port {remote_port} registered successfully.")


async def handle_ssh_tunnel(ws, local_ssh_port):
    """Handle the bidirectional tunnel between WebSocket and local SSH."""
    loop = asyncio.get_running_loop()
    local_ssh_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    local_ssh_socket.setblocking(False)
    await loop.sock_connect(local_ssh_socket, ("127.0.0.1", local_ssh_port))

    async def ws_to_ssh():
        try:
            async for data in ws:
                if isinstance(data, str):
                    data = data.encode()
                await loop.sock_sendall(local_ssh_socket, data)
        except websockets.ConnectionClosed:
            pass

    async def ssh_to_ws():
        try:
            while True:
                data = await loop.sock_recv(local_ssh_socket, 4096)
                if not data:
                    break
                await ws.send(data)
        finally:
            local_ssh_socket.close()

    await asyncio.gather(ws_to_ssh(), ssh_to_ws())


async def main():
    local_port = 22
    remote_port = 2022
    async with websockets.connect(
        EDGE_SERVER, extra_headers={"Authorization": AUTH_TOKEN}
    ) as ws:
        await register_reverse_ssh(ws, remote_port)
        print("Starting SSH tunnel...")
        try:
            await handle_ssh_tunnel(ws, local_port)
        except websockets.ConnectionClosed:
            print("WebSocket connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
