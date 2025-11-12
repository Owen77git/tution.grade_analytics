// static/js/Filcharts.js - Fixed Chart Management System
class ChartManager {
    constructor() {
        this.charts = new Map();
        this.colors = {
            primary: ['#6366f1', '#60a5fa', '#3b82f6'],
            success: ['#10b981', '#34d399', '#6ee7b7'],
            warning: ['#f59e0b', '#fbbf24', '#fcd34d'],
            danger: ['#ef4444', '#f87171', '#fca5a5'],
            accent: ['#8b5cf6', '#a78bfa', '#c4b5fd'],
            pink: ['#ec4899', '#f472b6', '#f9a8d4']
        };
    }

    // Safe chart initialization
    initChart(canvasId, config) {
        try {
            const canvas = document.getElementById(canvasId);
            if (!canvas) {
                console.warn(`Canvas element not found: ${canvasId}`);
                return null;
            }

            // Destroy existing chart
            this.destroyChart(canvasId);

            const ctx = canvas.getContext('2d');
            const chart = new Chart(ctx, config);
            this.charts.set(canvasId, chart);
            return chart;
        } catch (error) {
            console.error(`Error initializing chart ${canvasId}:`, error);
            return null;
        }
    }

    // Initialize all charts for admin dashboard
    initAdminCharts(performanceData) {
        if (!performanceData) {
            console.warn('No performance data provided for admin charts');
            return;
        }

        this.createPerformanceTrend('performanceChart', performanceData);
        this.createSubjectComparison('subjectChart', performanceData.subject_averages);
        this.createDayAnalysis('dayChart', performanceData.day_averages);
        this.createTeacherAnalysis('teacherChart', performanceData.teacher_averages);
        this.createTopicAnalysis('topicChart', performanceData.topic_averages);
    }

    // Initialize all charts for teacher dashboard
    initTeacherCharts(performanceData) {
        if (!performanceData) {
            console.warn('No performance data provided for teacher charts');
            return;
        }

        this.createAreaChart('areaChart', performanceData);
        this.createDayOfWeekChart('dayChart', performanceData.day_averages);
        this.createTeacherComparison('teacherChart', performanceData.teacher_averages);
        this.createTopicChart('topicChart', performanceData.topic_averages);
    }

    // Initialize all charts for student dashboard
    initStudentCharts(performanceData) {
        if (!performanceData) {
            console.warn('No performance data provided for student charts');
            return;
        }

        this.createStudentPerformance('performanceChart', performanceData);
        this.createStudentDayChart('dayChart', performanceData.day_averages);
        this.createStudentTeacherChart('teacherChart', performanceData.teacher_averages);
        this.createStudentTopicChart('topicChart', performanceData.topic_averages);
        this.createStudentSubjectChart('subjectChart', performanceData.subject_averages);
    }

    // Chart creation methods
    createPerformanceTrend(canvasId, data) {
        return this.initChart(canvasId, {
            type: 'line',
            data: {
                labels: data.dates || this.generateDefaultLabels(6),
                datasets: [{
                    label: 'Overall Performance',
                    data: data.scores || this.generateSampleData(6, 70, 10),
                    tension: 0.4,
                    borderWidth: 2,
                    fill: true,
                    backgroundColor: 'rgba(96,165,250,0.08)',
                    borderColor: 'rgba(96,165,250,0.9)',
                    pointBackgroundColor: 'rgba(96,165,250,1)',
                    pointBorderColor: '#fff',
                    pointRadius: 3
                }]
            },
            options: this.getLineChartOptions()
        });
    }

    createAreaChart(canvasId, data) {
        return this.initChart(canvasId, {
            type: 'line',
            data: {
                labels: data.dates || this.generateDefaultLabels(4),
                datasets: [{
                    label: 'Class Average',
                    data: data.scores || this.generateSampleData(4, 72, 8),
                    tension: 0.4,
                    borderWidth: 2,
                    fill: true,
                    backgroundColor: 'rgba(110,231,183,0.1)',
                    borderColor: 'rgba(110,231,183,0.8)',
                    pointBackgroundColor: 'rgba(110,231,183,1)',
                    pointBorderColor: '#fff'
                }]
            },
            options: this.getLineChartOptions()
        });
    }

    createStudentPerformance(canvasId, data) {
        return this.initChart(canvasId, {
            type: 'line',
            data: {
                labels: data.dates || this.generateDefaultLabels(5),
                datasets: [{
                    label: 'Your Performance',
                    data: data.scores || this.generateSampleData(5, 75, 10),
                    tension: 0.4,
                    borderWidth: 2,
                    fill: true,
                    backgroundColor: 'rgba(99,102,241,0.1)',
                    borderColor: 'rgba(99,102,241,0.8)',
                    pointBackgroundColor: 'rgba(99,102,241,1)',
                    pointBorderColor: '#fff'
                }]
            },
            options: this.getStudentChartOptions()
        });
    }

    createSubjectComparison(canvasId, subjectData) {
        const data = subjectData || { Mathematics: 78, Science: 82, English: 75 };
        const labels = Object.keys(data);
        const values = Object.values(data);

        return this.initChart(canvasId, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Average Score',
                    data: values,
                    backgroundColor: this.generateColors(labels.length, 0.8),
                    borderRadius: 6
                }]
            },
            options: this.getBarChartOptions()
        });
    }

    createDayAnalysis(canvasId, dayData) {
        const data = dayData || { Monday: 75, Tuesday: 82, Wednesday: 78, Thursday: 80, Friday: 76 };
        const labels = Object.keys(data);
        const values = Object.values(data);

        return this.initChart(canvasId, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Average Score',
                    data: values,
                    backgroundColor: 'rgba(249,115,22,0.8)',
                    borderRadius: 6
                }]
            },
            options: this.getBarChartOptions()
        });
    }

    createDayOfWeekChart(canvasId, dayData) {
        const data = dayData || { Monday: 75, Tuesday: 82, Wednesday: 78, Thursday: 80, Friday: 76 };
        const labels = Object.keys(data);
        const values = Object.values(data);

        return this.initChart(canvasId, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: this.generateColors(labels.length, 0.8)
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                cutout: '60%'
            }
        });
    }

    createTeacherAnalysis(canvasId, teacherData) {
        const data = teacherData || { 'Mr. Kamau': 80, 'Mrs. Moraa': 75, 'Mr. Njoroge': 78 };
        const labels = Object.keys(data);
        const values = Object.values(data);

        return this.initChart(canvasId, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: this.generateColors(labels.length, 0.8)
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#9aa4b2',
                            font: { size: 11 }
                        }
                    }
                }
            }
        });
    }

    createTeacherComparison(canvasId, teacherData) {
        const data = teacherData || { 'Mr. Kamau': 80, 'Mrs. Moraa': 75, 'Mr. Njoroge': 78 };
        const labels = Object.keys(data);
        const values = Object.values(data);

        return this.initChart(canvasId, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: 'rgba(96,165,250,0.8)',
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { display: false },
                    y: { display: false }
                }
            }
        });
    }

    createTopicAnalysis(canvasId, topicData) {
        const data = topicData || { Algebra: 72, Geometry: 78, Trigonometry: 75, Statistics: 82 };
        const labels = Object.keys(data);
        const values = Object.values(data);

        return this.initChart(canvasId, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Average Score',
                    data: values,
                    backgroundColor: 'rgba(139,92,246,0.8)',
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                indexAxis: 'y',
                scales: {
                    x: { grid: { display: false }, ticks: { color: '#9aa4b2' } },
                    y: { ticks: { color: '#9aa4b2' } }
                }
            }
        });
    }

    createTopicChart(canvasId, topicData) {
        const data = topicData || { Algebra: 80, Geometry: 75, Statistics: 82 };
        const labels = Object.keys(data);
        const values = Object.values(data);

        return this.initChart(canvasId, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: 'rgba(249,115,22,0.8)',
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { display: false },
                    y: { display: false }
                }
            }
        });
    }

    createStudentDayChart(canvasId, dayData) {
        const data = dayData || { Monday: 75, Tuesday: 82, Wednesday: 78, Thursday: 80, Friday: 76 };
        const labels = Object.keys(data);
        const values = Object.values(data);

        return this.initChart(canvasId, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Average Score',
                    data: values,
                    backgroundColor: 'rgba(99,102,241,0.8)',
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } }
            }
        });
    }

    createStudentTeacherChart(canvasId, teacherData) {
        const data = teacherData || { 'Mr. Kamau': 80, 'Mrs. Moraa': 75, 'Mr. Njoroge': 78 };
        const labels = Object.keys(data);
        const values = Object.values(data);

        return this.initChart(canvasId, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Average Score',
                    data: values,
                    backgroundColor: 'rgba(236,72,153,0.8)',
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } }
            }
        });
    }

    createStudentTopicChart(canvasId, topicData) {
        const data = topicData || { Statistics: 85, Algebra: 72, Geometry: 78, Trigonometry: 75 };
        const labels = Object.keys(data);
        const values = Object.values(data);

        return this.initChart(canvasId, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Average Score',
                    data: values,
                    backgroundColor: 'rgba(16,185,129,0.8)',
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                indexAxis: 'y'
            }
        });
    }

    createStudentSubjectChart(canvasId, subjectData) {
        const data = subjectData || { Mathematics: 78, English: 82 };
        const labels = Object.keys(data);
        const values = Object.values(data);

        return this.initChart(canvasId, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: this.generateColors(labels.length, 0.8)
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    // Utility methods
    generateColors(count, alpha = 1) {
        const baseColors = [
            `rgba(96,165,250,${alpha})`,
            `rgba(45,212,191,${alpha})`,
            `rgba(249,115,22,${alpha})`,
            `rgba(139,92,246,${alpha})`,
            `rgba(236,72,153,${alpha})`,
            `rgba(16,185,129,${alpha})`,
            `rgba(245,158,11,${alpha})`
        ];
        return baseColors.slice(0, count);
    }

    generateDefaultLabels(count) {
        return Array.from({ length: count }, (_, i) => `Week ${i + 1}`);
    }

    generateSampleData(count, base = 70, variance = 10) {
        return Array.from({ length: count }, () => 
            Math.max(0, Math.min(100, base + (Math.random() * variance * 2 - variance)))
        );
    }

    getLineChartOptions() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: '#9aa4b2' }
                },
                y: {
                    ticks: { color: '#9aa4b2' },
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    suggestedMin: 0,
                    suggestedMax: 100
                }
            }
        };
    }

    getBarChartOptions() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: '#9aa4b2' }
                },
                y: {
                    ticks: { color: '#9aa4b2' },
                    grid: { color: 'rgba(255,255,255,0.05)' }
                }
            }
        };
    }

    getStudentChartOptions() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: {
                    grid: { color: '#1e293b' },
                    ticks: { color: '#94a3b8' }
                },
                y: {
                    grid: { color: '#1e293b' },
                    ticks: { color: '#94a3b8' },
                    min: 0,
                    max: 100
                }
            }
        };
    }

    // Chart management
    destroyChart(canvasId) {
        if (this.charts.has(canvasId)) {
            this.charts.get(canvasId).destroy();
            this.charts.delete(canvasId);
        }
    }

    destroyAllCharts() {
        this.charts.forEach((chart, canvasId) => {
            chart.destroy();
        });
        this.charts.clear();
    }

    updateChartData(canvasId, newData) {
        if (this.charts.has(canvasId)) {
            const chart = this.charts.get(canvasId);
            chart.data = newData;
            chart.update('active');
        }
    }
}

// Global chart manager instance
const chartManager = new ChartManager();

// Utility functions
const ChartUtils = {
    calculateAverage: (scores) => {
        if (!scores || scores.length === 0) return 0;
        return scores.reduce((a, b) => a + b, 0) / scores.length;
    },

    formatPercentage: (value) => {
        return `${Math.round(value)}%`;
    },

    getGradeFromScore: (score) => {
        if (score >= 90) return 'A';
        if (score >= 85) return 'A-';
        if (score >= 80) return 'B+';
        if (score >= 75) return 'B';
        if (score >= 70) return 'B-';
        if (score >= 65) return 'C+';
        if (score >= 60) return 'C';
        if (score >= 55) return 'C-';
        if (score >= 50) return 'D';
        return 'F';
    }
};
