document.addEventListener('DOMContentLoaded', function () {
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
            stops: [
                [0.1, '#4caf50'], // Green
                [0.5, '#ffeb3b'], // Yellow
                [0.9, '#f44336'] // Red
            ],
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
                borderRadius: 3,
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

    // Initialize the gauges
    const gauges = {
        volts: Highcharts.chart('container-volts', Highcharts.merge(gaugeOptions, {
            yAxis: {
                min: 0,
                max: 100,
                title: {
                    text: 'Volts',
                    style: {
                        color: '#333',
                        opacity: 75
                    }
                }
            },
            series: [{
                name: 'Volts',
                data: [Math.floor(Math.random() * 100)],
                dataLabels: {
                    format: '<div style="text-align:center"><span style="font-size:1.15rem;color:#333">{y}</span><br/><span style="font-size:0.75rem;opacity:0.4;color:#333">V</span></div>'
                },
                tooltip: {
                    valueSuffix: ' V'
                }
            }]
        })),
        watts: Highcharts.chart('container-temp', Highcharts.merge(gaugeOptions, {
            yAxis: {
                min: 0,
                max: 100,
                title: {
                    text: 'Temperature'
                }
            },
            series: [{
                name: 'Temperature',
                data: [Math.floor(Math.random() * 100)],
                dataLabels: {
                    format: '<div style="text-align:center"><span style="font-size:1.15rem;color:#333">{y}</span><br/><span style="font-size:0.75rem;opacity:0.4;color:#333">F</span></div>'
                },
                tooltip: {
                    valueSuffix: ' F'
                }
            }]
        })),
        amps: Highcharts.chart('container-lag', Highcharts.merge(gaugeOptions, {
            yAxis: {
                min: 0,
                max: 100,
                title: {
                    text: 'Latency'
                }
            },
            series: [{
                name: 'Latency',
                data: [Math.floor(Math.random() * 100)],
                dataLabels: {
                    format: '<div style="text-align:center"><span style="font-size:1.15rem;color:#333">{y}</span><br/><span style="font-size:0.75rem;opacity:0.4;color:#333">ms</span></div>'
                },
                tooltip: {
                    valueSuffix: ' ms'
                }
            }]
        }))
    };
    function updateGauges(data) {
        if (gauges.volts) {
            gauges.volts.series[0].points[0].update(data.volts);
        }
        if (gauges.watts) {
            gauges.watts.series[0].points[0].update(data.watts);
        }
        if (gauges.amps) {
            gauges.amps.series[0].points[0].update(data.amps);
        }
    }

    // For now, use random data for demonstration
    setInterval(function () {
        updateGauges({
            volts: Math.floor(Math.random() * 100),
            watts: Math.floor(Math.random() * 100),
            amps: Math.floor(Math.random() * 100)
        });
    }, 2000);
});