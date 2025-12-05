async function loadPortfolio() {
    try {
        const response = await fetch('portfolio_data.json');
        const data = await response.json();
        populateTemplate(data);
    } catch (error) {
        console.error('Error loading portfolio data:', error);
    }
}

function populateTemplate(data) {
    document.getElementById('report-date').textContent = 
        new Date(data.generated_at).toLocaleDateString('en-US', { 
            year: 'numeric', month: 'long', day: 'numeric' 
        });
    
    document.getElementById('profile-goal').textContent = data.profile.goal;
    document.getElementById('profile-horizon').textContent = data.profile.time_horizon;
    document.getElementById('profile-risk').textContent = data.profile.risk_behavior;
    document.getElementById('profile-amount').textContent = `$${data.profile.amount.toLocaleString()}`;
    document.getElementById('donut-amount').textContent = `$${data.profile.amount.toLocaleString()}`;
    
    document.getElementById('equity-legend').textContent = `Equity ${data.portfolio.equity_pct}%`;
    document.getElementById('bonds-legend').textContent = `Bonds ${data.portfolio.bond_pct}%`;
    
    const tableBody = document.getElementById('etf-table-body');
    data.portfolio.etfs.forEach((etf, index) => {
        const row = document.createElement('tr');
        const typeClass = etf.type === 'Core' ? 'core' : 'thematic';
        const typeLabel = etf.type === 'Core' ? 'C' : 'T';
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${etf.name}</td>
            <td>${etf.allocation}%</td>
            <td>$${etf.amount.toLocaleString()}</td>
            <td><span class="type-badge ${typeClass}">${typeLabel}</span></td>
        `;
        tableBody.appendChild(row);
    });
    
    document.getElementById('scenario-split').textContent = 
        `${data.portfolio.equity_pct}% equity / ${data.portfolio.bond_pct}% bond`;
    document.getElementById('scenario-best').textContent = `+${data.scenarios.best}%`;
    document.getElementById('scenario-avg').textContent = `+${data.scenarios.average}%`;
    document.getElementById('scenario-worst').textContent = `${data.scenarios.worst}%`;
    
    const portfolioReturn = data.backtest.portfolio.return_3y;
    const sp500Return = data.backtest.sp500.return_3y;
    
    if (portfolioReturn !== null) {
        const pEl = document.getElementById('portfolio-return');
        pEl.textContent = `${portfolioReturn > 0 ? '+' : ''}${portfolioReturn}%`;
        pEl.style.color = portfolioReturn >= 0 ? '#16a34a' : '#dc2626';
    }
    
    if (sp500Return !== null) {
        const sEl = document.getElementById('sp500-return');
        sEl.textContent = `${sp500Return > 0 ? '+' : ''}${sp500Return}%`;
        sEl.style.color = sp500Return >= 0 ? '#16a34a' : '#dc2626';
    }
    
    if (portfolioReturn !== null && sp500Return !== null) {
        const diff = (portfolioReturn - sp500Return).toFixed(1);
        const dEl = document.getElementById('return-diff');
        dEl.textContent = `${diff > 0 ? '+' : ''}${diff}%`;
        dEl.style.color = diff >= 0 ? '#16a34a' : '#dc2626';
    }
    
    const themesGrid = document.getElementById('themes-grid');
    const allThemes = [
        ...data.profile.themes.regions,
        ...data.profile.themes.sectors,
        ...data.profile.themes.trends,
        ...data.profile.themes.commodities
    ].slice(0, 12);
    
    allThemes.forEach(theme => {
        const item = document.createElement('div');
        item.className = 'theme-item';
        item.innerHTML = `<span class="theme-arrow">›</span> ${theme}`;
        themesGrid.appendChild(item);
    });
    
    document.getElementById('step-amount').textContent = `$${data.profile.amount.toLocaleString()}`;
    const annualCost = (data.profile.amount * 0.0025).toFixed(2);
    document.getElementById('annual-cost').textContent = `~$${annualCost}/year (avg TER 0.25%)`;
    
    createAllocationChart(data.portfolio.equity_pct, data.portfolio.bond_pct);
    createBacktestChart(data.backtest, data.profile.amount);
}

function createAllocationChart(equity, bonds) {
    const ctx = document.getElementById('allocationChart').getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Equity', 'Bonds'],
            datasets: [{
                data: [equity, bonds],
                backgroundColor: ['#0088ff', '#f97316'],
                borderWidth: 0,
                cutout: '70%'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: { legend: { display: false }, tooltip: { enabled: false } }
        }
    });
}

function createBacktestChart(backtest, amount) {
    const ctx = document.getElementById('backtestChart').getContext('2d');
    
    const portfolioDates = backtest.portfolio.dates;
    const portfolioValues = backtest.portfolio.values.map(v => (v / 100) * amount);
    const sp500Values = backtest.sp500.values.map(v => (v / 100) * amount);
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: portfolioDates,
            datasets: [
                {
                    label: 'Your Portfolio',
                    data: portfolioValues,
                    borderColor: '#0088ff',
                    backgroundColor: 'rgba(0, 136, 255, 0.1)',
                    borderWidth: 2.5,
                    fill: false,
                    tension: 0.1,
                    pointRadius: 0
                },
                {
                    label: 'S&P 500',
                    data: sp500Values,
                    borderColor: '#dc2626',
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.1,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: { usePointStyle: true, boxWidth: 8 }
                }
            },
            scales: {
                x: {
                    type: 'category',
                    grid: { display: false },
                    ticks: {
                        maxTicksLimit: 6,
                        callback: function(val, index) {
                            const date = this.getLabelForValue(val);
                            return new Date(date).toLocaleDateString('en-US', { 
                                month: 'short', year: '2-digit' 
                            });
                        }
                    }
                },
                y: {
                    grid: { color: '#f0f0f0' },
                    ticks: {
                        callback: v => '$' + v.toLocaleString()
                    }
                }
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', loadPortfolio);

