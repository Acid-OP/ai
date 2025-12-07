// Template data injection
function renderTemplate(data) {
    // Date
    const dateStr = new Date().toLocaleDateString('en-US', { 
        year: 'numeric', month: 'long', day: 'numeric' 
    });
    document.querySelectorAll('[id^="report-date"]').forEach(el => el.textContent = dateStr);
    
    // User info
    document.getElementById('user-name').textContent = data.user?.name || '—';
    document.getElementById('user-email').textContent = data.user?.email || '—';
    document.getElementById('risk-level').textContent = 
        (data.portfolio?.risk_level || '').charAt(0).toUpperCase() + 
        (data.portfolio?.risk_level || '').slice(1);
    document.getElementById('time-horizon').textContent = data.profile?.time_horizon || '—';
    
    // Methodology
    if (data.methodology) {
        document.getElementById('methodology-title').textContent = 
            data.methodology.methodology_title || 'Investment Methodology';
        document.getElementById('methodology-text').textContent = 
            data.methodology.methodology_text || '';
        
        const principlesList = document.getElementById('principles-list');
        principlesList.innerHTML = '';
        (data.methodology.key_principles || []).forEach(p => {
            const li = document.createElement('li');
            li.textContent = p;
            principlesList.appendChild(li);
        });
    }
    
    // Holdings
    const holdingsBody = document.getElementById('holdings-body');
    holdingsBody.innerHTML = '';
    (data.holdings || []).forEach((h, i) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${i + 1}</td>
            <td class="ticker">${h.ticker}</td>
            <td>${h.name}</td>
            <td>${h.weight}%</td>
            <td>${h.category}</td>
        `;
        holdingsBody.appendChild(tr);
    });
    
    // Metrics
    const metrics = data.metrics || {};
    document.getElementById('five-yr-return').textContent = 
        metrics.five_yr_return ? `${metrics.five_yr_return}%` : '—';
    document.getElementById('three-yr-return').textContent = 
        metrics.three_yr_return ? `${metrics.three_yr_return}%` : '—';
    document.getElementById('volatility').textContent = 
        metrics.volatility ? `${metrics.volatility}%` : '—';
    document.getElementById('benchmark-return').textContent = 
        data.benchmark?.five_yr_return ? `${data.benchmark.five_yr_return}%` : '—';
    
    // Volatility marker position (0-30% range)
    const vol = metrics.volatility || 10;
    const markerPos = Math.min(100, (vol / 30) * 100);
    document.getElementById('volatility-marker').style.left = `${markerPos}%`;
    
    // Allocation legend
    const categories = {};
    (data.holdings || []).forEach(h => {
        const cat = h.category || 'Other';
        if (!categories[cat]) categories[cat] = { weight: 0, color: h.color };
        categories[cat].weight += h.weight;
    });
    
    const legendContainer = document.getElementById('allocation-legend');
    legendContainer.innerHTML = '';
    Object.entries(categories).forEach(([name, info]) => {
        const row = document.createElement('div');
        row.className = 'legend-row';
        row.innerHTML = `
            <div class="legend-color" style="background: ${info.color}"></div>
            <span class="legend-name">${name}</span>
            <span class="legend-percent">${info.weight}%</span>
        `;
        legendContainer.appendChild(row);
    });
    
    // Regions
    const regionsList = document.getElementById('regions-list');
    regionsList.innerHTML = '';
    (data.regions || []).slice(0, 6).forEach(r => {
        const item = document.createElement('div');
        item.className = 'breakdown-item';
        item.innerHTML = `
            <span class="breakdown-name">${r.name}</span>
            <div class="breakdown-bar">
                <div class="breakdown-fill" style="width: ${r.percentage}%"></div>
            </div>
            <span class="breakdown-percent">${r.percentage}%</span>
        `;
        regionsList.appendChild(item);
    });
    
    // Top Stocks
    const stocksGrid = document.getElementById('stocks-grid');
    stocksGrid.innerHTML = '';
    (data.top_stocks || []).forEach(s => {
        const item = document.createElement('div');
        item.className = 'stock-item';
        item.innerHTML = `
            <span class="stock-symbol">${s.symbol}</span>
            <span class="stock-weight">${s.weight}%</span>
        `;
        stocksGrid.appendChild(item);
    });
}

// Load data and render when ready
document.addEventListener('DOMContentLoaded', function() {
    if (typeof portfolioData !== 'undefined') {
        renderTemplate(portfolioData);
    }
});

