/**
 * dashboard.js - Chart.js Visualizations & Analytics for PlantCare AI Dashboard
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Health Status Doughnut Chart
    const statusCtx = document.getElementById('healthStatusChart');
    if (statusCtx && window.dashboardData) {
        const counts = window.dashboardData.status_counts || {};
        new Chart(statusCtx, {
            type: 'doughnut',
            data: {
                labels: ['Healthy', 'Potentially Affected', 'Diseased', 'Unclear'],
                datasets: [{
                    data: [
                        counts['Healthy'] || 0,
                        counts['Potentially Affected'] || 0,
                        counts['Diseased'] || 0,
                        counts['Unclear'] || 0
                    ],
                    backgroundColor: [
                        '#16a34a', // Healthy green
                        '#d97706', // Warning amber
                        '#dc2626', // Danger red
                        '#64748b'  // Unclear slate
                    ],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 14,
                            font: { family: "'Plus Jakarta Sans', sans-serif", weight: '600' }
                        }
                    }
                },
                cutout: '68%'
            }
        });
    }

    // 2. Top Monitored Plant Types Bar Chart
    const plantsCtx = document.getElementById('topPlantsChart');
    if (plantsCtx && window.dashboardData) {
        const topPlants = window.dashboardData.top_plants || [];
        const labels = topPlants.map(p => p.name.split('(')[0].trim());
        const counts = topPlants.map(p => p.count);

        new Chart(plantsCtx, {
            type: 'bar',
            data: {
                labels: labels.length > 0 ? labels : ['No data yet'],
                datasets: [{
                    label: 'Scans Completed',
                    data: counts.length > 0 ? counts : [0],
                    backgroundColor: 'rgba(22, 163, 74, 0.85)',
                    hoverBackgroundColor: '#15803d',
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    },
                    x: {
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }

    // 3. Monitoring Activity Trend Line Chart
    const trendCtx = document.getElementById('activityTrendChart');
    if (trendCtx && window.dashboardData) {
        const timeline = window.dashboardData.timeline || [];
        const labels = timeline.map(t => t.date);
        const counts = timeline.map(t => t.count);

        new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: labels.length > 0 ? labels : ['Today'],
                datasets: [{
                    label: 'Daily Analyses',
                    data: counts.length > 0 ? counts : [0],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.15)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.35,
                    pointBackgroundColor: '#15803d',
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    },
                    x: {
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }
});
