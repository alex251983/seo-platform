// frontend/src/pages/dashboard.js
import { API } from '../api/client.js';
import { renderChart } from '../components/charts.js';

export const DashboardPage = {
    // Загрузка данных с бэкенда
    async loader() {
        const [stats, activity, positions] = await Promise.all([
            API.get('/stats/summary').catch(() => null),
            API.get('/activity/recent').catch(() => null),
            API.get('/positions/changes?limit=5').catch(() => null)
        ]);
        
        return { stats, activity, positions };
    },
    
    // Рендер страницы
    render(data) {
        const { stats, activity, positions } = data || {};
        
        return `
            <div class="page-header">
                <div class="page-title">
                    <h1>Добро пожаловать! 👋</h1>
                    <p>Сводка ваших SEO-проектов за последние 7 дней</p>
                </div>
                <div class="page-actions">
                    <button class="btn btn-secondary" onclick="exportReport()">📥 Экспорт</button>
                    <button class="btn btn-primary" onclick="window.location.hash='projects'">➕ Новый проект</button>
                </div>
            </div>

            <!-- Статистика (реальные данные или заглушки) -->
            <div class="stats-grid">
                <div class="stat-card purple">
                    <div class="stat-header">
                        <span class="stat-label">Всего проектов</span>
                        <div class="stat-icon purple">📁</div>
                    </div>
                    <div class="stat-value">${stats?.projects_count ?? '—'}</div>
                    <span class="stat-change ${stats?.projects_growth >= 0 ? 'up' : 'down'}">
                        ${stats?.projects_growth >= 0 ? '↑' : '↓'} ${Math.abs(stats?.projects_growth ?? 0)} за месяц
                    </span>
                </div>
                <div class="stat-card green">
                    <div class="stat-header">
                        <span class="stat-label">Ключей в ТОП-10</span>
                        <div class="stat-icon green">🏆</div>
                    </div>
                    <div class="stat-value">${stats?.top10_keywords ?? '—'}</div>
                    <span class="stat-change up">↑ +${stats?.top10_growth ?? 0} (${stats?.top10_percent ?? 0}%)</span>
                </div>
                <div class="stat-card orange">
                    <div class="stat-header">
                        <span class="stat-label">Средний трафик</span>
                        <div class="stat-icon orange">👥</div>
                    </div>
                    <div class="stat-value">${formatNumber(stats?.avg_traffic ?? 0)}</div>
                    <span class="stat-change up">↑ +${stats?.traffic_growth ?? 0}%</span>
                </div>
                <div class="stat-card blue">
                    <div class="stat-header">
                        <span class="stat-label">SEO Score</span>
                        <div class="stat-icon blue">📈</div>
                    </div>
                    <div class="stat-value">${stats?.seo_score ?? '—'}</div>
                    <span class="stat-change up">↑ +${stats?.score_growth ?? 0} pts</span>
                </div>
            </div>

            <!-- Графики и таблицы -->
            <div class="grid-3">
                <div class="card">
                    <div class="card-header">
                        <div>
                            <div class="card-title">Динамика позиций</div>
                            <div class="card-subtitle">Средняя позиция за 12 недель</div>
                        </div>
                        <div class="tabs">
                            <button class="tab active" data-period="12w">12 недель</button>
                            <button class="tab" data-period="4w">4 недели</button>
                        </div>
                    </div>
                    <div class="chart-container">
                        <canvas id="positionsChart" height="180"></canvas>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <div>
                            <div class="card-title">SEO Score</div>
                            <div class="card-subtitle">Общая оценка</div>
                        </div>
                    </div>
                    <div class="card-body" style="text-align:center">
                        <div class="score-ring">
                            <svg viewBox="0 0 120 120">
                                <circle class="bg" cx="60" cy="60" r="52"/>
                                <circle class="fill" cx="60" cy="60" r="52"
                                    stroke="url(#grad1)" stroke-dasharray="326.73"
                                    stroke-dashoffset="${326.73 * (1 - (stats?.seo_score ?? 0) / 100)}"/>
                                <defs>
                                    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="0%">
                                        <stop offset="0%" style="stop-color:#6c5ce7"/>
                                        <stop offset="100%" style="stop-color:#00cec9"/>
                                    </linearGradient>
                                </defs>
                            </svg>
                            <div class="value">${stats?.seo_score ?? '—'}</div>
                        </div>
                        <!-- Прогресс-бары категорий -->
                        ${renderScoreBreakdown(stats?.breakdown)}
                    </div>
                </div>
            </div>

            <!-- Таблица изменений позиций -->
            <div class="card">
                <div class="card-header">
                    <div>
                        <div class="card-title">Последние изменения позиций</div>
                        <div class="card-subtitle">Обновлено ${formatTime(stats?.last_update)}</div>
                    </div>
                    <button class="btn btn-secondary btn-sm" onclick="window.location.hash='positions'">Все →</button>
                </div>
                <div class="card-body no-pad">
                    <div class="table-wrapper">
                        <table>
                            <thead>
                                <tr><th>Ключевое слово</th><th>Позиция</th><th>Δ</th><th>Проект</th></tr>
                            </thead>
                            <tbody>
                                ${(positions?.items ?? []).map(item => `
                                    <tr>
                                        <td style="font-weight:600">${escapeHtml(item.keyword)}</td>
                                        <td><strong>${item.position}</strong></td>
                                        <td><span class="stat-change ${item.delta >= 0 ? 'up' : 'down'}">
                                            ${item.delta >= 0 ? '↑' : '↓'} ${Math.abs(item.delta)}
                                        </span></td>
                                        <td><span class="status info">${escapeHtml(item.project)}</span></td>
                                    </tr>
                                `).join('') || '<tr><td colspan="4" style="text-align:center;color:var(--text-muted)">Нет данных</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
    },
    
    // Инициализация после рендера
    init(data) {
        // Инициализация графика
        if (data?.positions?.chart_data) {
            renderChart('positionsChart', {
                type: 'bar',
                data: data.positions.chart_data,
                options: {
                    responsive: true,
                    scales: {
                        y: { beginAtZero: true, reverse: true }
                    }
                }
            });
        }
    }
};

// Вспомогательные функции
function formatNumber(num) {
    if (num >= 1_000_000) return (num / 1_000_000).toFixed(1) + 'M';
    if (num >= 1_000) return (num / 1_000).toFixed(1) + 'K';
    return num.toString();
}

function formatTime(isoString) {
    if (!isoString) return '—';
    const date = new Date(isoString);
    const now = new Date();
    const diff = (now - date) / 1000;
    
    if (diff < 60) return 'только что';
    if (diff < 3600) return `${Math.floor(diff / 60)} мин назад`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} ч назад`;
    return date.toLocaleDateString('ru-RU');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function renderScoreBreakdown(breakdown = {}) {
    const items = [
        { label: 'Тех. SEO', key: 'technical', color: 'green' },
        { label: 'Контент', key: 'content', color: 'purple' },
        { label: 'Бэклинки', key: 'backlinks', color: 'orange' },
        { label: 'UX сигналы', key: 'ux', color: 'blue' }
    ];
    
    return items.map(item => `
        <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:8px">
            <span style="color:var(--text-secondary)">${item.label}</span>
            <span style="font-weight:700">${breakdown[item.key] ?? '—'}%</span>
        </div>
        <div class="progress-bar">
            <div class="progress-fill ${item.color}" style="width:${breakdown[item.key] ?? 0}%"></div>
        </div>
    `).join('');
}

async function exportReport() {
    try {
        const blob = await API.get('/reports/export?format=pdf');
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `seo-report-${new Date().toISOString().slice(0,10)}.pdf`;
        a.click();
        URL.revokeObjectURL(url);
    } catch (e) {
        alert('Ошибка экспорта: ' + e.message);
    }
}
