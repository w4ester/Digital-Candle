/**
 * Digital-Candle client-side SocketIO and candle interactions.
 * Uses exponential backoff for reconnection -- immediate retry
 * caused retry storms that overwhelmed the server.
 */

var socket = null;
var currentVigil = null;
var reconnectDelay = 1000;
var maxReconnectDelay = 30000;

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
        reconnectDelay = 1000;
        socket.emit("join_vigil", { vigil_id: vigilId });
    });

    socket.on("disconnect", function() {
        console.log("Disconnected from server");
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

    var lightBtn = document.getElementById("light-btn");
    if (lightBtn) {
        lightBtn.addEventListener("click", function() {
            socket.emit("light_candle", { vigil_id: vigilId });
        });
    }
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

    if (grid.firstChild) {
        grid.insertBefore(candle, grid.firstChild);
    } else {
        grid.appendChild(candle);
    }
}

function removeCandleFromGrid(candleId) {
    var candle = document.querySelector('.candle[data-id="' + candleId + '"]');
    if (!candle) return;
    candle.classList.add("fading");
    setTimeout(function() {
        if (candle.parentNode) {
            candle.parentNode.removeChild(candle);
        }
    }, 2000);
}

function updatePresenceCount(count) {
    var el = document.getElementById("presence-count");
    if (el) { el.textContent = count; }
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
