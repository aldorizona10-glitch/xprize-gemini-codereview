// CodeLens AI — Frontend Logic
const API_BASE = '';

async function submitReview() {
    const code = document.getElementById('code-input').value.trim();
    const language = document.getElementById('language-select').value;
    const btn = document.getElementById('review-btn');
    const output = document.getElementById('review-output');

    if (!code) {
        output.innerHTML = '<div class="output-placeholder"><p>⚠️ Please paste some code first!</p></div>';
        return;
    }

    // Show loading
    btn.querySelector('.btn-text').style.display = 'none';
    btn.querySelector('.btn-loading').style.display = 'inline';
    btn.disabled = true;
    output.innerHTML = '<div class="loading-bar"></div><div class="loading-bar" style="width:70%"></div><div class="loading-bar" style="width:40%"></div><p style="text-align:center;color:var(--text-secondary);margin-top:20px">🤖 Gemini is analyzing your code...</p>';

    try {
        const res = await fetch(`${API_BASE}/api/review`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code, language })
        });
        const data = await res.json();
        renderReview(data);
        loadStats();
    } catch (err) {
        output.innerHTML = `<div class="output-placeholder"><p>❌ Error: ${err.message}</p><p style="font-size:12px;color:var(--text-secondary)">Make sure the server is running</p></div>`;
    } finally {
        btn.querySelector('.btn-text').style.display = 'inline';
        btn.querySelector('.btn-loading').style.display = 'none';
        btn.disabled = false;
    }
}

function renderReview(data) {
    const output = document.getElementById('review-output');
    const score = data.score || 0;
    const scoreClass = score >= 75 ? 'score-high' : score >= 50 ? 'score-mid' : 'score-low';

    let issuesHTML = '';
    (data.issues || []).forEach(issue => {
        const sev = issue.severity || 'info';
        issuesHTML += `
            <div class="issue-item issue-${sev}">
                <div class="issue-header">
                    <span class="issue-title">${issue.title}</span>
                    <span class="issue-badge badge-${sev}">${sev}${issue.line ? ` L${issue.line}` : ''}</span>
                </div>
                <div class="issue-desc">${issue.description}</div>
                <div class="issue-fix">💡 ${issue.suggestion}</div>
            </div>
        `;
    });

    let strengthsHTML = (data.strengths || []).map(s => `<li>✅ ${s}</li>`).join('');
    let recsHTML = (data.recommendations || []).map(r => `<li>→ ${r}</li>`).join('');

    output.innerHTML = `
        <div class="review-score">
            <div class="score-circle ${scoreClass}">${score}</div>
            <div style="font-size:12px;color:var(--text-secondary)">${data.lines_reviewed || 0} lines • ${data.language || 'unknown'}</div>
        </div>
        <div class="review-summary">${data.summary || 'Review complete.'}</div>
        <h4 style="margin-bottom:8px;font-size:14px">Issues (${(data.issues||[]).length})</h4>
        ${issuesHTML}
        ${data.strengths ? `<h4 style="margin:16px 0 8px;font-size:14px">Strengths</h4><ul style="font-size:13px;padding-left:16px">${strengthsHTML}</ul>` : ''}
        ${data.recommendations ? `<h4 style="margin:16px 0 8px;font-size:14px">Recommendations</h4><ul style="font-size:13px;padding-left:16px;color:var(--text-secondary)">${recsHTML}</ul>` : ''}
        <div style="margin-top:16px;padding:8px 12px;background:var(--glass);border-radius:8px;font-size:11px;color:var(--text-secondary);text-align:center">
            ${data.powered_by || 'CodeLens AI'} • Review ID: ${data.review_id || '—'}
        </div>
    `;
}

async function loadStats() {
    try {
        const res = await fetch(`${API_BASE}/api/stats`);
        const data = await res.json();

        const setNum = (id, val) => {
            const el = document.getElementById(id);
            if (el) el.textContent = typeof val === 'number' ? val.toLocaleString() : val;
        };

        setNum('stat-reviews', data.total_reviews);
        setNum('stat-lines', data.lines_reviewed);
        setNum('stat-issues', data.issues_found);
        setNum('stat-score', data.avg_score || '—');
        setNum('hero-reviews', data.total_reviews);
        setNum('hero-lines', data.lines_reviewed);
        setNum('hero-issues', data.issues_found);

        // Load recent reviews
        const reviewsRes = await fetch(`${API_BASE}/api/reviews?limit=5`);
        const reviewsData = await reviewsRes.json();
        const list = document.getElementById('reviews-list');
        if (list && reviewsData.reviews) {
            list.innerHTML = reviewsData.reviews.map(r => `
                <div class="review-item">
                    <div>
                        <strong>${r.language || 'code'}</strong> — Score: ${r.score}/100
                        <div class="review-meta">${r.lines_reviewed} lines • ${(r.issues||[]).length} issues</div>
                    </div>
                    <span class="issue-badge badge-${r.score >= 75 ? 'style' : r.score >= 50 ? 'warning' : 'critical'}">${r.score >= 75 ? 'Good' : r.score >= 50 ? 'Fair' : 'Needs Work'}</span>
                </div>
            `).join('');
        }
    } catch (e) {
        console.log('Stats not loaded:', e.message);
    }
}

// Load stats on page load
document.addEventListener('DOMContentLoaded', loadStats);
// Refresh stats every 30s
setInterval(loadStats, 30000);
