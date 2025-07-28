import subprocess
import os

# Helper function to run commands
def run_command(command):
    """Run a shell command and check if it succeeds."""
    result = subprocess.run(command, shell=True, check=True, text=True)
    return result

# Install necessary packages (Nginx, Python3, etc.)
def install_dependencies():
    print("Installing dependencies...")
    run_command("sudo apt update")
    run_command("sudo apt install -y nginx python3-pip python3-dev libssl-dev libffi-dev build-essential")

# Install Python dependencies
def install_python_dependencies():
    print("Installing Python dependencies...")
    run_command("pip3 install websockets")

# Configure Nginx
def configure_nginx():
    print("Configuring Nginx...")
    nginx_config = """
    server {
        listen 443 ssl;
        server_name your-domain.com;  # Replace with your domain
        ssl_certificate     /etc/letsencrypt/live/your-domain.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

        location /tunnel {
            proxy_pass http://127.0.0.1:9000;  # Forward WebSocket traffic to local Python server
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
    # Write the configuration to the Nginx site configuration file
    with open("/etc/nginx/sites-available/default", "w") as f:
        f.write(nginx_config)

    # Test and restart Nginx
    run_command("sudo nginx -t")
    run_command("sudo systemctl restart nginx")

# Install SSL certificates using Let's Encrypt (Certbot)
def install_ssl_certificates():
    print("Installing SSL certificates with Let's Encrypt (Certbot)...")
    run_command("sudo apt install -y certbot python3-certbot-nginx")
    run_command("sudo certbot --nginx -d your-domain.com")  # Replace with your domain

# Install the Python Tunnel Server
def install_python_tunnel_server():
    print("Installing Python Tunnel Server...")
    tunnel_server_script = """
    import asyncio
    import websockets
    import json
    import socket

    async def register_reverse_ssh(ws, local_ssh_port):
        registration_message = {
            "action": "register_reverse",
            "remote_port": local_ssh_port
        }
        await ws.send(json.dumps(registration_message))
        print(f"Reverse SSH port {local_ssh_port} registered.")

    async def handle_ssh_tunnel(ws, local_ssh_port):
        local_ssh_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        local_ssh_socket.connect(('127.0.0.1', 22))
        while True:
            ws_data = await ws.recv()
            local_ssh_socket.sendall(ws_data)
            ssh_data = local_ssh_socket.recv(4096)
            if not ssh_data:
                break
            await ws.send(ssh_data)
        local_ssh_socket.close()

    async def main():
        async with websockets.serve(handle_ssh_tunnel, "127.0.0.1", 9000):
            print("WebSocket tunnel server started on port 9000.")
            await asyncio.Future()  # Run forever

    if __name__ == "__main__":
        asyncio.run(main())
    """
    # Write the Python server script
    with open("/opt/tunnel/tunnel_server.py", "w") as f:
        f.write(tunnel_server_script)

    # Install the Python dependencies
    run_command("pip3 install websockets")

# Enable and start Nginx and the Python tunnel server
def start_services():
    print("Enabling and starting services...")
    run_command("sudo systemctl enable nginx")
    run_command("sudo systemctl start nginx")
    
    # Start the Python server
    subprocess.Popen(["python3", "/opt/tunnel/tunnel_server.py"])

if __name__ == "__main__":
    install_dependencies()
    install_python_dependencies()
    configure_nginx()
    install_ssl_certificates()
    install_python_tunnel_server()
    start_services()
    print("Edge server setup complete.")
