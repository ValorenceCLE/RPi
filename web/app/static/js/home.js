window.addEventListener("load", () => {
    clock();

    function clock() {
        const today = new Date();

        const month = today.getMonth() + 1;
        const day = today.getDate();
        const year = today.getFullYear();

        const hour = today.getHours();
        const minute = today.getMinutes();

        const hourTime = hour > 12 ? hour - 12 : hour;
        const ampm = hour < 12 ? "AM" : "PM";

        const date = `${month}/${day}/${year}`;
        const time = `${hourTime}:${minute} ${ampm}`;

        document.getElementById("clock").innerHTML = `${date} ${time}`;
        setTimeout(clock, 1000);
    }
});

async function updateBadge(name, status) {
    const badge = document.getElementById(`${name}Status`);
    badge.textContent = status === "on" ? "On" : status === "off" ? "Off" : "Running";
    badge.className = status === "on" ? "badge bg-success" :
                      status === "off" ? "badge bg-danger" :
                      "badge bg-warning";
}

async function controlRelay(name, action) {
    try {
        if (action === "run_5_min") {
            updateBadge(name.charAt(0).toUpperCase() + name.slice(1), "running");
        }

        const response = await fetch(`/relay/${name}/${action}`, { method: "POST" });
        const data = await response.json();

        if (data.status === "success") {
            if (action !== "run_5_min") {
                updateBadge(name.charAt(0).toUpperCase() + name.slice(1), action === "restart" ? "on" : action);
            }
        } else {
            console.error("Failed to control relay:", data);
        }
    } catch (error) {
        console.error("Error:", error);
    }
}

async function updateRelayStatuses() {
    try {
        const response = await fetch("/relay/status");
        const data = await response.json();
        Object.keys(data).forEach(relay => {
            updateBadge(relay.charAt(0).toUpperCase() + relay.slice(1), data[relay]);
        });
    } catch (error) {
        console.error("Error fetching relay statuses:", error);
    }
}

function startPolling() {
    updateRelayStatuses(); // Initial update on page load
    setInterval(updateRelayStatuses, 15000); // Poll every 15 seconds
}

document.addEventListener("DOMContentLoaded", startPolling);

document.getElementById("RestartRouter").addEventListener("click", () => controlRelay("router", "restart"));
document.getElementById("CamOn").addEventListener("click", () => controlRelay("camera", "on"));
document.getElementById("CamOff").addEventListener("click", () => controlRelay("camera", "off"));
document.getElementById("StrobeOn").addEventListener("click", () => controlRelay("strobe", "on"));
document.getElementById("StrobeOff").addEventListener("click", () => controlRelay("strobe", "off"));
document.getElementById("RunStrobe").addEventListener("click", () => controlRelay("strobe", "run_5_min"));
document.getElementById("FanOn").addEventListener("click", () => controlRelay("fan", "on"));
document.getElementById("FanOff").addEventListener("click", () => controlRelay("fan", "off"));
document.getElementById("RunFan").addEventListener("click", () => controlRelay("fan", "run_5_min"));

document.addEventListener("DOMContentLoaded", function() {
    fetch('/cellular')
        .then(response => response.json())
        .then(data => {
            // Check if the response contains quality data
            if (data.Quality) {
                document.getElementById('signal').textContent = "Signal Quality: " + data.Quality;
            } else {
                document.getElementById('signal').textContent = "Signal Quality: Data Unavailable";
            }
        })
        .catch(error => {
            console.error('Error fetching signal quality:', error);
            document.getElementById('signal').textContent = "Signal Quality: Error";
        });
});