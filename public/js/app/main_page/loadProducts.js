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
  images.forEach((url) => {
    const slide = document.createElement("div");
    slide.className = "product-slide";
    const img = document.createElement("img");
    img.alt = p.title || "";
    img.loading = "lazy";
    img.dataset.src = url; // lazy
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
    price.textContent = `${formatted} ₽`; // будет "9 856 ₽"
    // Вариант с Intl currency:
    // price.textContent = new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 }).format(p.base_price);
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

    // наблюдать все новые lazy-изображения
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

// Точки (делегирование)
productsArea.addEventListener("click", (e) => {
  const dot = e.target.closest(".product-slider__dots .dot");
  if (!dot) return;
  e.stopPropagation(); // не пускаем до перехода
  const card = dot.closest(".product-card");
  if (!card) return;
  const idx = Number(dot.dataset.index || "0");
  setSlide(card, idx);
});

// Свайп
let swipeState = null;
function startSwipe(card, startX){
  const track = card.querySelector(".product-slider__track");
  if (!track) return;
  swipeState = { card, startX, dx:0, width:card.clientWidth, startIndex:Number(card.dataset.slideIndex||"0"), track };
  track.style.transition = "none";
}
function moveSwipe(x){
  if (!swipeState) return;
  swipeState.dx = x - swipeState.startX;
  const percent = (swipeState.dx / swipeState.width) * 100;
  const base = -swipeState.startIndex * 100;
  swipeState.track.style.transform = `translateX(${base + percent}%)`;
}
function endSwipe(){
  if (!swipeState) return;
  const { card, dx, width, startIndex, track } = swipeState;
  track.style.transition = ""; // вернуть анимацию
  const threshold = width * 0.2;
  let next = startIndex;
  if (dx > threshold) next = startIndex - 1;
  else if (dx < -threshold) next = startIndex + 1;
  setSlide(card, next);
  swipeState = null;
}

productsArea.addEventListener("touchstart", (e) => {
  const slider = e.target.closest(".product-slider");
  if (!slider) return;
  startSwipe(slider.closest(".product-card"), e.touches[0].clientX);
}, { passive:true });

productsArea.addEventListener("touchmove", (e) => {
  if (!swipeState) return;
  moveSwipe(e.touches[0].clientX);
}, { passive:true });

productsArea.addEventListener("touchend", endSwipe);
productsArea.addEventListener("touchcancel", endSwipe);

productsArea.addEventListener("mousedown", (e) => {
  const slider = e.target.closest(".product-slider");
  if (!slider) return;
  e.preventDefault();
  startSwipe(slider.closest(".product-card"), e.clientX);
});
productsArea.addEventListener("mousemove", (e) => { if (swipeState) moveSwipe(e.clientX); });
productsArea.addEventListener("mouseup", endSwipe);
productsArea.addEventListener("mouseleave", () => { if (swipeState) endSwipe(); });

// Переход по карточке
productsArea.addEventListener("click", (e) => {
  const interactive = e.target.closest("a,button,input,select,textarea,label,.product-slider__dots .dot");
  if (interactive) return;
  const card = e.target.closest(".product-card");
  if (!card) return;
  const id = card.dataset.productId;
  if (!id) return;
  window.location.href = `/product/${id}`;
});

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
