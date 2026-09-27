// ─── UTILITIES ───
const fmt = (n, cur='INR') => new Intl.NumberFormat('en-IN', {style:'currency',currency:cur,maximumFractionDigits:0}).format(n);
const fmtShort = (n) => n >= 100000 ? `${(n/100000).toFixed(1)}L` : n >= 1000 ? `${(n/1000).toFixed(1)}K` : Math.round(n);

function showToast(msg, type='success') {
  const t = document.getElementById('toast');
  t.textContent = msg; t.className = `toast ${type}`;
  setTimeout(() => t.className = 'toast hidden', 3000);
}

function openModal(html) {
  document.getElementById('modal-content').innerHTML = html;
  document.getElementById('modal-overlay').classList.remove('hidden');
}
function closeModal() {
  document.getElementById('modal-overlay').classList.add('hidden');
}
document.getElementById('modal-overlay')?.addEventListener('click', e => {
  if (e.target === document.getElementById('modal-overlay')) closeModal();
});

async function api(url, method='GET', body=null) {
  const opts = { method, headers: {'Content-Type':'application/json'} };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(url, opts);
  return res.json();
}

// ─── CHART DEFAULTS ───
const CHART_COLORS = {
  income: '#00e5a0', expense: '#ff5f6d', info: '#4d9fff',
  palette: ['#00e5a0','#ff5f6d','#4d9fff','#ffa940','#a78bfa','#fb923c','#34d399','#f87171','#60a5fa','#fbbf24','#c084fc','#6b7280']
};
Chart.defaults.color = '#8b93a0';
Chart.defaults.borderColor = 'rgba(255,255,255,0.06)';
Chart.defaults.font.family = "'DM Sans', sans-serif";

function makeLineChart(id, labels, datasets) {
  return new Chart(document.getElementById(id), {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: { intersect: false, mode: 'index' },
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { maxRotation: 0 } },
        y: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { callback: v => '₹' + fmtShort(v) } }
      }
    }
  });
}

function makeBarChart(id, labels, datasets) {
  return new Chart(document.getElementById(id), {
    type: 'bar',
    data: { labels, datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false } },
        y: { grid: { color: 'rgba(255,255,255,0.04)' }, ticks: { callback: v => '₹' + fmtShort(v) } }
      }
    }
  });
}

function makeDoughnutChart(id, labels, data) {
  return new Chart(document.getElementById(id), {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{ data, backgroundColor: CHART_COLORS.palette.slice(0, data.length), borderWidth: 2, borderColor: '#111418' }]
    },
    options: {
      responsive: true, maintainAspectRatio: false, cutout: '70%',
      plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, padding: 12, font: { size: 11 } } } }
    }
  });
}

// ─── CATEGORY EMOJI MAP ───
const CAT_EMOJI = {
  'Food & Dining': '🍜', 'Transport': '🚇', 'Shopping': '🛍️', 'Entertainment': '🎬',
  'Health': '💊', 'Education': '📚', 'Utilities': '💡', 'Housing': '🏠',
  'Travel': '✈️', 'Insurance': '🛡️', 'Savings': '💰', 'Other': '📦',
  'Salary': '💼', 'Freelance': '💻', 'Business': '🏢', 'Investment': '📈',
  'Gift': '🎁', 'Rental': '🏘️'
};

function catEmoji(c) { return CAT_EMOJI[c] || '💳'; }

function txnRow(t, currency='INR') {
  const sign = t.type === 'income' ? '+' : '-';
  return `
  <div class="txn-item" id="txn-${t.id}">
    <div class="txn-cat-icon">${catEmoji(t.category)}</div>
    <div class="txn-info">
      <div class="txn-name">${t.description || t.category}</div>
      <div class="txn-cat">${t.category} &nbsp;·&nbsp; <span class="badge badge-${t.type}">${t.type}</span></div>
    </div>
    <div class="txn-date">${t.date}</div>
    <div class="txn-amount ${t.type}">${sign}${fmt(t.amount, currency)}</div>
    <div class="txn-actions">
      <button class="txn-del-btn" onclick="deleteTxn(${t.id})">✕</button>
    </div>
  </div>`;
}

async function deleteTxn(id) {
  if (!confirm('Delete this transaction?')) return;
  const r = await api(`/api/transactions/${id}`, 'DELETE');
  if (r.success) {
    document.getElementById(`txn-${id}`)?.remove();
    showToast('Transaction deleted');
  }
}
