/**
 * Portfolio Report Charts & Interactions
 * This file contains chart configurations and helper functions
 * Data is injected from Python via template placeholders
 */

// Chart color palette (matches Figma design)
const COLORS = {
    primary: '#0f172a',      // Dark navy
    secondary: '#3b82f6',    // Blue
    tertiary: '#93c5fd',     // Light blue
    accent: '#6366f1',       // Purple (portfolio line)
    benchmark: '#22d3ee',    // Cyan (benchmark line)
    positive: '#16a34a',     // Green
    negative: '#dc2626',     // Red
    gray: '#64748b',
    lightGray: '#e2e8f0'
};

// Symbol badge color assignments
const SYMBOL_COLORS = ['green', 'purple', 'blue', 'orange', 'yellow'];

/**
 * Get symbol badge color class based on index
 */
function getSymbolColor(index) {
    return SYMBOL_COLORS[index % SYMBOL_COLORS.length];
}

/**
 * Format number as percentage
 */
function formatPercent(value, decimals = 1) {
    return `${value >= 0 ? '+' : ''}${value.toFixed(decimals)}%`;
}

/**
 * Format number as currency
 */
function formatCurrency(value, currency = '$') {
    return `${currency}${value.toLocaleString()}`;
}

/**
 * Initialize Performance Chart
 * @param {Object} data - { labels: [], portfolio: [], benchmark: [] }
 */
function initPerformanceChart(data) {
    const ctx = document.getElementById('performanceChart');
    if (!ctx) return;
    
    return new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'Portfolio',
                    data: data.portfolio,
                    borderColor: COLORS.accent,
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    borderWidth: 2
                },
                {
                    label: 'S&P 500',
                    data: data.benchmark,
                    borderColor: COLORS.benchmark,
                    backgroundColor: 'transparent',
                    fill: false,
                    tension: 0.4,
                    pointRadius: 0,
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${formatCurrency(context.raw)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { size: 10 }, color: COLORS.gray }
                },
                y: {
                    grid: { color: COLORS.lightGray },
                    ticks: { 
                        font: { size: 10 }, 
                        color: COLORS.gray,
                        callback: function(value) {
                            return formatCurrency(value);
                        }
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

/**
 * Initialize Allocation Doughnut Chart
 * @param {Object} data - { labels: [], values: [] }
 */
function initAllocationChart(data) {
    const ctx = document.getElementById('allocationChart');
    if (!ctx) return;
    
    return new Chart(ctx.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.values,
                backgroundColor: [COLORS.primary, COLORS.secondary, COLORS.tertiary],
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            cutout: '60%',
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.label}: ${context.raw}%`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Generate allocation legend HTML
 * @param {Object} data - { labels: [], values: [] }
 */
function generateAllocationLegend(data) {
    const colorClasses = ['dark', 'blue', 'light'];
    return data.labels.map((label, i) => `
        <div class="allocation-legend-item">
            <span class="legend-dot ${colorClasses[i]}"></span>
            <span>${label}</span>
        </div>
    `).join('');
}

/**
 * Generate holdings table rows HTML
 * @param {Array} holdings - Array of holding objects
 */
function generateHoldingsRows(holdings) {
    return holdings.map((h, i) => `
        <tr>
            <td><span class="symbol-badge ${getSymbolColor(i)}">${h.symbol}</span></td>
            <td>${h.name}</td>
            <td>${h.category}</td>
            <td>${h.expense_ratio}</td>
            <td>${h.allocation}</td>
        </tr>
    `).join('');
}

/**
 * Generate geographic exposure rows HTML
 * @param {Array} regions - Array of region objects { name, allocation }
 */
function generateGeographicRows(regions) {
    return regions.map(r => `
        <tr>
            <td>${r.name}</td>
            <td>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div class="allocation-bar" style="width: 60px;">
                        <div class="allocation-bar-fill" style="width: ${r.allocation}%;"></div>
                    </div>
                    <span>${r.allocation}%</span>
                </div>
            </td>
        </tr>
    `).join('');
}

/**
 * Generate top holdings rows HTML
 * @param {Array} holdings - Array of holding objects { name, allocation }
 */
function generateTopHoldingsRows(holdings) {
    return holdings.map(h => `
        <tr>
            <td>${h.name}</td>
            <td>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div class="allocation-bar" style="width: 60px;">
                        <div class="allocation-bar-fill" style="width: ${h.allocation}%;"></div>
                    </div>
                    <span>${h.allocation}%</span>
                </div>
            </td>
        </tr>
    `).join('');
}

// Export functions for use in template
window.PortfolioCharts = {
    initPerformanceChart,
    initAllocationChart,
    generateAllocationLegend,
    generateHoldingsRows,
    generateGeographicRows,
    generateTopHoldingsRows,
    formatPercent,
    formatCurrency,
    COLORS
};
