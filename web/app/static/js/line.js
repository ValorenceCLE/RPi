document.addEventListener('DOMContentLoaded', async function () {
    const pathSegments = window.location.pathname.split('/');
    const pageName = pathSegments[pathSegments.length -1] || 'system'; // Default to system page

    const datasets = {
        system: [
            { displayName: 'Volts', fieldName: 'volts' },
            { displayName: 'Watts', fieldName: 'watts' },
            { displayName: 'Amps', fieldName: 'amps' }
        ],
        router: [
            { displayName: 'Volts', fieldName: 'volts' },
            { displayName: 'Watts', fieldName: 'watts' },
            { displayName: 'Amps', fieldName: 'amps' }
        ],
        camera: [
            { displayName: 'Volts', fieldName: 'volts' },
            { displayName: 'Watts', fieldName: 'watts' },
            { displayName: 'Amps', fieldName: 'amps' }
        ],
        network: [
            { displayName: 'RSRP', fieldName: 'rsrp' },
            { displayName: 'RSRQ', fieldName: 'rsrq' },
            { displayName: 'SINR', fieldName: 'sinr' }
        ]
    };
    
    const currentPageData = datasets[pageName] || datasets['system']; // Default to system data
    let chart = null;



    function renderLineChart(data, yMin, yMax) {
        chart = Highcharts.chart('container-line-chart', {
            time: {
                useUTC: false // Ensure Highcharts uses UTC and converts to local time
            },
            boost: {
                useGPUTranslations: true, // Use GPU translations for performance
                usePreallocated: true     // Preallocate arrays for faster rendering
            },
            chart: {
                type: 'spline', // Use 'spline' for smoother lines
                backgroundColor: '#fff',
                zoomType: 'x' // Enable zooming on the x-axis
            },
            title: {
                text: null // Remove chart title
            },
            xAxis: {
                type: 'datetime',
                labels: {
                    style: {
                        color: '#333' // Dark color for labels
                    },
                    formatter: function () {
                        // Format the label to show local time in a readable format
                        return Highcharts.dateFormat('%m/%d %I:%M%p', this.value);
                    }
                },
                title: {
                    text: 'Timestamp'
                }
            },
            yAxis: {
                title: {
                    text: null // Remove y-axis title
                },
                labels: {
                    style: {
                        color: '#333' // Dark color for labels
                    }
                },
                allowDecimals: true,
                min: yMin, // Set y-axis minimum
                max: yMax, // Set y-axis maximum
                minPadding: 0.05,
                maxPadding: 0.05
            },
            tooltip: {
                shared: true, // Show a single tooltip for all series
                crosshairs: true, // Show a vertical line for each data point
                formatter: function () {
                    let tooltip = `<b>${Highcharts.dateFormat('%m/%d %I:%M%p', this.x)}</b><br/>`;
                    this.points.forEach((point) => {
                        tooltip += `<span style="color:${point.color}">\u25CF</span> ${point.series.name}: <b>${point.y}</b><br/>`;
                    });
                    return tooltip;
                }
            },
            plotOptions: {
                series: {
                    marker: {
                        enabled: false // Disable markers for each data point
                    },
                    turboThreshold: 0, // Disable the turbo threshold
                    boostThreshold: 1,  // Activate boost for large datasets
                    dataGrouping: {
                        enabled: true,
                        approximation: 'average',
                        groupPixelWidth: 10
                    }
                }
            },
            series: data, // Load data dynamically
            credits: {
                enabled: false
            },
            legend: {
                enabled: true,
                layout: 'horizontal',
                align: 'center',
                verticalAlign: 'bottom',
            },
            exporting: {
                enabled: true
            },
            responsive: {
                rules: [{
                    condition: {
                        maxWidth: 800
                    },
                    chartOptions: {
                        legend: {
                            enabled: false
                        }
                    }
                }]
            }
        });
    }

    // Helper function to clean timestamps
    function cleanTimestamp(timestamp) {
        return timestamp.replace(/(\.\d{3})\d+/, '$1');
    }

    function checkTimestamp(utcTimestamp){
        const date = new Date(utcTimestamp);
        if (utcTimestamp.endsWith('Z') || utcTimestamp.includes('+00:00')) {
            const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
            return localDate
        } else {
            return date
        }
    }

    // Fetch the data from the server
    async function fetchData(timeFrame) {
        try {
            const response = await fetch(`/${pageName}/data/${timeFrame}`);
            const result = await response.json();
            if (result.error){
                if(chart) {
                    chart.setTitle({ text: 'Error Fetching Data' });
                } else{
                    renderLineChart([], null, null);
                }
                return;
            }
            const seriesData = currentPageData.map(field => ({
                name: field.displayName,
                data: []
            }));
            result.data.forEach(entry => {
                const cleanedTimestamp = cleanTimestamp(entry.timestamp);
                const timestamp = checkTimestamp(cleanedTimestamp).getTime();
                if (isNaN(timestamp)) {
                    console.warn(`Invalid timestamp after cleaning: ${cleanedTimestamp}`);
                    return; // Skip invalid timestamps
                }
                currentPageData.forEach((field, index) => {
                    const value = entry[field.fieldName.toLowerCase()];
                    if (value !== undefined && value !== null) {
                        const numericValue = parseFloat(value);
                        if (isNaN(numericValue)) {
                            console.warn(`Invalid value for ${field.displayName}: ${value}`);
                            return; // Skip invalid values
                        }
                        seriesData[index].data.push([timestamp, numericValue]);
                    }
                });
            });

            // Calculate global yMin and yMax
            const allValues = seriesData.flatMap(series => series.data.map(point => point[1]));
            const yMin = Math.min(...allValues);
            const yMax = Math.max(...allValues);

            // Add a buffer to yMin and yMax for better visualization
            const buffer = (yMax - yMin) * 0.05;
            const adjustedYMin = yMin - buffer;
            const adjustedYMax = yMax + buffer;

            // Render the line chart with new data
            if (chart){
                seriesData.forEach((series, index) => {
                    if (chart.series[index]) {
                        chart.series[index].setData(series.data, false, false, false);
                    } else {
                        chart.addSeries(series, false, false);
                    }
                });
                // Update yAxis extremes
                chart.yAxis[0].setExtremes(adjustedYMin, adjustedYMax, false);
                chart.redraw();
            } else {
                renderLineChart(seriesData, adjustedYMin, adjustedYMax);
            }
        } catch (error) {
            console.error(error);
            if (chart) {
                chart.setTitle({ text: 'Error Fetching Data' });
            } else {
                renderLineChart([], null, null);
            }
        }
    }

    document.querySelectorAll('.dropdown-item').forEach(item => {
        item.addEventListener('click', function () {
            const timeFrame = this.getAttribute('data-value');
            fetchData(timeFrame);
        });
    });
    fetchData('1h');
});
