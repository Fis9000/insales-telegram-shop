class CollectionsManager {
    constructor() {
        this.collectionsContainer = document.getElementById('collectionsContainer');
        this.collectionsTable = document.getElementById('collectionsTable');
        this.loadingElement = document.getElementById('collectionsLoading');
        this.errorElement = document.getElementById('collectionsError');
    }

    async loadCollections() {
        this.showLoading();
        this.hideError();

        try {
            // Получаем параметры из URL страницы
            const urlParams = new URLSearchParams(window.location.search);
            const insales_id = urlParams.get('insales_id');
            const shop = urlParams.get('shop');

            if (!insales_id || !shop) {
                throw new Error('Параметры insales_id и shop не найдены в URL');
            }

            const url = `/show_collections_admin?insales_id=${encodeURIComponent(insales_id)}&shop=${encodeURIComponent(shop)}`;
            
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const collections = await response.json();
            this.renderCollectionsTable(collections);
            
        } catch (error) {
            console.error('Ошибка загрузки коллекций:', error);
            this.showError('Ошибка загрузки категорий: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    renderCollectionsTable(collections) {
        if (!collections || collections.length === 0) {
            this.collectionsTable.innerHTML = '<div class="no-data">Видимые категории не найдены</div>';
            return;
        }

        const tableHTML = `
            <table class="collections-table">
                <thead>
                    <tr>
                        <th>Название</th>
                        <th>Отображение в телеграм магазине</th>
                    </tr>
                </thead>
                <tbody>
                    ${collections.map(collection => `
                        <tr data-id="${collection.id}">
                            <td class="collection-name">
                                ${this.escapeHtml(collection.title)}
                            </td>
                            <td class="collection-visibility">
                                <label class="checkbox-container">
                                    <input type="checkbox" 
                                           class="visibility-checkbox"
                                           data-id="${collection.id}"
                                           checked>
                                    <span class="checkmark"></span>
                                </label>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        this.collectionsTable.innerHTML = tableHTML;
        this.attachEventListeners();
    }

    attachEventListeners() {
        const checkboxes = this.collectionsTable.querySelectorAll('.visibility-checkbox');
        
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const collectionId = e.target.dataset.id;
                const isVisible = e.target.checked;
                console.log('Изменение видимости коллекции:', collectionId, 'Видимая:', isVisible);
                // Здесь потом добавите обработчик
            });
        });
    }

    showLoading() {
        this.loadingElement.style.display = 'block';
        this.collectionsTable.innerHTML = '';
    }

    hideLoading() {
        this.loadingElement.style.display = 'none';
    }

    showError(message) {
        this.errorElement.textContent = message;
        this.errorElement.style.display = 'block';
        this.collectionsTable.innerHTML = '';
    }

    hideError() {
        this.errorElement.style.display = 'none';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

const collectionsManager = new CollectionsManager();
window.collectionsManager = collectionsManager;
