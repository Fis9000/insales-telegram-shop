(function () {
  // Инициализация точек для галереи товара
  function initProductDots() {
    const viewport = document.querySelector('.product-gallery-viewport');
    if (!viewport) return;

    const section = viewport.closest('.product-gallery');
    if (!section) return;

    const slides = Array.from(viewport.querySelectorAll('img.product-gallery-img'));
    // Если меньше 2 изображений — убираем точки и выходим
    if (slides.length <= 1) {
      removeDots(section);
      return;
    }

    // Чистим предыдущие точки именно для этой секции
    removeDots(section);

    // Создаем и вставляем контейнер точек внутрь секции (под галереей)
    const dotsWrap = createDots(slides.length);
    section.appendChild(dotsWrap);
    // Если нужно поверх фотографий:
    // dotsWrap.classList.add('overlay');

    // Геометрия слайдов
    let slideW = 0;
    let gap = 0;

    function measure() {
      const cs = getComputedStyle(viewport);
      gap = parseFloat(cs.columnGap || cs.gap || '6') || 6;
      const first = slides[0];
      const rect = first ? first.getBoundingClientRect() : null;
      slideW = rect ? Math.round(rect.width + gap) : viewport.clientWidth;
      if (!slideW) slideW = viewport.clientWidth;
    }

    // Помощники
    function setActive(idx) {
      setActiveDot(dotsWrap, clamp(idx, 0, slides.length - 1));
    }
    function clamp(x, a, b) { return Math.max(a, Math.min(b, x)); }

    // Индекс по ближайшему слайду к левой границе viewport (точнее при разной ширине)
    function currentIndexByRects() {
      const vpLeft = viewport.getBoundingClientRect().left;
      let best = 0, bestDist = Infinity;
      for (let i = 0; i < slides.length; i++) {
        const r = slides[i].getBoundingClientRect();
        const dist = Math.abs(r.left - vpLeft);
        if (dist < bestDist) { bestDist = dist; best = i; }
      }
      return best;
    }

    // Инициализация
    requestAnimationFrame(() => { measure(); setActive(0); });

    // Быстрый отклик + фиксация по окончании инерции
    let rafId = null;
    function trackUntilStop() {
      let last = viewport.scrollLeft, stableFrames = 0;
      cancelAnimationFrame(rafId);
      (function loop() {
        rafId = requestAnimationFrame(() => {
          const now = viewport.scrollLeft;
          if (Math.abs(now - last) < 0.5) stableFrames++; else stableFrames = 0;
          last = now;
          if (stableFrames >= 2) {
            // финальная фиксация — максимально точная
            const idx = currentIndexByRects();
            setActive(idx);
          } else {
            loop();
          }
        });
      })();
    }

    // Слушатели
    window.addEventListener('resize', () => { measure(); }, { passive: true });

    viewport.addEventListener('scroll', () => {
      if (!slideW) measure();

      // Мгновенная предварительная подсветка — отзывчиво
      const roughIdx = Math.round(viewport.scrollLeft / slideW);
      setActive(roughIdx);

      // Точная фиксация, когда инерция остановилась
      trackUntilStop();
    }, { passive: true });

    // Клик по точке — перейти к нужному слайду
    dotsWrap.addEventListener('click', (e) => {
      const dot = e.target.closest('.gallery-dot');
      if (!dot) return;
      const index = Array.from(dotsWrap.children).indexOf(dot);
      if (!slideW) measure();
      viewport.scrollTo({ left: index * slideW, behavior: 'smooth' });
    });
  }

  // Вспомогательные функции (точки)
  function removeDots(scopeEl) {
    if (!scopeEl) return;
    scopeEl.querySelectorAll('.gallery-dots').forEach(el => el.remove());
    const next = scopeEl.nextElementSibling;
    if (next && next.classList && next.classList.contains('gallery-dots')) next.remove();
  }

  function createDots(n) {
    const wrap = document.createElement('div');
    wrap.className = 'gallery-dots';
    for (let i = 0; i < n; i++) {
      const d = document.createElement('span');
      d.className = 'gallery-dot' + (i === 0 ? ' active' : '');
      wrap.appendChild(d);
    }
    return wrap;
  }

  function setActiveDot(wrap, idx) {
    wrap.querySelectorAll('.gallery-dot').forEach((el, i) => {
      el.classList.toggle('active', i === idx);
    });
  }

  // Безопасная инициализация для WebApp/SPA
  function boot() {
    try { initProductDots(); } catch (_) {}

    const root = document.querySelector('.scroll-area') || document.body;
    if (root && 'MutationObserver' in window) {
      const mo = new MutationObserver(() => {
        const viewport = document.querySelector('.product-gallery-viewport');
        const section = viewport && viewport.closest('.product-gallery');
        if (!viewport || !section) return;
        if (!section.querySelector('.gallery-dots')) {
          try { initProductDots(); } catch (_) {}
        }
      });
      mo.observe(root, { childList: true, subtree: true });
    }

    // Telegram viewportChanged — на случай перестроения верстки
    if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.onEvent) {
      try {
        window.Telegram.WebApp.onEvent('viewportChanged', () => {
          const viewport = document.querySelector('.product-gallery-viewport');
          const section = viewport && viewport.closest('.product-gallery');
          if (!viewport || !section) return;
          if (!section.querySelector('.gallery-dots')) {
            try { initProductDots(); } catch (_) {}
          }
        });
      } catch (_) {}
    }
  }

  document.addEventListener('DOMContentLoaded', boot);
  window.addEventListener('pageshow', boot);
})();
