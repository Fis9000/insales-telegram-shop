(function () {
  // Единое состояние
  const state = {
    initDone: false
  };

  // Безопасный доступ к Telegram.WebApp
  function getTG() {
    if (typeof Telegram === 'undefined' || !Telegram.WebApp) {
      return null;
    }
    return Telegram.WebApp;
  }

  // Стартовая страница — оставим функцию, если логика нужна дальше
  function isStartPage() {
    return document.body.getAttribute('data-start-page') === '1';
  }

  // Обновление CSS-переменных высоты
  function syncViewport() {
    const tg = getTG();
    if (!tg) return;
    document.documentElement.style.setProperty('--tg-viewport-height', tg.viewportHeight + 'px');
    document.documentElement.style.setProperty('--tg-is-expanded', tg.isExpanded ? '1' : '0');
  }

  // Пересинхронизация состояния интерфейса без кнопки Назад
  function syncUiState() {
    window.__goBack = function () {};
  }

  // Первичная инициализация (однократно)
  function initOnce() {
    if (state.initDone) return;

    const tg = getTG();
    if (tg) {
      try { tg.ready(); } catch (_) {}
      try { tg.expand(); } catch (_) {}
      try { tg.enableClosingConfirmation(); } catch (_) {}

      // Вешаем слушатель на изменение viewport через SDK
      try {
        tg.onEvent && tg.onEvent('viewportChanged', syncViewport);
      } catch (_) {}
    }

    // Первичная синхронизация
    syncViewport();

    state.initDone = true;
  }

  // Инициализация на текущем "экране"
  function initForThisPage() {
    initOnce();
    syncUiState();
  }

  // 1) Первая загрузка документа
  document.addEventListener('DOMContentLoaded', initForThisPage);

  // 2) Возврат из истории (bfcache) — пересобираем состояние
  window.addEventListener('pageshow', function () {
    syncViewport();
    syncUiState();
  });

  // 3) Изменение URL без перезагрузки (SPA/роутер)
  window.addEventListener('popstate', function () {
    // Подождём кадр, чтобы DOM обновился
    requestAnimationFrame(syncUiState);
  });

  // 4) Хук для программной навигации в SPA
  window.__syncBackButton = syncUiState; // оставим имя для совместимости
})();
