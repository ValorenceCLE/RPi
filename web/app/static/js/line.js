document.addEventListener('DOMContentLoaded', function () {
    const lineChartData = {
        volts: [
            [Date.UTC(2023, 4, 1), 12.6],
            [Date.UTC(2023, 4, 2), 12.1],
            [Date.UTC(2023, 4, 3), 12.3],
            [Date.UTC(2023, 4, 4), 13.1],
            [Date.UTC(2023, 4, 5), 12.1]
        ],
        watts: [
            [Date.UTC(2023, 4, 1), 13.1],
            [Date.UTC(2023, 4, 2), 13.6],
            [Date.UTC(2023, 4, 3), 12.9],
            [Date.UTC(2023, 4, 4), 13.5],
            [Date.UTC(2023, 4, 5), 13.8]
        ],
        amps: [
            [Date.UTC(2023, 4, 1), 1.1],
            [Date.UTC(2023, 4, 2), 0.9],
            [Date.UTC(2023, 4, 3), 1],
            [Date.UTC(2023, 4, 4), 1.3],
            [Date.UTC(2023, 4, 5), 1.4]
        ]
    };

    function renderLineChart() {
        Highcharts.chart('container-line-chart', {
            chart: {
                type: 'spline',
                backgroundColor: '#fff'
            },
            title: {
                text: null // Remove chart title
            },
            xAxis: {
                type: 'datetime',
                dateTimeLabelFormats: {
                    month: '%e. %b',
                    year: '%b'
                },
                labels: {
                    style: {
                        color: '#333'
                    }
                }
            },
            yAxis: {
                title: {
                    text: null // Remove y-axis title
                },
                min: 0,
                labels: {
                    style: {
                        color: '#333'
                    }
                }
            },
            tooltip: {
                headerFormat: '<b>{series.name}</b><br>',
                pointFormat: '{point.x:%e. %b}: {point.y:.2f}'
            },
            plotOptions: {
                series: {
                    marker: {
                        symbol: 'circle',
                        fillColor: '#FFFFFF',
                        enabled: true,
                        radius: 2.5,
                        lineWidth: 1,
                        lineColor: null
                    }
                }
            },
            series: [
                {
                    name: 'Volts',
                    data: lineChartData.volts
                },
                {
                    name: 'Watts',
                    data: lineChartData.watts
                },
                {
                    name: 'Amps',
                    data: lineChartData.amps
                }
            ],
            credits: {
                enabled: false
            },
            legend: {
                enabled: true // Enable legend to differentiate data sets
            }
        });
    }

    // Initial chart setup with all data sets
    renderLineChart();
});
