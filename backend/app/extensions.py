from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO

db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
jwt = JWTManager()
bcrypt = Bcrypt()
from flask import request

limiter = Limiter(
    key_func=get_remote_address,
    default_limits_exempt_when=lambda: request.method == "OPTIONS",
)
# threading mode: works on Windows/macOS/Linux with no extra server setup.
# WebSocket upgrades aren't available in this mode, so Socket.IO uses long-polling,
# which is plenty for WebRTC signalling.
socketio = SocketIO(async_mode="threading")
