document.addEventListener('DOMContentLoaded', function() {
    const apiEndpoint = '/api/alerts';
    let limit = 10;
    let offset = 0;
    let hasMore = true;
    let currentSort = { column: null, direction: 'asc' };

    // Fetch alerts from the backend
    async function fetchAlerts(loadMore = false) {
        try {
            const params = new URLSearchParams({
                limit: limit,
                offset: offset
            });

            const response = await fetch(`${apiEndpoint}?${params}`);
            const data = await response.json();

            // Log the API response for debugging purposes
            console.log("API response:", data);

            // Check if data contains an alerts array, otherwise handle "No alerts" case
            if (data && Array.isArray(data.alerts) && data.alerts.length > 0) {
                if (loadMore) {
                    appendToTable(data.alerts);
                } else {
                    renderTable(data.alerts);
                }
                hasMore = data.has_more;  // Update hasMore status for Load More button
            } else if (!loadMore) {
                // Only show the "No alerts available" message if it's the first load
                showNoAlertsMessage();
                hasMore = false;
            }

            // Handle the Load More and Reset button visibility
            toggleLoadMoreOrResetButton();
        } catch (error) {
            console.error("Error fetching alerts:", error);
        }
    }

    // Show a "No Alerts Available" message only on the initial load
    function showNoAlertsMessage() {
        const tableBody = document.querySelector("table tbody");
        tableBody.innerHTML = "";  // Clear the table if needed

        const noAlertsRow = document.createElement("tr");
        const noAlertsCell = document.createElement("td");
        noAlertsCell.colSpan = 4;  // Span across all columns
        noAlertsCell.textContent = "No alerts available.";
        noAlertsCell.classList.add("text-center");  // Center the text
        noAlertsRow.appendChild(noAlertsCell);
        tableBody.appendChild(noAlertsRow);
    }

    // Toggle between Load More and Reset button based on hasMore
    function toggleLoadMoreOrResetButton() {
        const loadMoreButton = document.getElementById('loadMoreBtn');
        const resetButton = document.getElementById('resetBtn');

        if (hasMore) {
            loadMoreButton.style.display = 'block';  // Show "Load More" button
            resetButton.style.display = 'none';  // Hide "Reset" button
        } else {
            loadMoreButton.style.display = 'none';  // Hide "Load More" button
            resetButton.style.display = 'block';  // Show "Reset" button
        }
    }

    // Function to reset the table to the first 10 alerts
    function resetTable() {
        const tableBody = document.querySelector("table tbody");
        const rows = Array.from(tableBody.querySelectorAll('tr'));

        // Keep only the first 10 rows, remove the rest
        rows.forEach((row, index) => {
            if (index >= 10) {
                row.remove();
            }
        });

        // Set hasMore back to true so the user can load more again
        offset = 10;
        hasMore = true;
        toggleLoadMoreOrResetButton();  // Show the "Load More" button again
    }

    function renderTable(alerts) {
        const tableBody = document.querySelector("table tbody");
        tableBody.innerHTML = "";  // Clear table before rendering new rows

        appendToTable(alerts);
    }

    // Append alerts to the table (used for the "Load More" feature)
    function appendToTable(alerts) {
        const tableBody = document.querySelector("table tbody");

        alerts.forEach(alert => {
            const row = document.createElement("tr");

            // Timestamp
            const timestampCell = document.createElement("td");
            timestampCell.textContent = new Date(alert.timestamp).toLocaleString();  // Format timestamp
            row.appendChild(timestampCell);

            // Source
            const sourceCell = document.createElement("td");
            sourceCell.textContent = alert.source;
            row.appendChild(sourceCell);

            // Level
            const levelCell = document.createElement("td");
            levelCell.textContent = alert.level;
            levelCell.classList.add("alert-level", alert.level.toLowerCase());
            row.appendChild(levelCell);

            // Value
            const valueCell = document.createElement("td");
            valueCell.textContent = alert.value;
            row.appendChild(valueCell);

            // Append the row to the table
            tableBody.appendChild(row);
        });

        // After appending alerts, check if there are more to load
        toggleLoadMoreOrResetButton();
    }

    // Sort the table by column (timestamp, source, level, or value)
    function sortTable(columnIndex, type = 'string') {
        const table = document.querySelector("table");
        const rows = Array.from(table.querySelectorAll("tbody tr"));
        
        // Remove previous sort direction arrows
        document.querySelectorAll("th").forEach(th => th.classList.remove("sorted-asc", "sorted-desc"));
    
        const sortedRows = rows.sort((a, b) => {
            const cellA = a.cells[columnIndex].textContent;
            const cellB = b.cells[columnIndex].textContent;
    
            if (type === 'number') {
                return parseFloat(cellA) - parseFloat(cellB);
            } else if (type === 'date') {
                return new Date(cellA) - new Date(cellB);
            } else {
                return cellA.localeCompare(cellB);
            }
        });
    
        // If sorting direction is descending, reverse the sorted array
        if (currentSort.column === columnIndex && currentSort.direction === 'asc') {
            sortedRows.reverse();
            currentSort.direction = 'desc';
            document.querySelectorAll("th")[columnIndex].classList.add("sorted-desc");  // Add descending arrow
        } else {
            currentSort.direction = 'asc';
            document.querySelectorAll("th")[columnIndex].classList.add("sorted-asc");  // Add ascending arrow
        }
    
        currentSort.column = columnIndex;
    
        // Remove existing rows and append sorted rows
        const tableBody = table.querySelector("tbody");
        tableBody.innerHTML = "";
        sortedRows.forEach(row => tableBody.appendChild(row));
    }

    // Add click event listeners to the table headers for sorting
    document.querySelectorAll("th").forEach((header, index) => {
        header.addEventListener("click", () => {
            if (index === 0) {  // Timestamp column (Date sorting)
                sortTable(index, 'date');
            } else if (index === 3) {  // Value column (String sorting)
                sortTable(index, 'string');
            } else {  // String sorting for Source and Level columns
                sortTable(index, 'string');
            }
        });
    });

    // Load More button click event
    document.getElementById('loadMoreBtn').addEventListener('click', function () {
        offset += limit;  // Increment the offset for pagination
        fetchAlerts(true);  // Load more alerts
    });

    // Reset button click event
    document.getElementById('resetBtn').addEventListener('click', function () {
        resetTable();  // Reset the table back to the first 10 alerts
    });

    // Initial fetch of alerts
    fetchAlerts();
});
