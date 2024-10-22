document.addEventListener('DOMContentLoaded', async function () {
    // Initialize WebSocket connection and gauge configurations
    const pageName = window.location.pathname.split('/').pop(); // Extract page name from URL

    // Fetch preset min/max values from the backend
    const response = await fetch(`/presets/${pageName}`);
    const presets = await response.json();

    // Define default gauge options
    const gaugeOptions = {
        chart: {
            type: 'solidgauge',
            backgroundColor: '#fff', // Light background
        },
        title: null,
        pane: {
            center: ['50%', '85%'],
            size: '150%',
            startAngle: -90,
            endAngle: 90,
            background: {
                backgroundColor: '#f4f4f4', // Very light background
                borderRadius: 5,
                innerRadius: '60%',
                outerRadius: '100%',
                shape: 'arc'
            }
        },
        exporting: {
            enabled: false
        },
        tooltip: {
            enabled: false
        },
        credits: {
            enabled: false
        },
        yAxis: {
            lineWidth: 0,
            tickWidth: 0,
            minorTickInterval: null,
            tickAmount: 2,
            title: {
                y: -70,
                style: {
                    color: '#212529' // Dark color for title
                }
            },
            labels: {
                y: 16,
                style: {
                    color: '#212529' // Dark color for labels
                }
            }
        },
        plotOptions: {
            solidgauge: {
                dataLabels: {
                    y: 5,
                    borderWidth: 0,
                    useHTML: true,
                    style: {
                        color: '#212529' // Dark color for data labels
                    }
                }
            }
        }
    };

    // Initialize the gauges with the preset values
    const gauges = {};
    Object.keys(presets).forEach((key) => {
        const containerId = `container-${key}`;

        // Set up dynamic color stops based on the page and gauge type
        let colorStops;
        if (pageName === "network") {
            // Reverse the color stops for the network gauges
            colorStops = [
                [0.1, '#f44336'],  // Red
                [0.5, '#ffeb3b'],  // Yellow
                [0.9, '#4caf50']   // Green
            ];
        } else {
            // Default color stops
            colorStops = [
                [0.1, '#4caf50'],  // Green
                [0.5, '#ffeb3b'],  // Yellow
                [0.9, '#f44336']   // Red
            ];
        }

        gauges[key] = Highcharts.chart(containerId, Highcharts.merge(gaugeOptions, {
            yAxis: {
                min: presets[key].min,
                max: presets[key].max,
                stops: colorStops,  // Apply the dynamic color stops
                title: {
                    text: key.charAt(0).toUpperCase() + key.slice(1),
                    style: {
                        color: '#333',
                        opacity: 75
                    }
                }
            },
            series: [{
                name: key,
                data: [0], // Start with zero value
                dataLabels: {
                    format: `<div style="text-align:center"><span style="font-size:1.15rem;color:#333">{y}</span><br/><span style="font-size:0.75rem;opacity:0.4;color:#333">${presets[key].suffix}</span></div>`
                },
                tooltip: {
                    valueSuffix: presets[key].suffix
                }
            }]
        }));
    });

    // Function to update gauges with new data
    function updateGauges(data) {
        Object.keys(gauges).forEach(key => {
            if (gauges[key]) {
                gauges[key].series[0].points[0].update(data[key]);
            }
        });
    }

    // Determine WebSocket protocol based on current page's protocol
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const socketUrl = `${protocol}//${window.location.host}/ws/${pageName}`;

    // WebSocket connection
    const ws = new WebSocket(socketUrl);

    ws.onmessage = function (event) {
        const data = JSON.parse(event.data);

        // Error handling: If there's an error, show it in the gauge titles
        if (data.error) {
            Object.keys(gauges).forEach(key => {
                gauges[key].yAxis[0].setTitle({ text: 'Error' });
            });
        } else {
            // Update gauges with the received data
            updateGauges(data);
        }
    };

    ws.onerror = function (event) {
        console.error("WebSocket error observed:", event);
        Object.keys(gauges).forEach(key => {
            gauges[key].yAxis[0].setTitle({ text: 'Error' });
        });
    };

    ws.onclose = function () {
        console.log("WebSocket connection closed");
    };
});