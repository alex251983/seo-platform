// frontend/src/utils/router.js
export class Router {
    constructor(routes) {
        this.routes = routes;
        this.currentPath = null;
    }

    // Инициализация: обработчик hash-навигации
    init() {
        window.addEventListener('hashchange', () => this.load());
        window.addEventListener('load', () => this.load());
    }

    // Загрузка страницы по хэшу
    async load() {
        const hash = window.location.hash.slice(1) || 'dashboard';
        const route = this.routes[hash];
        
        if (!route) {
            this.render404();
            return;
        }

        // Показываем лоадер
        this.showLoader();
        
        try {
            // Загружаем данные (если есть loader)
            const data = route.loader ? await route.loader() : null;
            
            // Рендерим страницу
            const content = await route.render(data);
            document.getElementById('content').innerHTML = content;
            
            // Инициализируем страницу (если есть init)
            if (route.init) route.init(data);
            
            // Обновляем активный пункт меню
            this.updateNav(hash);
            
        } catch (error) {
            console.error('Router error:', error);
            document.getElementById('content').innerHTML = `
                <div class="empty-state">
                    <div class="icon">❌</div>
                    <h3>Ошибка загрузки</h3>
                    <p>${error.message}</p>
                    <button class="btn btn-primary" onclick="location.reload()">Попробовать снова</button>
                </div>
            `;
        } finally {
            this.hideLoader();
        }
    }

    // Навигация программно
    navigate(path) {
        window.location.hash = path;
    }

    // Обновление активного пункта меню
    updateNav(activeId) {
        document.querySelectorAll('.nav-item').forEach(el => {
            el.classList.toggle('active', el.dataset.page === activeId);
        });
    }

    showLoader() {
        let loader = document.getElementById('page-loader');
        if (!loader) {
            loader = document.createElement('div');
            loader.id = 'page-loader';
            loader.className = 'page-loader';
            loader.innerHTML = '<div class="spinner"></div>';
            document.getElementById('content').appendChild(loader);
        }
        loader.style.display = 'flex';
    }

    hideLoader() {
        const loader = document.getElementById('page-loader');
        if (loader) loader.style.display = 'none';
    }

    render404() {
        document.getElementById('content').innerHTML = `
            <div class="empty-state">
                <div class="icon">🔍</div>
                <h3>Страница не найдена</h3>
                <p>Запрошенный раздел не существует</p>
                <button class="btn btn-primary" onclick="window.location.hash='dashboard'">← На дашборд</button>
            </div>
        `;
    }
}
