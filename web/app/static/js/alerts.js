document.addEventListener('DOMContentLoaded', function() {
    const apiEndpoint = '/api/alerts';
    let limit = 10;
    let offset = 0;
    let hasMore = true;
    let currentSort = { column: null, direction: 'asc' };

    // Capture form submission event for advanced search
    document.getElementById('advancedSearchForm').addEventListener('submit', function(event) {
        event.preventDefault();

        // Get search form params
        let startDate = document.getElementById('startDate').value;
        let endDate = document.getElementById('endDate').value;
        const alertLevel = document.getElementById('alertLevel').value;
        const alertSource = document.getElementById('alertSource').value;

        // Reset the offset
        offset = 0;

        // Fetch alerts with new search params
        fetchSearchAlerts(startDate, endDate, alertLevel, alertSource);
    });

    // Fetch alerts from the backend (Initial load)
    async function fetchAlerts(loadMore = false) {
        try {
            const params = new URLSearchParams({ limit, offset });

            const response = await fetch(`${apiEndpoint}?${params}`);
            const data = await response.json();

            if (data && Array.isArray(data.alerts) && data.alerts.length > 0) {
                if (loadMore) {
                    appendToTable(data.alerts);
                } else {
                    renderTable(data.alerts);
                }
                hasMore = data.has_more;
            } else if (!loadMore) {
                showNoAlertsMessage();
                hasMore = false;
            }
            toggleLoadMoreOrResetButton();
        } catch (error) {
            showErrorMessage(error);
            console.error('Error fetching alerts:', error);
        }
    }

    // Fetch alerts from the backend with search params
    async function fetchSearchAlerts(startDate = '', endDate = '', alertLevel = '', alertSource = ''){
        try {
            const params = new URLSearchParams({
                limit: limit,
                offset: offset,
            });
            // Conditionally add params
            if (startDate) params.append('start', startDate);
            if (endDate) params.append('end', endDate);
            if (alertLevel) params.append('level', alertLevel);
            if (alertSource) params.append('source', alertSource);
            
            const searchApiEndpoint = '/api/search_alerts';
            const response = await fetch(`${searchApiEndpoint}?${params}`);
            const data = await response.json();

            if (data && Array.isArray(data.alerts) && data.alerts.length > 0) {
                renderTable(data.alerts);
                hasMore = data.has_more;
            } else {
                showNoAlertsMessage();
                hasMore = false;
            }
            toggleLoadMoreOrResetButton();
        } catch (error) {
            showErrorMessage(error);
            console.error('Error fetching searched alerts:', error);
        }
    }
    // Show Error Message
    function showErrorMessage(message){
        const tableBody = document.querySelector("table tbody");
        tableBody.innerHTML = "";  // Clear the table if needed

        const errorRow = document.createElement("tr");
        const errorCell = document.createElement("td");
        errorCell.colSpan = 4;  // Span across all columns
        errorCell.textContent = message || "An error occurred while fetching alerts!";
        errorCell.classList.add("text-center", "text-danger");  // Center the text
        errorRow.appendChild(errorCell);
        tableBody.appendChild(errorRow);
    } 

    // Show a "No Alerts Available" message only on the initial load
    function showNoAlertsMessage() {
        const tableBody = document.querySelector("table tbody");
        tableBody.innerHTML = "";  // Clear the table if needed

        const noAlertsRow = document.createElement("tr");
        const noAlertsCell = document.createElement("td");
        noAlertsCell.colSpan = 4;  // Span across all columns
        noAlertsCell.textContent = "No alerts during this time!";
        noAlertsCell.classList.add("text-center");  // Center the text
        noAlertsRow.appendChild(noAlertsCell);
        tableBody.appendChild(noAlertsRow);
    }

    // Load more and Reset button Logic
    function toggleLoadMoreOrResetButton() {
        const loadMoreButton = document.getElementById('loadMoreBtn');
        const resetButton = document.getElementById('resetBtn');

        if (hasMore) {
            loadMoreButton.style.display = 'block';
            resetButton.style.display = 'none';
        } else {
            loadMoreButton.style.display = 'none';
            resetButton.style.display = 'block';
        }
        if (!hasMore && !alert.length) {
            loadMoreButton.style.display = 'none';
            resetButton.style.display = 'none';
        }
    }

    // Function to reset the table to the first 10 alerts
    function resetTable(){
        const tableBody = document.querySelector("table tbody");
        const rows = tableBody.querySelectorAll('tr');
        rows.forEach((row, index) => {
            if (index >= 10){
                row.remove();
            }
        });
        offset = 10;
        hasMore = true;
        toggleLoadMoreOrResetButton();
    }
    function renderTable(alerts){
        const tableBody = document.querySelector("table tbody");
        tableBody.innerHTML = "";  // Clear the table if needed
        appendToTable(alerts);
    }

    // Append alerts to the table (used for the "Load More" functionality)
    function appendToTable(alerts){
        const tableBody = document.querySelector("table tbody");
        alerts.forEach(alert => {
            const row = document.createElement("tr");

            // Timestamp 
            const timestampCell = document.createElement("td");
            timestampCell.textContent = new Date(alert.timestamp).toLocaleString();
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

            tableBody.appendChild(row);
        });
        toggleLoadMoreOrResetButton();
    }
    // Sort the table by column (timestamp, source, level, or value)
    function sortTable(columnIndex, type = 'string') {
        const table = document.querySelector("table");
        const rows = Array.from(table.querySelectorAll("tbody tr"));
        
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
    
        if (currentSort.column === columnIndex && currentSort.direction === 'asc') {
            sortedRows.reverse();
            currentSort.direction = 'desc';
            document.querySelectorAll("th")[columnIndex].classList.add("sorted-desc");
        } else {
            currentSort.direction = 'asc';
            document.querySelectorAll("th")[columnIndex].classList.add("sorted-asc");
        }
    
        currentSort.column = columnIndex;
    
        const tableBody = table.querySelector("tbody");
        tableBody.innerHTML = "";
        sortedRows.forEach(row => tableBody.appendChild(row));
    }
    // Add click event listener to the table headers
    document.querySelectorAll("th").forEach((header, index) => {
        header.addEventListener("click", () => {
            if (index === 0) {
                sortTable(index, 'date');
            } else if (index === 3) {
                sortTable(index, 'string');
            } else {
                sortTable(index, 'string');
            }
        });
    });
    document.getElementById('loadMoreBtn').addEventListener('click', function() {
        offset += limit;
        fetchAlerts(true);
    });
    document.getElementById('resetBtn').addEventListener('click', function() {
        resetTable();
    });
    fetchAlerts();
});