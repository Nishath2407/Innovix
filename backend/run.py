import os
from app import create_app
from app.extensions import socketio

app = create_app(os.environ.get("FLASK_ENV", "development"))

if __name__ == "__main__":
    # Using socketio.run so WebSocket (chat) support works in dev too.
    # allow_unsafe_werkzeug is fine for local development; production deploys
    # (Railway/Render) should run under eventlet/gunicorn instead, e.g.:
    #   gunicorn --worker-class eventlet -w 1 run:app
    socketio.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=app.config.get("DEBUG", False),
        allow_unsafe_werkzeug=True,
    )
