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
        import socket

        import websockets

        async def register_reverse_ssh(ws, local_ssh_port):
            registration_message = {
                "action": "register_reverse",
                "remote_port": local_ssh_port,
            }
            await ws.send(json.dumps(registration_message))
            print(f"Reverse SSH port {local_ssh_port} registered.")

        async def handle_ssh_tunnel(ws, local_ssh_port):
            loop = asyncio.get_running_loop()
            local_ssh_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM
            )
            local_ssh_socket.setblocking(False)
            await loop.sock_connect(
                local_ssh_socket, ("127.0.0.1", local_ssh_port)
            )

            async def ws_to_ssh():
                async for data in ws:
                    if isinstance(data, str):
                        data = data.encode()
                    await loop.sock_sendall(local_ssh_socket, data)

            async def ssh_to_ws():
                while True:
                    data = await loop.sock_recv(local_ssh_socket, 4096)
                    if not data:
                        break
                    await ws.send(data)

            await asyncio.gather(ws_to_ssh(), ssh_to_ws())

        async def main():
            async with websockets.serve(handle_ssh_tunnel, "127.0.0.1", 9000):
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
