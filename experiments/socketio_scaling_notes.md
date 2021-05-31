# SocketIO Scaling Notes

Notes on Flask-SocketIO connection behavior, scaling issues,
and solutions found while building Digital-Candle.

## Connection Limits

With eventlet async mode, a single server process handles hundreds
of WebSocket connections. Tested up to ~200 concurrent watchers
on a small VPS without issues.

The bottleneck is not connections but events. When 50 people are
all lighting candles at the same vigil, every light event broadcasts
to all 50 connections. That is 50 emit calls per candle lit.

## Rooms

Flask-SocketIO rooms are the key scaling tool. Each vigil gets its
own room. Events only broadcast to people watching that specific vigil.

```python
join_room(vigil_id)
emit("candle_lit", data, room=vigil_id)
```

Without rooms, every connected client would receive every event
from every vigil. Rooms keep the broadcast targeted.

## Reconnection

### First Attempt: Immediate Retry
Tried reconnecting immediately on disconnect:
```javascript
socket.on("disconnect", function() {
    socket.connect();  // BAD
});
```

This caused retry storms. If the server goes down briefly, every
client tries to reconnect at the same instant. The server comes
back up and gets hammered by 100 simultaneous connection attempts.

### Solution: Exponential Backoff
```javascript
var reconnectDelay = 1000;
var maxReconnectDelay = 30000;

socket = io({
    reconnectionDelay: reconnectDelay,
    reconnectionDelayMax: maxReconnectDelay
});
```

Socket.IO has built-in reconnection with jitter. Let it handle it.
Do not override with manual reconnect logic.

## Presence Tracking

Tracking how many people are watching a vigil is harder than expected.

### The Negative Count Bug
Browser tab close does not always fire the "leave_vigil" event.
The tab just goes away. The "disconnect" event fires but only
after a timeout.

If we decrement presence on "leave_vigil" and also on "disconnect",
we can double-decrement. Presence count goes negative.

Fix: Track presence by session ID in a set. On disconnect, remove
the session ID from all vigil sets. Count the set size. Cannot go
negative because removing a non-existent element from a set is a no-op.

```python
presence = {}  # { vigil_id: set(session_ids) }

@socketio.on("disconnect")
def handle_disconnect():
    for vigil_id in list(presence.keys()):
        presence[vigil_id].discard(request.sid)
        count = len(presence[vigil_id])
        socketio.emit("presence_update", {"count": count}, room=vigil_id)
```

## Redis Pub/Sub for Multi-Process

Single process works fine for moderate load. But if we needed to
scale to multiple server processes (behind a load balancer), SocketIO
events need to cross process boundaries.

Redis pub/sub handles this:
```python
socketio = SocketIO(app, message_queue="redis://")
```

Flask-SocketIO's Redis message queue means emit() in one process
gets delivered to clients connected to other processes.

Did not end up needing multi-process for our community usage, but
the pub/sub infrastructure is there via store_redis.py.

## Eventlet Conflicts

Eventlet monkey-patching conflicts with Flask's debug mode reloader.
The reloader forks a new process, and eventlet's monkey-patching
does not survive the fork cleanly.

Fix: Do not use debug=True with eventlet in production. For development,
use debug=True without eventlet (falls back to threading mode).

In deploy.sh, we run without debug:
```bash
python web/app.py --store redis --port 5000
```

## Lessons

- Rooms are essential. Without them, broadcast cost grows linearly
  with total connected clients.
- Exponential backoff is not optional. Retry storms are real.
- Track presence with sets, not counters. Sets cannot go negative.
- Redis pub/sub is the answer for multi-process SocketIO.
- Eventlet and Flask debug mode do not play well together.
