document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
});

function initializeDashboard() {
    
    const departmentFilter = document.getElementById('department-filter');
    if (departmentFilter) {
        departmentFilter.addEventListener('change', function() {
            applyDepartmentFilter(this.value);
        });
    }
    
    
    animateKpiNumbers();
    
    
    setupTooltips();
}

function applyDepartmentFilter(department) {
    // Get current URL
    const url = new URL(window.location.href);
    
    // Update department parameter
    if (department) {
        url.searchParams.set('department', department);
    } else {
        url.searchParams.delete('department');
    }
    
    // Navigate to new URL
    window.location.href = url.toString();
}

function animateKpiNumbers() {
    const kpiElements = document.querySelectorAll('.kpi-card .display-4');
    
    kpiElements.forEach(element => {
        const targetValue = parseFloat(element.textContent);
        if (!isNaN(targetValue)) {
            // Start from zero
            let startValue = 0;
            const duration = 1500; // milliseconds
            const increment = targetValue / (duration / 16); // 60 FPS
            
            // Animate the number
            const animation = setInterval(() => {
                startValue += increment;
                if (startValue >= targetValue) {
                    element.textContent = Number.isInteger(targetValue) ? 
                        targetValue.toString() : 
                        targetValue.toFixed(1);
                    clearInterval(animation);
                } else {
                    element.textContent = Number.isInteger(targetValue) ? 
                        Math.floor(startValue).toString() : 
                        startValue.toFixed(1);
                }
            }, 16);
        }
    });
}

function setupTooltips() {
    // Add tooltips to charts
    const chartContainers = document.querySelectorAll('.chart-container');
    chartContainers.forEach(container => {
        const header = container.querySelector('h5');
        if (header) {
            header.setAttribute('data-toggle', 'tooltip');
            header.setAttribute('data-placement', 'top');
            header.setAttribute('title', 'Click to expand');
            
            // Add click handler to expand chart
            header.addEventListener('click', function() {
                const chart = this.parentElement;
                chart.classList.toggle('expanded');
                if (chart.classList.contains('expanded')) {
                    chart.style.position = 'fixed';
                    chart.style.top = '5%';
                    chart.style.left = '5%';
                    chart.style.width = '90%';
                    chart.style.height = '90%';
                    chart.style.zIndex = '1000';
                    chart.style.overflow = 'auto';
                } else {
                    chart.style.position = '';
                    chart.style.top = '';
                    chart.style.left = '';
                    chart.style.width = '';
                    chart.style.height = '';
                    chart.style.zIndex = '';
                    chart.style.overflow = '';
                }
            });
        }
    });
    
    
    $('[data-toggle="tooltip"]').tooltip();
}

// Utility to format numbers
function formatNumber(num) {
    return num.toString().replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1,');
}

// Handle ETL and Model refresh processes
function updateProgressBar(percentage, message) {
    const progressBar = document.getElementById('progress-bar');
    const messageElem = document.getElementById('progress-message');
    
    if (progressBar) {
        progressBar.style.width = percentage + '%';
        progressBar.setAttribute('aria-valuenow', percentage);
    }
    
    if (messageElem && message) {
        messageElem.textContent = message;
    }
}
