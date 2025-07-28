import os
import subprocess
import textwrap


def run_command(command):
    """Run a shell command and check if it succeeds."""
    result = subprocess.run(command, shell=True, check=True, text=True)
    return result


def install_dependencies():
    print("Installing dependencies...")
    run_command("sudo apt update")
    run_command(
        "sudo apt install -y nginx python3-pip python3-dev "
        "libssl-dev libffi-dev build-essential"
    )


def install_python_dependencies():
    print("Installing Python dependencies...")
    run_command("pip3 install websockets")


def configure_nginx():
    print("Configuring Nginx...")
    nginx_config = """
    server {
        listen 443 ssl;
        server_name your-domain.com;  # Replace with your domain
        ssl_certificate     /etc/letsencrypt/live/your-domain.com/fullchain.pem;  # noqa: E501
        ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;  # noqa: E501

        location /tunnel {
            proxy_pass http://127.0.0.1:9000;  # Forward WebSocket traffic
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "Upgrade";
            proxy_set_header Host $host;
            proxy_read_timeout 3600s;
        }
    }

    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$host$request_uri;
    }
    """
    with open("/etc/nginx/sites-available/default", "w") as f:
        f.write(nginx_config)

    run_command("sudo nginx -t")
    run_command("sudo systemctl restart nginx")


def install_ssl_certificates():
    print("Installing SSL certificates with Let's Encrypt (Certbot)...")
    run_command("sudo apt install -y certbot python3-certbot-nginx")
    run_command("sudo certbot --nginx -d your-domain.com")


def install_python_tunnel_server():
    print("Installing Python Tunnel Server...")
    tunnel_server_script = textwrap.dedent(
        """
        import asyncio
        import json

        import websockets

        active_lock = asyncio.Lock()

        async def bridge_connection(ws, reader, writer):
            if active_lock.locked():
                writer.close()
                await writer.wait_closed()
                return

            async with active_lock:
                await ws.send(json.dumps({"action": "connect"}))

                async def ws_to_tcp():
                    async for message in ws:
                        if isinstance(message, bytes):
                            writer.write(message)
                            await writer.drain()
                        else:
                            cmd = json.loads(message)
                            if cmd.get("action") == "close":
                                break

                async def tcp_to_ws():
                    while True:
                        data = await reader.read(4096)
                        if not data:
                            break
                        await ws.send(data)
                    await ws.send(json.dumps({"action": "close"}))

                await asyncio.gather(
                    ws_to_tcp(),
                    tcp_to_ws(),
                    return_exceptions=True,
                )

                writer.close()
                await writer.wait_closed()


        async def tunnel_handler(ws):
            registration = json.loads(await ws.recv())
            remote_port = registration.get("remote_port", 2022)

            server = await asyncio.start_server(
                lambda r, w: bridge_connection(ws, r, w),
                "0.0.0.0",
                remote_port,
            )
            print(f"Reverse tunnel listening on {remote_port}")

            async with server:
                await ws.wait_closed()


        async def main():
            async with websockets.serve(tunnel_handler, "127.0.0.1", 9000):
                print("WebSocket tunnel server started on port 9000.")
                await asyncio.Future()


        if __name__ == "__main__":
            asyncio.run(main())
        """
    )

    os.makedirs("/opt/tunnel", exist_ok=True)
    with open("/opt/tunnel/tunnel_server.py", "w") as f:
        f.write(tunnel_server_script)

    run_command("pip3 install websockets")


def start_services():
    print("Enabling and starting services...")
    run_command("sudo systemctl enable nginx")
    run_command("sudo systemctl start nginx")

    subprocess.Popen(["python3", "/opt/tunnel/tunnel_server.py"])


if __name__ == "__main__":
    install_dependencies()
    install_python_dependencies()
    configure_nginx()
    install_ssl_certificates()
    install_python_tunnel_server()
    start_services()
    print("Edge server setup complete.")
