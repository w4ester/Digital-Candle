/**
 * Digital-Candle client-side SocketIO and candle animations.
 *
 * Handles real-time candle lighting, presence updates,
 * and connection status with exponential backoff on reconnect.
 */

var socket = null;
var currentVigil = null;
var reconnectDelay = 1000;  // Start at 1 second
var maxReconnectDelay = 30000;  // Cap at 30 seconds


function initVigil(vigilId) {
    currentVigil = vigilId;

    socket = io({
        reconnection: true,
        reconnectionDelay: reconnectDelay,
        reconnectionDelayMax: maxReconnectDelay,
        reconnectionAttempts: Infinity
    });

    socket.on("connect", function() {
        console.log("Connected to server");
        setConnectionStatus(true);
        reconnectDelay = 1000;  // Reset on successful connect

        socket.emit("join_vigil", { vigil_id: vigilId });
    });

    socket.on("disconnect", function() {
        console.log("Disconnected from server");
        setConnectionStatus(false);
    });

    socket.on("reconnect_attempt", function(attempt) {
        console.log("Reconnecting... attempt " + attempt);
    });

    socket.on("candle_lit", function(data) {
        addCandleToGrid(data);
    });

    socket.on("candle_expired", function(data) {
        removeCandleFromGrid(data.candle_id);
    });

    socket.on("presence_update", function(data) {
        updatePresenceCount(data.count);
    });

    socket.on("rate_limited", function(data) {
        showRateMessage(data.message);
    });

    // Light button handler
    var lightBtn = document.getElementById("light-btn");
    if (lightBtn) {
        lightBtn.addEventListener("click", function() {
            lightCandle();
        });
    }

    // Enter key in dedication field
    var dedicationInput = document.getElementById("dedication");
    if (dedicationInput) {
        dedicationInput.addEventListener("keypress", function(e) {
            if (e.key === "Enter") {
                lightCandle();
            }
        });
    }
}


function lightCandle() {
    if (!socket || !socket.connected) {
        showRateMessage("Not connected -- please wait");
        return;
    }

    var dedication = "";
    var dedicationInput = document.getElementById("dedication");
    if (dedicationInput) {
        dedication = dedicationInput.value.trim();
        dedicationInput.value = "";
    }

    socket.emit("light_candle", {
        vigil_id: currentVigil,
        dedication: dedication
    });
}


function addCandleToGrid(data) {
    var grid = document.getElementById("candle-grid");
    if (!grid) return;

    var candle = document.createElement("div");
    candle.className = "candle";
    candle.setAttribute("data-id", data.candle_id);

    var flame = document.createElement("div");
    flame.className = "flame";

    var flameInner = document.createElement("div");
    flameInner.className = "flame-inner";
    flame.appendChild(flameInner);

    var wax = document.createElement("div");
    wax.className = "wax";

    candle.appendChild(flame);
    candle.appendChild(wax);

    if (data.dedication) {
        var ded = document.createElement("div");
        ded.className = "candle-dedication";
        ded.textContent = data.dedication;
        candle.appendChild(ded);
    }

    // Add to beginning of grid
    if (grid.firstChild) {
        grid.insertBefore(candle, grid.firstChild);
    } else {
        grid.appendChild(candle);
    }
}


function removeCandleFromGrid(candleId) {
    var candle = document.querySelector('.candle[data-id="' + candleId + '"]');
    if (!candle) return;

    // Fade out animation
    candle.classList.add("fading");
    setTimeout(function() {
        if (candle.parentNode) {
            candle.parentNode.removeChild(candle);
        }
    }, 2000);
}


function updatePresenceCount(count) {
    var el = document.getElementById("presence-count");
    if (el) {
        el.textContent = count;
    }
}


function setConnectionStatus(connected) {
    var dot = document.getElementById("status-dot");
    if (!dot) return;

    if (connected) {
        dot.className = "status-dot connected";
    } else {
        dot.className = "status-dot reconnecting";
    }
}


function showRateMessage(message) {
    var el = document.getElementById("rate-msg");
    if (!el) return;

    el.textContent = message;
    el.style.display = "block";

    setTimeout(function() {
        el.style.display = "none";
    }, 3000);
}
