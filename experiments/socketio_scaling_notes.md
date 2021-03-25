# SocketIO Scaling Notes

Notes on Flask-SocketIO connection behavior and scaling.

## Connection Limits

With eventlet async mode, a single process handles hundreds
of WebSocket connections. The bottleneck is not connections
but event broadcasting.

## Rooms

Flask-SocketIO rooms keep broadcasts targeted to specific vigils.
Without rooms, every client receives every event.

## Reconnection

TODO: Document reconnection findings. Immediate retry is bad.
Exponential backoff is required.
