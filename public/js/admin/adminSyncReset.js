// public/js/admin/adminSync.js

document.addEventListener('DOMContentLoaded', () => {
  // Привязка кнопок
  bindSyncButton('syncProductsBtn', '/reset_products', 'syncLoading', 'syncStatus');
  bindSyncButton('syncCategoriesBtn', '/reset_collections', 'syncLoadingCats', 'syncStatusCats');
});

/**
 * Привязывает кнопку синхронизации к эндпоинту
 * @param {string} btnId - id кнопки
 * @param {string} endpoint - относительный URL эндпоинта
 * @param {string} loadId - id элемента “загрузка…”
 * @param {string} statusId - id элемента статуса
 */
function bindSyncButton(btnId, endpoint, loadId, statusId) {
  const btn = document.getElementById(btnId);
  if (!btn) {
    console.error('Button not found:', btnId);
    return;
  }
  // Если в разметке указан data-endpoint — используем его, иначе переданный endpoint
  const dataEndpoint = btn.getAttribute('data-endpoint');
  const url = dataEndpoint || endpoint;

  btn.addEventListener('click', () => syncFlow(btn, url, loadId, statusId));
}

/**
 * Читает query-параметр из URL
 */
function getQueryParam(name) {
  const params = new URLSearchParams(window.location.search);
  return params.get(name);
}

/**
 * Возвращает текущий контекст магазина строго из URL
 */
function getCurrentShopContext() {
  const insales_id = getQueryParam('insales_id');
  const shop = getQueryParam('shop');
  return { insales_id, shop };
}

/**
 * Выполняет цикл синхронизации с UI-индикацией
 */
async function syncFlow(btn, url, loadId, statusId) {
  const loadingEl = document.getElementById(loadId);
  const statusEl = document.getElementById(statusId);

  if (!loadingEl || !statusEl) {
    console.error('UI elements not found:', { loadId, statusId });
    return;
  }

  const { insales_id, shop } = getCurrentShopContext();
  if (!insales_id || !shop) {
    setError(statusEl, 'Не найдены параметры магазина (insales_id/shop) в URL. Откройте админку с корректным адресом.');
    return;
  }

  setBusy(btn, loadingEl, true);
  setNeutral(statusEl, 'Запуск синхронизации…');

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ insales_id, shop })
    });

    if (response.ok) {
      const result = await response.json().catch(() => ({}));
      setSuccess(statusEl, result.message || 'Синхронизация завершена');
    } else {
      // Пробуем извлечь подробности ошибки
      let errorText = '';
      try {
        const ct = response.headers.get('Content-Type') || '';
        if (ct.includes('application/json')) {
          const err = await response.json();
          errorText = typeof err.detail === 'string'
            ? err.detail
            : JSON.stringify(err);
        } else {
          errorText = await response.text();
        }
      } catch {
        errorText = `HTTP ${response.status}`;
      }
      setError(statusEl, `Ошибка: ${errorText}`);
    }
  } catch (error) {
    setError(statusEl, 'Ошибка сети: ' + (error?.message || String(error)));
  } finally {
    setBusy(btn, loadingEl, false);
  }
}

/* ---------- UI helpers ---------- */
function setBusy(btn, loadingEl, isBusy) {
  btn.disabled = isBusy;
  btn.setAttribute('aria-busy', String(isBusy));
  loadingEl.style.display = isBusy ? 'inline-block' : 'none';
  btn.classList.toggle('is-busy', isBusy);
}

function setNeutral(statusEl, text) {
  statusEl.textContent = text || '';
  statusEl.className = 'status-text';
}

function setSuccess(statusEl, text) {
  statusEl.textContent = text || '';
  statusEl.className = 'status-text success';
}

function setError(statusEl, text) {
  statusEl.textContent = text || '';
  statusEl.className = 'status-text error';
}
