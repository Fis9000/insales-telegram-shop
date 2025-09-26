function showCartCounter() {
    // Получаем параметры
    let userId = null;
    
    // Сначала пробуем получить реальный Telegram ID
    if (window.Telegram?.WebApp?.initDataUnsafe?.user?.id) {
        userId = window.Telegram.WebApp.initDataUnsafe.user.id;
        console.log('Using real Telegram user ID:', userId);
    } else {
        // Для тестирования в браузере используем фиксированный ID
        userId = '123456789';
        console.log('Using test user ID:', userId);
    }
    
    const shopData = document.getElementById('shop-data');
    
    if (!shopData) {
        console.log('No shop data found');
        return;
    }
    
    const insalesId = shopData.dataset.insalesId;
    const shop = shopData.dataset.shop;
    
    console.log('Cart counter params:', { userId, insalesId, shop });
    
    // ИСПОЛЬЗУЕМ ПРАВИЛЬНЫЙ ENDPOINT
    const url = `/cart_count?user_id=${userId}&insales_id=${insalesId}&shop=${shop}`;
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            console.log('Cart count response:', data);
            
            const count = data.count || 0;
            
            // Находим кнопку корзины
            const cartBtn = document.querySelector('.footer-btn[href="/cart"]');
            
            if (!cartBtn) {
                console.log('Cart button not found');
                return;
            }
            
            // Удаляем старый счетчик
            const oldCounter = cartBtn.querySelector('.cart-badge');
            if (oldCounter) {
                oldCounter.remove();
            }
            
            // Добавляем новый счетчик если есть товары
            if (count > 0) {
                const badge = document.createElement('span');
                badge.className = 'cart-badge';
                badge.textContent = count;
                
                // Добавляем стили прямо в JS
                badge.style.cssText = `
                    position: absolute;
                    top: 5px;
                    right: 5px;
                    background: #ff4444;
                    color: white;
                    border-radius: 10px;
                    width: 20px;
                    height: 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 12px;
                    font-weight: bold;
                    z-index: 10;
                `;
                
                cartBtn.appendChild(badge);
                console.log('Cart badge added:', count);
            } else {
                console.log('No items in cart, no badge shown');
            }
        })
        .catch(error => {
            console.error('Cart count error:', error);
        });
}

// Запускаем при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(showCartCounter, 2000);
});

// Экспортируем функцию для вызова из других мест
window.updateCartCounter = showCartCounter;
