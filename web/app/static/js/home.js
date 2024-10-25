window.addEventListener("load", () => {
    clock();

    function clock() {
        const today = new Date();

        // Get date components
        const month = (today.getMonth() + 1).toString().padStart(2, "0");
        const day = today.getDate().toString().padStart(2, "0");
        const year = today.getFullYear();

        // Get time components
        let hour = today.getHours();
        const minute = today.getMinutes().toString().padStart(2, "0");

        // Determine AM/PM and convert to 12-hour format
        const ampm = hour >= 12 ? "PM" : "AM";
        hour = hour % 12 || 12; // Converts hour '0' to '12'

        // Construct date and time strings
        const date = `${month}/${day}/${year}`;
        const time = `${hour}:${minute} ${ampm}`;

        // Update the clock display
        document.getElementById("clock").innerHTML = `${date} ${time}`;

        // Update the clock every second
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