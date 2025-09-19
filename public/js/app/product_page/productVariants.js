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
            addToCartBtn.addEventListener('click', () => {
                if (!selectedVariant || addToCartBtn.disabled) return;

                // Здесь будет логика добавления в корзину
                console.log('[DEBUG] Adding to cart:', selectedVariant);
                
                // Временная анимация успеха
                const originalText = addToCartBtn.textContent;
                addToCartBtn.textContent = 'Добавлено!';
                addToCartBtn.style.background = '#4CAF50';
                
                setTimeout(() => {
                    addToCartBtn.textContent = originalText;
                    addToCartBtn.style.background = '';
                }, 1500);

                // Здесь можно добавить отправку данных в Telegram или на сервер
                if (window.Telegram?.WebApp) {
                    try {
                        window.Telegram.WebApp.HapticFeedback.impactOccurred('medium');
                        
                        // Отправка данных в бот
                        const productData = {
                            productId: document.getElementById('product-wrapper')?.dataset.productId,
                            variantId: selectedVariant.variantId,
                            variantTitle: selectedVariant.title,
                            price: selectedVariant.price
                        };
                        
                        window.Telegram.WebApp.sendData(JSON.stringify({
                            action: 'add_to_cart',
                            data: productData
                        }));
                    } catch (e) {
                        console.error('Telegram WebApp error:', e);
                    }
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
