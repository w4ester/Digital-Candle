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
