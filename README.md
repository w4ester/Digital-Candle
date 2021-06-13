# Digital-Candle

A web-based vigil candle where people light candles as a form of presence and solidarity. Real-time via Flask-SocketIO. Built during the supply chain disruptions of early 2021, when the physical beacon concept had to go digital.

## Why This Exists

In 2018, Share-Your-Light made NeoPixel garments that turned people into walking beacons. In 2020, Window-Beacon put an amber light in a windowsill to signal "I am here" to passing neighbors. Both projects depended on hardware -- LEDs, microcontrollers, addressable strips.

By January 2021, supply chains made that hardware impossible to source. NeoPixels were backordered for months. Microcontrollers were sold out everywhere. The physical light was not an option.

But the idea behind it -- being present, signaling solidarity, showing someone that you are thinking of them -- that did not need hardware. It needed a browser.

Digital-Candle is a web page where people gather to light candles together. You create a vigil, share the link, and anyone who visits can light a candle. Everyone watching sees new candles appear in real time. A presence counter shows how many people are there right now.

Our neighborhood used it during isolation. Memorial vigils when someone passed. Solidarity vigils when the news was heavy. Hope vigils on particularly long weeks. The candles burn for 24 hours and then fade out, like real ones.

## How It Works

### Candle Lifecycle
1. Someone clicks "Light a Candle" on a vigil page
2. A new candle appears with a flickering CSS flame animation
3. Everyone watching the vigil sees it appear instantly (SocketIO)
4. The candle burns for 24 hours
5. After 24 hours, the candle fades out and disappears

### Vigils
A vigil is a named collection of candles. Each vigil has:
- **Name** -- what this gathering is for
- **Theme** -- memorial, celebration, solidarity, or hope
- **Dedication** -- an optional message explaining the purpose
- **Presence counter** -- how many people are watching right now

### Real-Time
Flask-SocketIO handles WebSocket connections. Each vigil is a SocketIO room. When someone lights a candle, the event broadcasts only to people watching that vigil. Presence is tracked by session ID in a set (not a counter -- counters can go negative on disconnect edge cases).

### Storage
Started with SQLite. Hit locking problems with 5 concurrent users. Migrated to Redis. See `experiments/sqlite_to_redis_notes.md` for the full story. Redis solved the locking, added TTL for automatic candle expiration, and pub/sub for potential multi-process scaling.

### Rate Limiting
After someone lit 500 candles in 2 minutes, added rate limiting: max 10 candles per minute per IP address.

## Project Structure

```
Digital-Candle/
  candle/
    candle.py          -- candle state: create, light, expiration, rate limiting
    vigil.py           -- vigil management: create, themes, dedications, stats
    store_sqlite.py    -- SQLite backend (original, still works as fallback)
    store_redis.py     -- Redis backend (default, handles concurrent access)
  web/
    app.py             -- Flask + SocketIO server, routes, events
    templates/
      index.html       -- vigil page with candle grid and presence counter
      create.html      -- create vigil form with themes
    static/
      style.css        -- dark theme, candle gold accents, flame animations
      candle.js         -- client SocketIO, flame triggers, presence updates
  experiments/
    sqlite_to_redis_notes.md   -- migration pain and solutions
    socketio_scaling_notes.md  -- connection limits, reconnection, pub/sub
  requirements.txt
  deploy.sh
```

## Quick Start

### With Redis (recommended)
```bash
# Install Redis
sudo apt-get install redis-server
sudo systemctl start redis

# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run
python web/app.py --store redis --port 5000
```

### With SQLite (no Redis needed)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python web/app.py --store sqlite --port 5000
```

Open http://localhost:5000 to see active vigils or create a new one.

## Connections

This project is part of a series exploring how technology can signal presence and build community connection:

- **Share-Your-Light** (2018) -- NeoPixel garments made light wearable. Digital-Candle makes light shareable. When supply chains made hardware impossible, the light went digital.
- **Window-Beacon** (2020) -- Amber beacon in a windowsill. Digital candle in a browser. Same signal -- "I am here."
- **SafeChat-Router** (2020) -- Taught that simple fallbacks beat complex systems. SQLite was the simple fallback. Redis was necessary growth. Same lesson: start simple, scale when the pain is real.
- **Smart Pillbox** (2017) -- Reminded you to take meds. Digital-Candle reminds you that someone is thinking of you.

## Lessons Learned

1. **Supply chain is a design constraint.** When hardware is unavailable, the core idea has to survive without it. The light was never about LEDs -- it was about presence.

2. **SQLite breaks under concurrent WebSocket writes.** WAL mode helps but does not solve the fundamental problem. If your app has real-time concurrent writes, plan for something beyond SQLite.

3. **Redis TTL is perfect for ephemeral data.** Candles that expire on their own, with no background cleanup job, using Redis key expiration. The simplest solution to a problem I was overcomplicating.

4. **Track presence with sets, not counters.** Counters can go negative on disconnect edge cases. Sets cannot. `discard()` on a set is a no-op if the element is not there.

5. **Exponential backoff is not optional.** Immediate reconnection on disconnect causes retry storms that can take down the server. Let Socket.IO handle reconnection with its built-in backoff.

6. **CSS animations on mobile need `transform`, not `box-shadow`.** Box-shadow animations cause frame drops on mobile Safari. Transform-based animations are GPU-accelerated and smooth.

7. **Rate limiting comes from real abuse.** Did not add it until someone actually lit 500 candles in 2 minutes. Community tools need community protections.
