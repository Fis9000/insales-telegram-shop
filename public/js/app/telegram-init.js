// Добавьте в начало loadProducts.js или в отдельный файл telegram-init.js
if (window.Telegram?.WebApp) {
    // Отключаем стандартные жесты Telegram для свайпа
    window.Telegram.WebApp.setSwipeBehavior('vertical_disabled');
    
    // Также можно попробовать:
    // window.Telegram.WebApp.disableVerticalSwipes();
    
    console.log('[DEBUG] Telegram WebApp swipe behavior configured');
}

// Альтернативный способ через postMessage
function disableTelegramSwipes() {
    if (window.parent !== window) {
        try {
            window.parent.postMessage('{"eventType": "web_app_setup_swipe_behavior", "eventData": {"allow_vertical_swipe": false}}', '*');
        } catch (e) {
            console.warn('Failed to disable Telegram swipes:', e);
        }
    }
}

// Вызывайте при загрузке страницы
document.addEventListener('DOMContentLoaded', disableTelegramSwipes);
