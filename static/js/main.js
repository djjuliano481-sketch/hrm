document.addEventListener('DOMContentLoaded', function () {
    initSidebar();
    initNotifications();
    initUserDropdown();
    initAutoCloseAlerts();
});

function initSidebar() {
    const toggleBtn = document.getElementById('toggleSidebar');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', function () {
            sidebar.classList.toggle('show');
            if (overlay) overlay.classList.toggle('show');
        });
    }

    if (overlay) {
        overlay.addEventListener('click', function () {
            sidebar.classList.remove('show');
            overlay.classList.remove('show');
        });
    }

    const currentPath = window.location.pathname;
    document.querySelectorAll('.sidebar .nav-link').forEach(function (link) {
        const href = link.getAttribute('href');
        if (href && currentPath.startsWith(href) && href !== '/') {
            link.classList.add('active');
        } else if (href === '/' && currentPath === '/') {
            link.classList.add('active');
        }
    });
}

function initNotifications() {
    const notifBtn = document.getElementById('notificationBtn');
    const notifDropdown = document.getElementById('notificationDropdown');

    if (notifBtn && notifDropdown) {
        notifBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            notifDropdown.classList.toggle('show');
            closeUserDropdown();
        });

        document.addEventListener('click', function (e) {
            if (!notifBtn.contains(e.target) && !notifDropdown.contains(e.target)) {
                notifDropdown.classList.remove('show');
            }
        });
    }
}

function initUserDropdown() {
    const userBtn = document.getElementById('userDropdownBtn');
    const userMenu = document.getElementById('userDropdownMenu');

    if (userBtn && userMenu) {
        userBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            userMenu.classList.toggle('show');
            closeNotifDropdown();
        });

        document.addEventListener('click', function (e) {
            if (!userBtn.contains(e.target) && !userMenu.contains(e.target)) {
                userMenu.classList.remove('show');
            }
        });
    }
}

function closeNotifDropdown() {
    const dd = document.getElementById('notificationDropdown');
    if (dd) dd.classList.remove('show');
}

function closeUserDropdown() {
    const dd = document.getElementById('userDropdownMenu');
    if (dd) dd.classList.remove('show');
}

function initAutoCloseAlerts() {
    document.querySelectorAll('.alert').forEach(function (alert) {
        setTimeout(function () {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(function () {
                if (alert.parentNode) alert.remove();
            }, 500);
        }, 5000);
    });
}

function initCharts(chartData) {
    if (!chartData || typeof Chart === 'undefined') return;

    const chartColors = {
        primary: '#2563EB',
        primaryLight: '#DBEAFE',
        success: '#10B981',
        warning: '#F59E0B',
        danger: '#EF4444',
        gray: '#9CA3AF',
    };

    function createChart(canvasId, config) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        try {
            return new Chart(canvas, config);
        } catch (e) {
            console.warn('Chart init error for', canvasId, e);
        }
    }

    createChart('deptChart', {
        type: 'doughnut',
        data: {
            labels: chartData.deptLabels || [],
            datasets: [{
                data: chartData.deptData || [],
                backgroundColor: ['#2563EB', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4'],
                borderWidth: 0,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { padding: 16, usePointStyle: true, font: { size: 12 } }
                }
            },
            cutout: '70%',
        }
    });

    createChart('attendanceTrendChart', {
        type: 'line',
        data: {
            labels: chartData.attendanceLabels || [],
            datasets: [{
                label: 'Present',
                data: chartData.attendanceData || [],
                borderColor: chartColors.primary,
                backgroundColor: chartColors.primaryLight,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: chartColors.primary,
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 4,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, grid: { color: '#F3F4F6' } },
                x: { grid: { display: false } }
            }
        }
    });

    createChart('employeeGrowthChart', {
        type: 'bar',
        data: {
            labels: chartData.employeeGrowthLabels || [],
            datasets: [{
                label: 'New Employees',
                data: chartData.employeeGrowthData || [],
                backgroundColor: chartColors.primary,
                borderRadius: 6,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, grid: { color: '#F3F4F6' } },
                x: { grid: { display: false } }
            }
        }
    });

    createChart('leaveTrendChart', {
        type: 'bar',
        data: {
            labels: chartData.leaveTrendLabels || [],
            datasets: [{
                label: 'Leave Requests',
                data: chartData.leaveTrendData || [],
                backgroundColor: chartColors.warning,
                borderRadius: 6,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, grid: { color: '#F3F4F6' } },
                x: { grid: { display: false } }
            }
        }
    });
}
