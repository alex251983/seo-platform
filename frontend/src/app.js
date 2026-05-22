// frontend/src/app.js

// ===== КОНФИГУРАЦИЯ =====
const CONFIG = {
    API_BASE: '/api/v1',
    TOKEN_KEY: 'seo_token',
    MODE_KEY: 'user_mode'
};

// ===== СОСТОЯНИЕ =====
const state = {
    currentMode: localStorage.getItem(CONFIG.MODE_KEY) || 'user',
    currentPage: 'dashboard',
    authToken: localStorage.getItem(CONFIG.TOKEN_KEY),
    userData: null
};

// ===== API КЛИЕНТ =====
const api = {
    async request(endpoint, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        if (state.authToken) {
            headers['Authorization'] = `Bearer ${state.authToken}`;
        }
        
        try {
            const response = await fetch(`${CONFIG.API_BASE}${endpoint}`, {
                ...options,
                headers
            });
            
            if (response.status === 401 || response.status === 403) {
                this.handleAuthError();
                return null;
            }
            
            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail?.message || `HTTP ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            ui.showNotification('error', error.message);
            throw error;
        }
    },
    
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },
    
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    
    handleAuthError() {
        localStorage.removeItem(CONFIG.TOKEN_KEY);
        state.authToken = null;
        state.userData = null;
        ui.showNotification('error', '❌ Сессия истекла. Выполните вход.');
        setTimeout(() => {
            window.location.hash = 'login';
            location.reload();
        }, 1500);
    },
    
    async login(email, password) {
        const data = await this.post('/auth/login', { email, password });
        if (data?.access_token) {
            state.authToken = data.access_token;
            localStorage.setItem(CONFIG.TOKEN_KEY, data.access_token);
            state.userData = data.user || { email };
            return true;
        }
        return false;
    },
    
    logout() {
        localStorage.removeItem(CONFIG.TOKEN_KEY);
        localStorage.removeItem(CONFIG.MODE_KEY);
        state.authToken = null;
        state.userData = null;
        state.currentMode = 'user';
        window.location.hash = 'login';
        location.reload();
    }
};

// ===== UI УТИЛИТЫ =====
const ui = {
    showNotification(type, message) {
        const notif = document.getElementById('notification');
        if (!notif) return;
        
        const icon = notif.querySelector('.notif-icon');
        const text = notif.querySelector('.notif-text');
        
        const icons = {
            success: '✅',
            error: '❌',
            info: 'ℹ️',
            warning: '⚠️'
        };
        
        notif.className = `notification ${type} show`;
        if (icon) icon.textContent = icons[type] || icons.info;
        if (text) text.textContent = message;
        
        setTimeout(() => {
            notif.classList.remove('show');
        }, 3500);
    },
    
    updateNav() {
        const nav = document.getElementById('sidebarNav');
        if (!nav) return;
        
        const config = navConfig[state.currentMode];
        nav.innerHTML = config.map(section => `
            <div class="nav-section">
                <div class="nav-section-title">${section.section}</div>
                ${section.items.map(item => `
                    <div class="nav-item ${state.currentPage === item.id ? 'active' : ''}" 
                         data-page="${item.id}"
                         onclick="router.navigate('${item.id}')">
                        <span class="nav-icon">${item.icon}</span>
                        <span>${item.label}</span>
                        ${item.badge ? `<span class="nav-badge ${item.badgeClass || ''}">${item.badge}</span>` : ''}
                    </div>
                `).join('')}
            </div>
        `).join('');
    },
    
    updateModeSwitcher() {
        document.querySelectorAll('.mode-btn').forEach(btn => {
            const mode = btn.getAttribute('data-mode');
            btn.classList.toggle('active', mode === state.currentMode);
        });
    },
    
    showLoader(show = true) {
        let loader = document.getElementById('page-loader');
        if (!loader) {
            loader = document.createElement('div');
            loader.id = 'page-loader';
            loader.className = 'page-loader';
            loader.innerHTML = '<div class="spinner"></div>';
            document.getElementById('content').appendChild(loader);
        }
        loader.style.display = show ? 'flex' : 'none';
    }
};

// ===== РОУТЕР =====
const router = {
    routes: {
        'dashboard': {
            loader: () => api.get('/stats/summary'),
            render: (data) => pages.dashboard(data),
            init: (data) => charts.initDashboard(data)
        },
        'projects': {
            loader: () => api.get('/projects'),
            render: (data) => pages.projects(data),
            init: () => {}
        },
        'keywords': {
            loader: () => api.get('/keywords'),
            render: (data) => pages.keywords(data),
            init: () => {}
        },
        'audit': {
            loader: () => api.get('/audit/summary'),
            render: (data) => pages.audit(data),
            init: () => {}
        },
        'positions': {
            loader: () => api.get('/positions'),
            render: (data) => pages.positions(data),
            init: (data) => charts.initPositions(data)
        },
        'backlinks': {
            loader: () => api.get('/backlinks'),
            render: (data) => pages.backlinks(data),
            init: () => {}
        },
        'competitors': {
            loader: () => api.get('/competitors'),
            render: (data) => pages.competitors(data),
            init: (data) => charts.initCompetitors(data)
        },
        'reports': {
            loader: () => api.get('/reports'),
            render: (data) => pages.reports(data),
            init: () => {}
        },
        'serp': {
            render: () => pages.serp(),
            init: () => {}
        },
        'login': {
            render: () => pages.login(),
            init: () => auth.initLoginForm()
        },
        // Admin pages
        'admin-dash': {
            loader: () => api.get('/admin/stats'),
            render: (data) => pages.adminDash(data),
            init: (data) => charts.initAdmin(data)
        },
        'users': {
            loader: () => api.get('/admin/users'),
            render: (data) => pages.users(data),
            init: () => {}
        },
        'subscriptions': {
            loader: () => api.get('/admin/subscriptions'),
            render: (data) => pages.subscriptions(data),
            init: () => {}
        },
        'billing': {
            loader: () => api.get('/admin/billing'),
            render: (data) => pages.billing(data),
            init: () => {}
        },
        'server': {
            render: () => pages.server(),
            init: () => {}
        },
        'api': {
            render: () => pages.api(),
            init: () => {}
        },
        'settings': {
            render: () => pages.settings(),
            init: () => {}
        }
    },
    
    async navigate(pageId) {
        const route = this.routes[pageId];
        if (!route) {
            console.error(`Route ${pageId} not found`);
            return;
        }
        
        state.currentPage = pageId;
        ui.updateNav();
        ui.showLoader(true);
        
        try {
            const data = route.loader ? await route.loader() : null;
            const content = document.getElementById('content');
            content.innerHTML = `<div class="page active">${route.render(data)}</div>`;
            
            if (route.init) route.init(data);
            
            // Закрыть мобильное меню
            document.getElementById('sidebar')?.classList.remove('open');
            
        } catch (error) {
            console.error('Navigation error:', error);
            document.getElementById('content').innerHTML = `
                <div class="page active">
                    <div class="empty-state">
                        <div class="icon">❌</div>
                        <h3>Ошибка загрузки</h3>
                        <p>${error.message}</p>
                        <button class="btn btn-primary" onclick="router.navigate('${state.currentPage}')">
                            Повторить
                        </button>
                    </div>
                </div>
            `;
        } finally {
            ui.showLoader(false);
        }
    },
    
    init() {
        window.addEventListener('hashchange', () => {
            const hash = window.location.hash.slice(1) || 'dashboard';
            this.navigate(hash);
        });
        
        window.addEventListener('load', () => {
            const hash = window.location.hash.slice(1) || 'dashboard';
            this.navigate(hash);
        });
    }
};

// ===== АВТОРИЗАЦИЯ =====
const auth = {
    initLoginForm() {
        const form = document.getElementById('loginForm');
        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const email = document.getElementById('loginEmail').value;
                const password = document.getElementById('loginPass').value;
                
                const btn = document.getElementById('loginBtn');
                const originalText = btn.innerHTML;
                btn.innerHTML = '⏳ Вход...';
                btn.disabled = true;
                
                try {
                    const success = await api.login(email, password);
                    if (success) {
                        ui.showNotification('success', '✅ Вход выполнен!');
                        setTimeout(() => {
                            window.location.hash = 'dashboard';
                            location.reload();
                        }, 500);
                    }
                } catch (error) {
                    ui.showNotification('error', '❌ Неверный логин или пароль');
                } finally {
                    btn.innerHTML = originalText;
                    btn.disabled = false;
                }
            });
        }
    },
    
    checkAuth() {
        if (!state.authToken) {
            window.location.hash = 'login';
            return false;
        }
        return true;
    }
};

// ===== ГРАФИКИ =====
const charts = {
    initDashboard(data) {
        if (!data) return;
        
        // Инициализация графика позиций
        const chartEl = document.getElementById('positionsChart');
        if (chartEl && data.chart_data) {
            this.renderBarChart(chartEl, data.chart_data);
        }
    },
    
    initPositions(data) {
        const chartEl = document.getElementById('positionsChart');
        if (chartEl && data) {
            this.renderLineChart(chartEl, data);
        }
    },
    
    initCompetitors(data) {
        const chartEl = document.getElementById('competitorsChart');
        if (chartEl && data) {
            this.renderMultiBarChart(chartEl, data);
        }
    },
    
    initAdmin(data) {
        const chartEl = document.getElementById('registrationsChart');
        if (chartEl && data?.registrations) {
            this.renderBarChart(chartEl, data.registrations);
        }
    },
    
    renderBarChart(element, data) {
        // Простая реализация столбчатого графика
        element.innerHTML = data.map((item, i) => `
            <div class="chart-bar-group">
                <div class="chart-bar purple" style="height:${item.value}%"></div>
                <span class="chart-bar-label">${item.label}</span>
            </div>
        `).join('');
    },
    
    renderLineChart(element, data) {
        // Простая реализация линейного графика
        element.innerHTML = data.map((item, i) => `
            <div class="chart-bar-group">
                <div class="chart-bar green" style="height:${item.value}%"></div>
                <span class="chart-bar-label">${item.label}</span>
            </div>
        `).join('');
    },
    
    renderMultiBarChart(element, data) {
        element.innerHTML = data.map(item => `
            <div class="chart-bar-group">
                <div class="chart-bar purple" style="height:${item.value1}%"></div>
                <div class="chart-bar green" style="height:${item.value2}%; opacity: 0.7"></div>
                <span class="chart-bar-label">${item.label}</span>
            </div>
        `).join('');
    }
};

// ===== СТРАНИЦЫ (рендеры) =====
const pages = {
    login() {
        return `
            <div style="display:flex;align-items:center;justify-content:center;min-height:100vh;background:var(--bg-primary)">
                <div class="card" style="width:100%;max-width:420px;padding:40px">
                    <div style="text-align:center;margin-bottom:32px">
                        <div style="width:60px;height:60px;margin:0 auto 16px;background:linear-gradient(135deg,var(--accent),var(--green));border-radius:16px;display:flex;align-items:center;justify-content:center;font-size:28px;font-weight:800;color:white;box-shadow:0 4px 20px var(--accent-glow)">R</div>
                        <h2 style="margin:0 0 8px">Вход в RankPulse</h2>
                        <p style="color:var(--text-muted)">SEO-платформа нового поколения</p>
                    </div>
                    <form id="loginForm">
                        <div class="form-group">
                            <label class="form-label">Email</label>
                            <input class="form-input" type="email" id="loginEmail" placeholder="you@example.com" value="newuser@seoviden.ru" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Пароль</label>
                            <input class="form-input" type="password" id="loginPass" placeholder="••••••••" value="NewUser1234" required>
                        </div>
                        <button type="submit" class="btn btn-primary" id="loginBtn" style="width:100%;margin-top:8px">
                            Войти
                        </button>
                    </form>
                    <p style="text-align:center;margin-top:16px;font-size:13px;color:var(--text-muted)">
                        Нет аккаунта? <a href="#" onclick="ui.showNotification('info','📧 Обратитесь к администратору')" style="color:var(--accent-light)">Связаться с поддержкой</a>
                    </p>
                </div>
            </div>
        `;
    },
    
    dashboard(data) {
        const stats = data || {
            projects_count: 12,
            top10_keywords: 342,
            avg_traffic: 14200,
            seo_score: 78,
            projects_growth: 2,
            top10_growth: 28,
            traffic_growth: 12.4,
            score_growth: 5
        };
        
        return `
            <div class="page-header">
                <div class="page-title">
                    <h1>Добро пожаловать! 👋</h1>
                    <p>Сводка ваших SEO-проектов за последние 7 дней</p>
                </div>
                <div class="page-actions">
                    <button class="btn btn-secondary" onclick="ui.showNotification('info','📊 Отчёт формируется...')">📥 Экспорт</button>
                    <button class="btn btn-primary" onclick="router.navigate('projects')">➕ Новый проект</button>
                </div>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card purple">
                    <div class="stat-header">
                        <span class="stat-label">Всего проектов</span>
                        <div class="stat-icon purple">📁</div>
                    </div>
                    <div class="stat-value">${stats.projects_count}</div>
                    <span class="stat-change ${stats.projects_growth >= 0 ? 'up' : 'down'}">
                        ${stats.projects_growth >= 0 ? '↑' : '↓'} ${Math.abs(stats.projects_growth)} за месяц
                    </span>
                </div>
                <div class="stat-card green">
                    <div class="stat-header">
                        <span class="stat-label">Ключей в ТОП-10</span>
                        <div class="stat-icon green">🏆</div>
                    </div>
                    <div class="stat-value">${stats.top10_keywords}</div>
                    <span class="stat-change up">↑ +${stats.top10_growth} (${stats.top10_growth}%)</span>
                </div>
                <div class="stat-card orange">
                    <div class="stat-header">
                        <span class="stat-label">Средний трафик</span>
                        <div class="stat-icon orange">👥</div>
                    </div>
                    <div class="stat-value">${this.formatNumber(stats.avg_traffic)}</div>
                    <span class="stat-change up">↑ +${stats.traffic_growth}%</span>
                </div>
                <div class="stat-card blue">
                    <div class="stat-header">
                        <span class="stat-label">SEO Score</span>
                        <div class="stat-icon blue">📈</div>
                    </div>
                    <div class="stat-value">${stats.seo_score}</div>
                    <span class="stat-change up">↑ +${stats.score_growth} pts</span>
                </div>
            </div>
            
            <div class="grid-3">
                <div class="card">
                    <div class="card-header">
                        <div>
                            <div class="card-title">Динамика позиций</div>
                            <div class="card-subtitle">Средняя позиция за 12 недель</div>
                        </div>
                    </div>
                    <div class="chart-container">
                        <div class="chart-bars" id="positionsChart"></div>
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
                                    stroke-dashoffset="${326.73 * (1 - stats.seo_score / 100)}"/>
                                <defs>
                                    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="0%">
                                        <stop offset="0%" style="stop-color:#6c5ce7"/>
                                        <stop offset="100%" style="stop-color:#00cec9"/>
                                    </linearGradient>
                                </defs>
                            </svg>
                            <div class="value">${stats.seo_score}</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },
    
    projects(data) {
        const projects = data || [];
        return `
            <div class="page-header">
                <div class="page-title">
                    <h1>Проекты</h1>
                    <p>Управление вашими SEO-проектами</p>
                </div>
                <div class="page-actions">
                    <button class="btn btn-secondary">📥 Импорт</button>
                    <button class="btn btn-primary" onclick="modals.open('project')">➕ Новый проект</button>
                </div>
            </div>
            
            <div class="card">
                <div class="card-body no-pad">
                    <div class="table-wrapper">
                        <table>
                            <thead>
                                <tr>
                                    <th>Проект</th>
                                    <th>Домен</th>
                                    <th>Ключей</th>
                                    <th>ТОП-10</th>
                                    <th>Трафик</th>
                                    <th>SEO Score</th>
                                    <th>Статус</th>
                                    <th>Действия</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${projects.length ? projects.map(p => this.renderProjectRow(p)).join('') : '<tr><td colspan="8" style="text-align:center;padding:40px;color:var(--text-muted)">Нет проектов</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
    },
    
    renderProjectRow(project) {
        return `
            <tr>
                <td><strong>${project.name || 'TechStore'}</strong></td>
                <td style="color:var(--text-muted)">${project.domain || 'techstore.ru'}</td>
                <td>${project.keywords_count || 245}</td>
                <td><strong style="color:var(--green)">${project.top10_percent || 89}%</strong></td>
                <td>${this.formatNumber(project.traffic || 8400)}</td>
                <td>
                    <div style="display:flex;align-items:center;gap:8px">
                        <div class="progress-bar" style="width:80px">
                            <div class="progress-fill green" style="width:${project.seo_score || 85}%"></div>
                        </div>
                        <span style="font-weight:700;font-size:13px">${project.seo_score || 85}</span>
                    </div>
                </td>
                <td><span class="status active"><span class="status-dot"></span>Активен</span></td>
                <td><button class="btn-icon">⋯</button></td>
            </tr>
        `;
    },
    
    keywords(data) {
        return `
            <div class="page-header">
                <div class="page-title">
                    <h1>Ключевые слова</h1>
                    <p>Мониторинг позиций</p>
                </div>
            </div>
            <div class="card">
                <div class="card-body">
                    <p style="color:var(--text-muted);text-align:center;padding:40px">
                        Страница в разработке. Данные будут загружены из API.
                    </p>
                </div>
            </div>
        `;
    },
    
    audit(data) {
        return `
            <div class="page-header">
                <div class="page-title">
                    <h1>Аудит сайта</h1>
                    <p>Проверка технического состояния</p>
                </div>
            </div>
            <div class="card">
                <div class="card-body">
                    <p style="color:var(--text-muted);text-align:center;padding:40px">
                        Страница в разработке.
                    </p>
                </div>
            </div>
        `;
    },
    
    positions(data) {
        return `
            <div class="page-header">
                <div class="page-title">
                    <h1>Позиции</h1>
                    <p>Отслеживание позиций ключевых слов</p>
                </div>
            </div>
            <div class="card">
                <div class="chart-container">
                    <div class="chart-bars" id="positionsChart"></div>
                </div>
            </div>
        `;
    },
    
    backlinks(data) {
        return `<div class="page-header"><div class="page-title"><h1>Бэклинки</h1></div></div><div class="card"><div class="card-body"><p style="text-align:center;color:var(--text-muted);padding:40px">В разработке</p></div></div>`;
    },
    
    competitors(data) {
        return `<div class="page-header"><div class="page-title"><h1>Конкуренты</h1></div></div><div class="card"><div class="card-body"><p style="text-align:center;color:var(--text-muted);padding:40px">В разработке</p></div></div>`;
    },
    
    reports(data) {
        return `<div class="page-header"><div class="page-title"><h1>Отчёты</h1></div></div><div class="card"><div class="card-body"><p style="text-align:center;color:var(--text-muted);padding:40px">В разработке</p></div></div>`;
    },
    
    serp() {
        return `<div class="page-header"><div class="page-title"><h1>SERP Checker</h1></div></div><div class="card"><div class="card-body"><p style="text-align:center;color:var(--text-muted);padding:40px">В разработке</p></div></div>`;
    },
    
    // Admin pages
    adminDash(data) {
        return `<div class="page-header"><div class="page-title"><h1>Админ-панель ⚙️</h1></div></div><div class="card"><div class="card-body"><p style="text-align:center;color:var(--text-muted);padding:40px">Админ-панель в разработке</p></div></div>`;
    },
    
    users(data) {
        return `<div class="page-header"><div class="page-title"><h1>Пользователи</h1></div></div><div class="card"><div class="card-body"><p style="text-align:center;color:var(--text-muted);padding:40px">В разработке</p></div></div>`;
    },
    
    subscriptions(data) {
        return `<div class="page-header"><div class="page-title"><h1>Подписки</h1></div></div><div class="card"><div class="card-body"><p style="text-align:center;color:var(--text-muted);padding:40px">В разработке</p></div></div>`;
    },
    
    billing(data) {
        return `<div class="page-header"><div class="page-title"><h1>Биллинг</h1></div></div><div class="card"><div class="card-body"><p style="text-align:center;color:var(--text-muted);padding:40px">В разработке</p></div></div>`;
    },
    
    server() {
        return `<div class="page-header"><div class="page-title"><h1>Серверы</h1></div></div><div class="card"><div class="card-body"><p style="text-align:center;color:var(--text-muted);padding:40px">В разработке</p></div></div>`;
    },
    
    api() {
        return `<div class="page-header"><div class="page-title"><h1>API Статус</h1></div></div><div class="card"><div class="card-body"><p style="text-align:center;color:var(--text-muted);padding:40px">В разработке</p></div></div>`;
    },
    
    settings() {
        return `<div class="page-header"><div class="page-title"><h1>Настройки</h1></div></div><div class="card"><div class="card-body"><p style="text-align:center;color:var(--text-muted);padding:40px">В разработке</p></div></div>`;
    },
    
    formatNumber(num) {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toString();
    }
};

// ===== МОДАЛЬНЫЕ ОКНА =====
const modals = {
    open(type) {
        const overlay = document.getElementById('modalOverlay');
        if (!overlay) return;
        
        const titles = {
            project: '➕ Новый проект',
            keyword: '➕ Добавить ключи',
            audit: '🔍 Запустить аудит'
        };
        
        document.getElementById('modalTitle').textContent = titles[type] || 'Модальное окно';
        document.getElementById('modalBody').innerHTML = '<p>Содержимое загружается...</p>';
        document.getElementById('modalFooter').innerHTML = '<button class="btn btn-secondary" onclick="modals.close()">Закрыть</button>';
        
        overlay.classList.add('active');
    },
    
    close() {
        document.getElementById('modalOverlay')?.classList.remove('active');
    }
};

// ===== НАВИГАЦИОННАЯ КОНФИГУРАЦИЯ =====
const navConfig = {
    user: [
        { section: 'Основное', items: [
            { id: 'dashboard', icon: '📊', label: 'Дашборд' },
            { id: 'projects', icon: '📁', label: 'Проекты', badge: '12' },
            { id: 'keywords', icon: '🔑', label: 'Ключевые слова', badge: '847', badgeClass: 'green' },
            { id: 'audit', icon: '🔍', label: 'Аудит сайта', badge: '3', badgeClass: 'red' }
        ]},
        { section: 'Аналитика', items: [
            { id: 'positions', icon: '📈', label: 'Позиции' },
            { id: 'backlinks', icon: '🔗', label: 'Бэклинки' },
            { id: 'competitors', icon: '⚔️', label: 'Конкуренты' },
            { id: 'reports', icon: '📋', label: 'Отчёты' }
        ]},
        { section: 'Инструменты', items: [
            { id: 'serp', icon: '🌐', label: 'SERP Checker' }
        ]}
    ],
    admin: [
        { section: 'Управление', items: [
            { id: 'admin-dash', icon: '📊', label: 'Обзор' },
            { id: 'users', icon: '👥', label: 'Пользователи' },
            { id: 'subscriptions', icon: '💳', label: 'Подписки' },
            { id: 'billing', icon: '💰', label: 'Биллинг' }
        ]},
        { section: 'Мониторинг', items: [
            { id: 'server', icon: '🖥️', label: 'Серверы' },
            { id: 'api', icon: '🔌', label: 'API Статус' }
        ]},
        { section: 'Настройки', items: [
            { id: 'settings', icon: '⚙️', label: 'Настройки' }
        ]}
    ]
};

// ===== ИНИЦИАЛИЗАЦИЯ =====
function initApp() {
    // Обновляем UI
    ui.updateNav();
    ui.updateModeSwitcher();
    
    // Инициализируем роутер
    router.init();
    
    // Обработчик переключения режима
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const mode = btn.getAttribute('data-mode');
            if (mode !== state.currentMode) {
                state.currentMode = mode;
                localStorage.setItem(CONFIG.MODE_KEY, mode);
                ui.updateNav();
                ui.updateModeSwitcher();
                router.navigate(state.currentPage === 'login' ? 'dashboard' : state.currentPage);
            }
        });
    });
    
    // Обработчик выхода
    document.getElementById('logoutBtn')?.addEventListener('click', () => {
        if (confirm('Выйти из аккаунта?')) {
            api.logout();
        }
    });
    
    console.log('✅ RankPulse initialized');
}

// Запуск приложения
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}

// Экспорт для глобального доступа
window.router = router;
window.api = api;
window.ui = ui;
window.auth = auth;
window.modals = modals;
window.navConfig = navConfig;
