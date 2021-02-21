/**
 * Digital-Candle client-side candle interactions.
 * Light button and basic animation triggers.
 */

document.addEventListener("DOMContentLoaded", function() {
    var lightBtn = document.getElementById("light-btn");
    if (lightBtn) {
        lightBtn.addEventListener("click", function() {
            // For now, just submit the form
            var vigilId = lightBtn.getAttribute("data-vigil");
            if (vigilId) {
                var form = document.createElement("form");
                form.method = "POST";
                form.action = "/vigil/" + vigilId + "/light";
                document.body.appendChild(form);
                form.submit();
            }
        });
    }
});
