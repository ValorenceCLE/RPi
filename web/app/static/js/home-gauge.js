document.addEventListener('DOMContentLoaded', async function () {
    // Fetch the presets for the homepage
    const response = await fetch('/presets/home');
    const presets = await response.json();

    // Define Gauge options/settings
    const gaugeOptions = {
        chart: {
            type: 'solidgauge',
            backgroundColor: '#fff',
        },
        title: null,
        pane: {
            center: ['50%', '85%'],
            size: '150%',
            startAngle: -90,
            endAngle: 90,
            background: {
                backgroundColor: '#f4f4f4',
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
            stops: [
                [0.1, '#4caf50'],  // Green
                [0.5, '#ffeb3b'],  // Yellow
                [0.9, '#f44336']   // Red
            ],
            lineWidth: 0,
            tickWidth: 0,
            minorTickInterval: null,
            tickAmount: 2,
            title: {
                y: -70,
                style: {
                    color: '#212529'
                }
            },
            labels: {
                y: 16,
                style: {
                    color: '#212529'
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
                        color: '#212529'
                    }
                }
            }
        }
    };

    // Initialize the gauges with the preset values
    const gauges = {
        volts: Highcharts.chart('container-volts', Highcharts.merge(gaugeOptions, {
            yAxis: {
                min: presets.volts.min,
                max: presets.volts.max,
                title: {
                    text: 'Volts'
                }
            },
            series: [{
                name: 'Volts',
                data: [0],
                dataLabels: {
                    format: `<div style="text-align:center"><span style="font-size:1.15rem;color:#333">{y}</span><br/><span style="font-size:0.75rem;opacity:0.4;color:#333">V</span></div>`
                },
                tooltip: {
                    valueSuffix: ' V'
                }
            }]
        })),
        temperature: Highcharts.chart('container-temp', Highcharts.merge(gaugeOptions, {
            yAxis: {
                min: presets.temperature.min,
                max: presets.temperature.max,
                title: {
                    text: 'Temperature'
                }
            },
            series: [{
                name: 'Temperature',
                data: [0],
                dataLabels: {
                    format: `<div style="text-align:center"><span style="font-size:1.15rem;color:#333">{y}</span><br/><span style="font-size:0.75rem;opacity:0.4;color:#333">°F</span></div>`
                },
                tooltip: {
                    valueSuffix: ' °F'
                }
            }]
        })),
        latency: Highcharts.chart('container-lag', Highcharts.merge(gaugeOptions, {
            yAxis: {
                min: presets.latency.min,
                max: presets.latency.max,
                title: {
                    text: 'Latency'
                }
            },
            series: [{
                name: 'Latency',
                data: [0],
                dataLabels: {
                    format: `<div style="text-align:center"><span style="font-size:1.15rem;color:#333">{y}</span><br/><span style="font-size:0.75rem;opacity:0.4;color:#333">ms</span></div>`
                },
                tooltip: {
                    valueSuffix: ' ms'
                }
            }]
        }))
    };

    // Function to update gauges with new data
    function updateGauges(data) {
        Object.keys(gauges).forEach(key => {
            if (gauges[key]) {
                gauges[key].series[0].points[0].update(data[key]);
            }
        });
    }

    // WebSocket connection for the homepage
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const socketUrl = `${protocol}//${window.location.host}/ws/`;
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
