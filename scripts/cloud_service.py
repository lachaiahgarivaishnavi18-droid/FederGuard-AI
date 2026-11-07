"""Container entrypoint: initialize volume ownership, then drop privileges."""
import os
from pathlib import Path
import socket
import uvicorn

data=Path('/data')
data.mkdir(exist_ok=True)
if os.geteuid()==0:
    os.chown(data,10001,10001)
    os.setgid(10001)
    os.setuid(10001)

kind=os.getenv('SERVICE_KIND','backend')
if kind=='bank':
    os.environ.setdefault('BANK_DATA_DIR','/data/local')
    app='bank_clients.node:app'
else:
    os.environ.setdefault('DATABASE_URL','sqlite:////data/coordinator.db')
    app='backend.app.main:app'

# Explicit dual-stack socket supports both Railway private IPv6 and public IPv4.
server_socket=socket.socket(socket.AF_INET6,socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
server_socket.setsockopt(socket.IPPROTO_IPV6,socket.IPV6_V6ONLY,0)
server_socket.bind(('::',int(os.getenv('PORT','8000'))))
server_socket.listen(128)
server=uvicorn.Server(uvicorn.Config(app,log_level='info'))
server.run(sockets=[server_socket])
