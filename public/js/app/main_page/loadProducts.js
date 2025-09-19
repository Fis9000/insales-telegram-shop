const PAGE_SIZE = 12;

let feedState = {
    mode: "all",
    collectionId: null,
    offset: 0,
    hasMore: true,
    loading: false,
    q: ""
};

const productsArea = document.getElementById("productsArea");
let sentinel = null;
let listObserver = null;
let imageObserver = null;

function resetFeed(){
    feedState.offset = 0;
    feedState.hasMore = true;
    feedState.loading = false;
    productsArea.innerHTML = "";

    if (listObserver){ listObserver.disconnect(); listObserver=null; }
    if (imageObserver){ imageObserver.disconnect(); imageObserver=null; }
    if (sentinel && sentinel.parentNode) sentinel.parentNode.removeChild(sentinel);

    sentinel = document.createElement("div");
    sentinel.id = "products-sentinel";
    sentinel.style.height = "1px";
    productsArea.after(sentinel);
}

// Цены с пробелом
function formatRub(value) {
    try {
        return Number(value).toLocaleString('ru-RU');
    } catch {
        return String(value ?? '');
    }
}

function createCard(p){
    const card = document.createElement("div");
    card.className = "product-card";
    card.dataset.productId = String(p.product_id);

    const slider = document.createElement("div");
    slider.className = "product-slider";

    const track = document.createElement("div");
    track.className = "product-slider__track";

    const images = Array.isArray(p.images) && p.images.length ? p.images : [p.image_0].filter(Boolean);
    
    // Если нет изображений, добавляем заглушку
    if (images.length === 0) {
        images.push('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="150" height="150"><rect width="150" height="150" fill="%23f0f0f0"/><text x="75" y="75" text-anchor="middle" fill="%23999">Нет фото</text></svg>');
    }
    
    images.forEach((url) => {
        const slide = document.createElement("div");
        slide.className = "product-slide";
        const img = document.createElement("img");
        img.alt = p.title || "";
        img.loading = "lazy";
        img.dataset.src = url;
        slide.appendChild(img);
        track.appendChild(slide);
    });

    slider.appendChild(track);

    const dots = document.createElement("div");
    dots.className = "product-slider__dots";
    images.forEach((_, i) => {
        const dot = document.createElement("button");
        dot.type = "button";
        dot.className = "dot" + (i===0 ? " active" : "");
        dot.dataset.index = String(i);
        dots.appendChild(dot);
    });

    const title = document.createElement("div");
    title.className = "product-title";
    title.textContent = p.title || "";

    const price = document.createElement("div");
    price.className = "product-price";
    if (p.base_price != null) {
        const formatted = formatRub(p.base_price);
        price.textContent = `${formatted} ₽`;
    } else {
        price.textContent = "";
    }

    card.appendChild(slider);
    card.appendChild(dots);
    card.appendChild(title);
    card.appendChild(price);

    card.dataset.slideIndex = "0";
    setSlide(card, 0);
    return card;
}

function ensureObservers(){
    const rootEl = document.querySelector(".scroll-area") || null;

    imageObserver = new IntersectionObserver((entries, obs) => {
        entries.forEach(e => {
            if (!e.isIntersecting) return;
            const img = e.target;
            const src = img.dataset.src;
            if (src){
                img.src = src;
                img.removeAttribute("data-src");
            }
            obs.unobserve(img);
        });
    }, { root: rootEl, rootMargin: "200px 0px", threshold: 0.01 });

    listObserver = new IntersectionObserver((entries) => {
        entries.forEach(e => { if (e.isIntersecting) loadNextPage(); });
    }, { root: rootEl, rootMargin: "400px 0px", threshold: 0 });

    listObserver.observe(sentinel);
}

async function loadNextPage(){
    if (feedState.loading || !feedState.hasMore) return;
    feedState.loading = true;
    
    try{
        const params = new URLSearchParams();
        params.set("limit", String(PAGE_SIZE));
        params.set("offset", String(feedState.offset));
        if (feedState.mode === "collection" && feedState.collectionId){
            params.set("collection_id", String(feedState.collectionId));
        }
        if (feedState.q) params.set("q", feedState.q);

        const res = await fetch(`/show_products?${params.toString()}`);
        if (!res.ok) throw new Error("HTTP " + res.status);
        const data = await res.json();

        const items = data.items || [];
        const frag = document.createDocumentFragment();
        const cards = [];
        for (const p of items){
            const card = createCard(p);
            frag.appendChild(card);
            cards.push(card);
        }
        productsArea.appendChild(frag);

        cards.forEach(card => {
            card.querySelectorAll("img[data-src]").forEach(img => imageObserver.observe(img));
        });

        feedState.offset += items.length;
        feedState.hasMore = !!data.has_more && items.length > 0;
    }catch(e){
        console.error(e);
    }finally{
        feedState.loading = false;
    }
}

// Переключение слайда
function setSlide(card, index){
    const track = card.querySelector(".product-slider__track");
    if (!track) return;
    const slides = card.querySelectorAll(".product-slide");
    const dots = card.querySelectorAll(".product-slider__dots .dot");
    const max = slides.length - 1;
    const i = Math.max(0, Math.min(index, max));
    track.style.transform = `translateX(${-i * 100}%)`;
    card.dataset.slideIndex = String(i);
    dots.forEach((d,k) => d.classList.toggle("active", k===i));
}

// СВАЙП С РАЗЛИЧЕНИЕМ КЛИКА И СВАЙПА
let swipeState = null;

function startSwipe(card, startX, startY){
    const track = card.querySelector(".product-slider__track");
    if (!track) return;
    
    swipeState = { 
        card, 
        startX, 
        startY,
        dx: 0, 
        dy: 0,
        width: card.clientWidth, 
        startIndex: Number(card.dataset.slideIndex || "0"), 
        track,
        moved: false,
        startTime: Date.now()
    };
    track.style.transition = "none";
}

function moveSwipe(x, y){
    if (!swipeState) return;
    
    swipeState.dx = x - swipeState.startX;
    swipeState.dy = y - swipeState.startY;
    
    // Отмечаем движение если сдвиг больше 10px
    if (Math.abs(swipeState.dx) > 10 || Math.abs(swipeState.dy) > 10) {
        swipeState.moved = true;
    }
    
    // Только горизонтальный свайп для слайдера
    if (Math.abs(swipeState.dx) > Math.abs(swipeState.dy)) {
        const percent = (swipeState.dx / swipeState.width) * 100;
        const base = -swipeState.startIndex * 100;
        swipeState.track.style.transform = `translateX(${base + percent}%)`;
    }
}

function endSwipe(){
    if (!swipeState) return;
    
    const { card, dx, dy, width, startIndex, track, moved, startTime } = swipeState;
    track.style.transition = "";
    
    let next = startIndex;
    const threshold = width * 0.15;
    const timeElapsed = Date.now() - startTime;
    
    // Свайп только если было горизонтальное движение больше порога
    if (moved && Math.abs(dx) > threshold && Math.abs(dx) > Math.abs(dy)) {
        if (dx > threshold) next = startIndex - 1;
        else if (dx < -threshold) next = startIndex + 1;
    }
    
    setSlide(card, next);
    
    // Возвращаем информацию о том, был ли это свайп
    const wasSwipe = moved && (Math.abs(dx) > 15 || Math.abs(dy) > 15 || timeElapsed > 200);
    
    const result = { wasSwipe, moved };
    swipeState = null;
    
    return result;
}

// Touch события
let lastTouchResult = null;

productsArea.addEventListener("touchstart", (e) => {
    const slider = e.target.closest(".product-slider");
    if (!slider) {
        // Если тач не на слайдере, сбрасываем состояние
        swipeState = null;
        lastTouchResult = null;
        return;
    }
    
    const touch = e.touches[0];
    startSwipe(slider.closest(".product-card"), touch.clientX, touch.clientY);
}, { passive: true });

productsArea.addEventListener("touchmove", (e) => {
    if (!swipeState) return;
    
    const touch = e.touches[0];
    moveSwipe(touch.clientX, touch.clientY);
    
    // Предотвращаем скролл только если это горизонтальный свайп
    if (swipeState && Math.abs(swipeState.dx) > Math.abs(swipeState.dy) && Math.abs(swipeState.dx) > 10) {
        e.preventDefault();
    }
}, { passive: false });

productsArea.addEventListener("touchend", (e) => {
    if (swipeState) {
        lastTouchResult = endSwipe();
        
        // Если был свайп, предотвращаем клик
        if (lastTouchResult && lastTouchResult.wasSwipe) {
            e.preventDefault();
            e.stopPropagation();
        }
    }
}, { passive: false });

// Мышь для десктопа
let mouseSwipeResult = null;

productsArea.addEventListener("mousedown", (e) => {
    const slider = e.target.closest(".product-slider");
    if (!slider) return;
    
    e.preventDefault();
    startSwipe(slider.closest(".product-card"), e.clientX, e.clientY);
});

productsArea.addEventListener("mousemove", (e) => { 
    if (swipeState) {
        e.preventDefault();
        moveSwipe(e.clientX, e.clientY);
    }
});

productsArea.addEventListener("mouseup", (e) => {
    if (swipeState) {
        mouseSwipeResult = endSwipe();
        
        // Если был свайп мышью, предотвращаем клик
        if (mouseSwipeResult && mouseSwipeResult.wasSwipe) {
            e.preventDefault();
            e.stopPropagation();
            
            // Очищаем результат через короткое время
            setTimeout(() => {
                mouseSwipeResult = null;
            }, 100);
        }
    }
});

productsArea.addEventListener("mouseleave", () => {
    if (swipeState) endSwipe();
});

// Дополнительная проверка для mouse кликов
productsArea.addEventListener("click", (e) => {
    // Если был недавний mouse свайп, блокируем клик
    if (mouseSwipeResult && mouseSwipeResult.wasSwipe) {
        console.log('[DEBUG] Mouse click prevented - was swipe');
        e.preventDefault();
        e.stopPropagation();
        mouseSwipeResult = null;
        return;
    }
}, true); // capture phase

// Точки (делегирование)
productsArea.addEventListener("click", (e) => {
    const dot = e.target.closest(".product-slider__dots .dot");
    if (dot) {
        e.stopPropagation();
        const card = dot.closest(".product-card");
        if (!card) return;
        const idx = Number(dot.dataset.index || "0");
        setSlide(card, idx);
        return;
    }
});

// Клики (с проверкой на предыдущий свайп)
productsArea.addEventListener("click", (e) => {
    // Обработка кликов по карточкам товаров
    const card = e.target.closest(".product-card");
    if (card) {
        // Проверяем, был ли недавний свайп
        if (lastTouchResult && lastTouchResult.wasSwipe) {
            console.log('[DEBUG] Click prevented - was swipe');
            e.preventDefault();
            e.stopPropagation();
            lastTouchResult = null; // Сбрасываем
            return;
        }
        
        // Проверяем, что клик не на интерактивном элементе
        const interactive = e.target.closest("button, .product-slider__dots");
        if (interactive) return;
        
        // Это обычный клик - получаем информацию о магазине и переходим
        const productId = card.dataset.productId;
        console.log('[DEBUG] Product clicked:', productId);
        
        // Получаем информацию о текущем магазине
        const shopData = document.getElementById('shop-data');
        if (shopData) {
            const insalesId = shopData.dataset.insalesId;
            const shop = shopData.dataset.shop;
            
            if (insalesId && shop) {
                // ПЕРЕХОД НА СТРАНИЦУ ТОВАРА С ПАРАМЕТРАМИ МАГАЗИНА
                window.location.href = `/product/${productId}?insales_id=${insalesId}&shop=${shop}`;
                return;
            }
        }
        
        // Fallback - переход без параметров (будет использован Referer)
        window.location.href = `/product/${productId}`;
    }
});

// Очищаем результат свайпа через некоторое время
setInterval(() => {
    if (lastTouchResult) {
        lastTouchResult = null;
    }
}, 500);

// Публичные инициализаторы
window.initAllProductsFeed = async function(){
    resetFeed();
    feedState.mode = "all";
    feedState.collectionId = null;
    ensureObservers();
    await loadNextPage();
};

window.initCollectionFeed = async function(collectionId){
    resetFeed();
    feedState.mode = "collection";
    feedState.collectionId = Number(collectionId);
    ensureObservers();
    await loadNextPage();
};
