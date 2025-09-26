document.addEventListener("DOMContentLoaded", () => {
    console.log('[CART] Initializing...');
    
    // --- Инициализация ---
    let userId = window.Telegram?.WebApp?.initDataUnsafe?.user?.id;
    if (!userId) {
        console.warn("Не удалось получить Telegram ID — тестовый режим");
        userId = "123456789";
    }
    
    console.log('[CART] User ID:', userId);
    
    // Получаем параметры магазина
    const shopData = document.getElementById('shop-data');
    if (!shopData) {
        console.error('[CART] No shop data found!');
        return;
    }
    
    const insalesId = shopData.dataset.insalesId;
    const shop = shopData.dataset.shop;
    
    console.log('[CART] Shop params:', { insalesId, shop });
    
    const container = document.getElementById("cart-items");
    const emptyBlock = document.querySelector(".no-items");
    const loadingBlock = document.querySelector(".loading");

    // Блоки суммы и кнопки
    const checkoutSummary = document.getElementById("checkout-summary");
    const orderTotalEl = document.getElementById("order-total");
    const checkoutContainer = document.getElementById("checkout-container");
    const checkoutBtn = document.getElementById("checkout-btn");

    // Хранилища
    const quantities = {}; // { [variant_id]: number }
    const prices = {}; // { [variant_id]: number }

    if (loadingBlock) loadingBlock.style.display = "block";
    emptyBlock.style.display = "none";
    container.innerHTML = "";

    const formatRub = (v) => Number(v || 0).toLocaleString("ru-RU") + " ₽";

    // --- Загрузка корзины ---
    function loadCart() {
        console.log('[CART] Loading cart...');
        
        // ИСПРАВЛЕННЫЙ URL с параметрами магазина
        const url = `/get_user_cart?user_id=${userId}&insales_id=${insalesId}&shop=${shop}`;
        console.log('[CART] Fetching from:', url);
        
        fetch(url, {
            headers: { 'ngrok-skip-browser-warning': 'true' }
        })
        .then(response => {
            console.log('[CART] Response status:', response.status);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json();
        })
        .then(items => {
            console.log('[CART] Items loaded:', items);
            
            if (loadingBlock) loadingBlock.style.display = "none";

            if (!items || items.length === 0) {
                emptyBlock.style.display = "block";
                checkoutSummary.style.display = "none";
                checkoutContainer.style.display = "none";
                return;
            }

            emptyBlock.style.display = "none";
            renderCart(items);
            updateSummary();
            checkoutSummary.style.display = "block";
            checkoutContainer.style.display = "block";
        })
        .catch(error => {
            console.error('[CART] Error loading cart:', error);
            
            if (loadingBlock) loadingBlock.style.display = "none";
            emptyBlock.style.display = "block";
            
            // Показываем ошибку
            emptyBlock.innerHTML = `
                <div style="margin-left: 6px; padding-top: 16px;">Ошибка загрузки корзины</div>
                <div style="margin-left: 6px; padding-top: 10px;">${error.message}</div>
            `;
        });
    }

    // Остальной код остается тем же...
    function renderCart(items) {
        container.innerHTML = "";
        
        items.forEach(item => {
            quantities[item.variant_id] = item.quantity;
            prices[item.variant_id] = item.variant_price;

            const div = document.createElement("div");
            div.className = "cart-item";
            div.dataset.variantId = item.variant_id;

            div.innerHTML = `
                <img class="cart-item-img" src="${item.image_0 || '/placeholder.jpg'}" alt="Product Image" loading="lazy">
                <div class="cart-item-info">
                    <div class="cart-item-title">${item.product_title || 'Товар'}</div>
                    <div class="cart-item-variant">Размер: ${item.variant_title || 'не указан'}</div>
                    <div class="cart-item-price">${formatRub(item.variant_price || 0)}</div>
                </div>
                <div class="delete-btn" data-variant-id="${item.variant_id}">
                    <i class="ri-delete-bin-line"></i>
                </div>
            `;

            container.appendChild(div);
        });

        // Обработчики удаления
        container.querySelectorAll(".delete-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                const variantId = btn.dataset.variantId;
                deleteItem(variantId);
            });
        });
    }

    function deleteItem(variantId) {
        console.log('[CART] Deleting item:', variantId);
        
        const url = `/delete_from_cart?user_id=${userId}&variant_id=${variantId}&insales_id=${insalesId}&shop=${shop}`;
        
        fetch(url, { method: 'DELETE' })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const itemEl = container.querySelector(`[data-variant-id="${variantId}"]`);
                if (itemEl) {
                    itemEl.classList.add('removing');
                    setTimeout(() => {
                        itemEl.remove();
                        delete quantities[variantId];
                        delete prices[variantId];
                        updateSummary();
                        
                        if (Object.keys(quantities).length === 0) {
                            emptyBlock.style.display = "block";
                            checkoutSummary.style.display = "none";
                            checkoutContainer.style.display = "none";
                        }
                        
                        // Обновляем счетчик корзины
                        if (window.updateCartCounter) {
                            window.updateCartCounter();
                        }
                    }, 300);
                }
            }
        })
        .catch(console.error);
    }

    function updateSummary() {
        const total = Object.keys(quantities).reduce((sum, vid) => {
            return sum + (quantities[vid] * (prices[vid] || 0));
        }, 0);
        
        orderTotalEl.textContent = formatRub(total);
    }

    // Обработчик оформления заказа
    if (checkoutBtn) {
        checkoutBtn.addEventListener("click", () => {
            alert("Функция оформления заказа в разработке");
        });
    }

    // Запускаем загрузку корзины
    loadCart();
});
