document.addEventListener("DOMContentLoaded", () => {
  // --- Инициализация ---
  let userId = window.Telegram?.WebApp?.initDataUnsafe?.user?.id;
  if (!userId) {
    console.warn("Не удалось получить Telegram ID — тестовый режим");
    userId = "123456789";
  }

  const container = document.getElementById("cart-items");
  const emptyBlock = document.querySelector(".no-items");
  const loadingBlock = document.querySelector(".loading");

  // Блоки суммы и кнопки
  const checkoutSummary = document.getElementById("checkout-summary");
  const orderTotalEl = document.getElementById("order-total");
  const checkoutContainer = document.getElementById("checkout-container");
  const checkoutBtn = document.getElementById("checkout-btn");

  // Хранилища
  const quantities = {};   // { [variant_id]: number }
  const prices = {};       // { [variant_id]: number }

  if (loadingBlock) loadingBlock.style.display = "block";
  emptyBlock.style.display = "none";
  container.innerHTML = "";

  const formatRub = (v) => Number(v || 0).toLocaleString("ru-RU") + " ₽";

  // ДОБАВЛЯЕМ ФУНКЦИЮ ОПРЕДЕЛЕНИЯ МАГАЗИНА
  function getShopParams() {
    // Пробуем получить из URL (если есть параметры)
    const urlParams = new URLSearchParams(window.location.search);
    const insalesIdFromUrl = urlParams.get('insales_id');
    const shopFromUrl = urlParams.get('shop');
    
    if (insalesIdFromUrl && shopFromUrl) {
      return { insales_id: insalesIdFromUrl, shop: shopFromUrl };
    }
    
    // Пробуем получить из localStorage (если сохранили ранее)
    const savedShop = localStorage.getItem('current_shop');
    const savedInsalesId = localStorage.getItem('current_insales_id');
    
    if (savedShop && savedInsalesId) {
      return { insales_id: savedInsalesId, shop: savedShop };
    }
    
    // Fallback - используем основной магазин
    return { insales_id: '1030167', shop: '4forms.ru' };
  }

  function recalcTotal() {
    let sum = 0;
    for (const vid in prices) {
      const qty = quantities[vid] || 0;
      const price = prices[vid] || 0;
      sum += price * qty;
    }
    if (orderTotalEl) orderTotalEl.textContent = formatRub(sum);
  }

  function toggleSummaryAndButtonVisibility() {
    const hasItems = !!container.querySelector(".cart-item");
    if (checkoutSummary) checkoutSummary.style.display = hasItems ? "block" : "none";
    if (checkoutContainer) checkoutContainer.style.display = hasItems ? "block" : "none";
  }

  // --- Загрузка корзины С ПАРАМЕТРАМИ МАГАЗИНА ---
  const shopParams = getShopParams();
  console.log('[DEBUG] Loading cart for shop:', shopParams);

  fetch("/cart", {
    method: "POST",
    headers: { 
      "Content-Type": "application/json",
      // ВАЖНО: добавляем параметры магазина в заголовки или body
    },
    body: JSON.stringify({ 
      user_id: userId,
      shop: shopParams.shop,
      insales_id: shopParams.insales_id
    })
  })
    .then(res => {
      console.log('[DEBUG] Cart response status:', res.status);
      return res.json();
    })
    .then(items => {
      console.log('[DEBUG] Cart items received:', items);
      
      if (loadingBlock) loadingBlock.style.display = "none";

      if (!items || items.length === 0) {
        emptyBlock.style.display = "block";
        toggleSummaryAndButtonVisibility();
        return;
      }

      emptyBlock.style.display = "none";

      items.forEach(item => {
        // берём количество из БД, если есть, иначе 1
        const qtyFromDb = (item.quantity ?? 1);
        const safeQty = Number.isFinite(Number(qtyFromDb)) && Number(qtyFromDb) > 0 ? Number(qtyFromDb) : 1;

        const el = document.createElement("div");
        el.className = "cart-item";
        el.innerHTML = `
          <img src="${item.image_0}" alt="${item.product_title}" class="cart-item-img"/>
          <div class="cart-item-info">
            <div class="cart-item-title">${item.product_title}</div>
            <div class="cart-item-variant">${item.variant_title}</div>
            <div class="cart-item-price">${Number(item.variant_price).toLocaleString('ru-RU')} ₽</div>
            <div class="cart-item-quantity">
              <i class="ri-subtract-line qty-btn" data-action="decrease" data-variant-id="${item.variant_id}"></i>
              <span class="qty-value" data-variant-id="${item.variant_id}">${safeQty}</span>
              <i class="ri-add-line qty-btn" data-action="increase" data-variant-id="${item.variant_id}"></i>
            </div>
          </div>
          <i class="ri-close-circle-line delete-btn"
            style="color:#e74c3c; font-size:25px; cursor:pointer;"
            data-variant-id="${item.variant_id}"></i>
        `;
        container.appendChild(el);

        // Инициализация цен и количеств
        prices[item.variant_id] = Number(item.variant_price) || 0;
        quantities[item.variant_id] = safeQty;
      });

      toggleSummaryAndButtonVisibility();
      recalcTotal();
    })
    .catch(err => {
      if (loadingBlock) loadingBlock.style.display = "none";
      console.error("Ошибка при загрузке корзины:", err);
      emptyBlock.style.display = "block";
    });

  // Остальной код остается прежним...
});
