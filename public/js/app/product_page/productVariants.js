(function() {
    let selectedVariant = null;

    function initProductVariants() {
        const variantsList = document.querySelector('.product-variants-list');
        const addToCartBtn = document.getElementById('add-to-cart-btn');
        const variantHelper = document.getElementById('variant-helper');

        if (!variantsList) return;

        // Обработчик кликов по вариантам
        variantsList.addEventListener('click', (e) => {
            const variantBtn = e.target.closest('.variant-btn');
            if (!variantBtn || variantBtn.disabled) return;

            // Убираем активный класс у всех вариантов
            variantsList.querySelectorAll('.variant-btn').forEach(btn => {
                btn.classList.remove('selected');
            });

            // Добавляем активный класс к выбранному
            variantBtn.classList.add('selected');

            // Сохраняем данные выбранного варианта
            selectedVariant = {
                variantId: variantBtn.dataset.variantId,
                title: variantBtn.dataset.variantTitle,
                price: variantBtn.dataset.price,
                photoUrl: variantBtn.dataset.photoUrl,
                available: variantBtn.dataset.available === 'true'
            };

            // Активируем кнопку "Добавить в корзину"
            if (addToCartBtn) {
                addToCartBtn.disabled = false;
                addToCartBtn.classList.add('active');
            }

            // Обновляем helper текст
            if (variantHelper) {
                variantHelper.textContent = `Выбран размер: ${selectedVariant.title}`;
            }

            console.log('[DEBUG] Selected variant:', selectedVariant);
        });

        // Обработчик кнопки "Добавить в корзину"
        if (addToCartBtn) {
            addToCartBtn.addEventListener('click', async () => {
                if (!selectedVariant || addToCartBtn.disabled) return;

                console.log('[DEBUG] Adding to cart:', selectedVariant);
                
                // Получаем информацию о магазине
                const currentUrl = window.location.href;
                const match = currentUrl.match(/\/product\/\d+\?insales_id=(\d+)&shop=([^&]+)/);
                
                let insalesId, shop;
                if (match) {
                    insalesId = match[1];
                    shop = match[2];
                } else {
                    const productWrapper = document.getElementById('product-wrapper');
                    if (productWrapper) {
                        insalesId = productWrapper.dataset.insalesId;
                        shop = productWrapper.dataset.shop;
                    }
                }
                
                if (!insalesId || !shop) {
                    console.error('Не удалось определить магазин');
                    return;
                }

                // Сохраняем параметры магазина
                localStorage.setItem('current_shop', shop);
                localStorage.setItem('current_insales_id', insalesId);

                // ВРЕМЕННО БЛОКИРУЕМ КНОПКУ ТОЛЬКО НА ВРЕМЯ ЗАПРОСА
                const originalText = addToCartBtn.textContent;
                addToCartBtn.disabled = true;
                addToCartBtn.textContent = 'Добавление...';

                try {
                    // Отправка на сервер
                    const response = await fetch('/add_to_cart', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            user_id: window.Telegram?.WebApp?.initDataUnsafe?.user?.id || 123456789,
                            product_id: document.getElementById('product-wrapper')?.dataset.productId,
                            variant_id: selectedVariant.variantId,
                            variant_price: selectedVariant.price,
                            image_0: selectedVariant.photoUrl || document.querySelector('.product-gallery-img')?.src || '',
                            variant_title: selectedVariant.title,
                            
                            // ИСПРАВЛЕНО: используем правильный селектор
                            product_title: document.querySelector('.product-title-main')?.textContent?.trim() || 
                                        document.title.split(' - ')[0]?.trim() || 
                                        'Товар',
                            
                            shop: shop,
                            insales_id: insalesId
                        })
                    });

                    console.log('[DEBUG] Add to cart response status:', response.status);
                    const data = await response.json();
                    console.log('[DEBUG] Add to cart response:', data);
                    
                    if (data.status === 'success') {
                        // БЫСТРАЯ АНИМАЦИЯ УСПЕХА БЕЗ БЛОКИРОВКИ
                        addToCartBtn.textContent = 'Добавлено!';
                        addToCartBtn.style.background = '#4CAF50';
                        
                        setTimeout(() => {
                            addToCartBtn.textContent = originalText;
                            addToCartBtn.style.background = '';
                            addToCartBtn.disabled = false; // РАЗБЛОКИРУЕМ КНОПКУ
                        }, 800); // Уменьшаем время до 800ms

                        // === ОБНОВЛЯЕМ СЧЕТЧИК КОРЗИНЫ ===
                        console.log('[DEBUG] Updating cart counter after successful add');
                        if (window.updateCartCounter) {
                            await window.updateCartCounter();
                        } else {
                            console.warn('[DEBUG] updateCartCounter function not found');
                        }

                        // Telegram haptic feedback
                        if (window.Telegram?.WebApp) {
                            try {
                                window.Telegram.WebApp.HapticFeedback.impactOccurred('medium');
                            } catch (e) {
                                console.error('Telegram WebApp error:', e);
                            }
                        }
                    } else {
                        // При ошибке тоже разблокируем кнопку
                        addToCartBtn.textContent = originalText;
                        addToCartBtn.disabled = false;
                        console.error('Failed to add to cart:', data);
                        alert('Ошибка добавления в корзину. Попробуйте еще раз.');
                    }
                } catch (error) {
                    // При ошибке разблокируем кнопку
                    addToCartBtn.textContent = originalText;
                    addToCartBtn.disabled = false;
                    console.error('Ошибка добавления в корзину:', error);
                    alert('Ошибка сети. Попробуйте еще раз.');
                }
            });
        }
    }

    // Публичный API
    window.getSelectedVariant = function() {
        return selectedVariant;
    };

    window.selectVariantById = function(variantId) {
        const variantBtn = document.querySelector(`[data-variant-id="${variantId}"]`);
        if (variantBtn && !variantBtn.disabled) {
            variantBtn.click();
        }
    };

    // Инициализация
    function boot() {
        try { 
            initProductVariants(); 
            console.log('[DEBUG] Product variants initialized');
        } catch (e) {
            console.error('[DEBUG] Product variants error:', e);
        }
    }

    document.addEventListener('DOMContentLoaded', boot);
    window.addEventListener('pageshow', boot);
})();
