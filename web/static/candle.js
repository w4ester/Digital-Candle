/**
 * Digital-Candle client-side SocketIO and candle interactions.
 */

var socket = null;
var currentVigil = null;

function initVigil(vigilId) {
    currentVigil = vigilId;

    socket = io();

    socket.on("connect", function() {
        console.log("Connected to server");
        socket.emit("join_vigil", { vigil_id: vigilId });
    });

    socket.on("candle_lit", function(data) {
        addCandleToGrid(data);
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
