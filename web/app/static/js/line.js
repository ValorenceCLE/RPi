document.addEventListener('DOMContentLoaded', function () {
    // Determine the page and datasets dynamically
    const pageName = window.location.pathname.split('/').pop(); // Extract page name from URL

    // Map datasets based on the page
    const datasets = {
        system: ['Volts', 'Watts', 'Amps'],
        router: ['Volts', 'Watts', 'Amps'],
        camera: ['Volts', 'Watts', 'Amps'],
        network: ['RSRP', 'RSRQ', 'SINR']
    };

    const currentPageData = datasets[pageName] || datasets['system']; // Default to system if page not found

    // Initialize the chart
    let chart = null;

    // Function to render the chart
    function renderLineChart(data) {
        chart = Highcharts.chart('container-line-chart', {
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
                        radius: 1.5,
                        lineWidth: 1,
                        lineColor: null
                    }
                }
            },
            series: data, // Load data dynamically
            credits: {
                enabled: false
            },
            legend: {
                enabled: true // Enable legend to differentiate data sets
            }
        });
    }

    // Fetch and update the chart data
    async function fetchChartData(timeFrame) {
        try {
            const response = await fetch(`/${pageName}/data/${timeFrame}`);
            const result = await response.json();

            if (result.error) {
                chart.setTitle({ text: 'Error' });
                return;
            }

            const chartData = currentPageData.map((name, index) => {
                return {
                    name: name,
                    data: result.data.map(item => [Date.parse(item.timestamp), item[name.toLowerCase()]])
                };
            });

            // Render or update the chart with the new data
            if (chart) {
                chart.series.forEach((series, index) => {
                    series.setData(chartData[index].data);
                });
            } else {
                renderLineChart(chartData);
            }
        } catch (error) {
            console.error("Error fetching chart data:", error);
            if (chart) {
                chart.setTitle({ text: 'Error' });
            }
        }
    }

    // Event listener for time frame selection
    document.querySelectorAll('.dropdown-item').forEach(item => {
        item.addEventListener('click', function () {
            const timeFrame = this.getAttribute('data-value');
            fetchChartData(timeFrame);
        });
    });

    // Initial load with 15 minutes of data (or the default time frame)
    fetchChartData('15m');
});
