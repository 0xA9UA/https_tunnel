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
    """Forward data between the server WebSocket and the local SSH port."""
    loop = asyncio.get_running_loop()
    local_sock = None
    reader_task = None

    async def read_local(sock):
        try:
            while True:
                data = await loop.sock_recv(sock, 4096)
                if not data:
                    break
                await ws.send(data)
        finally:
            await ws.send(json.dumps({"action": "close"}))

    try:
        async for message in ws:
            if isinstance(message, str):
                command = json.loads(message)
                if command.get("action") == "connect" and local_sock is None:
                    local_sock = socket.socket(
                        socket.AF_INET, socket.SOCK_STREAM
                    )
                    local_sock.setblocking(False)
                    await loop.sock_connect(
                        local_sock, ("127.0.0.1", local_ssh_port)
                    )
                    reader_task = asyncio.create_task(read_local(local_sock))
                elif command.get("action") == "close" and local_sock:
                    local_sock.close()
                    local_sock = None
                    if reader_task:
                        reader_task.cancel()
                        reader_task = None
            elif local_sock:
                await loop.sock_sendall(local_sock, message)
    finally:
        if local_sock:
            local_sock.close()
        if reader_task:
            reader_task.cancel()


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
