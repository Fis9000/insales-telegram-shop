// ===== Выпадающее меню "Каталог" (портал в body) =====
(function initCatalogDropdownOnce() {
  if (window.__catalogDropdownInitDone) return;
  window.__catalogDropdownInitDone = true;

  // ===== Подсветка соответствующей кнопки коллекции =====
  function setActiveCollectionButton(idOrNull) {
    const area = document.getElementById('collectionsArea');
    if (!area) return;
    const buttons = area.querySelectorAll('.collections-btn');
    buttons.forEach(b => b.classList.remove('active'));
    if (!idOrNull || idOrNull === '') {
      const btnAll = Array.from(buttons).find(
        b => b.textContent.trim() === 'Смотреть все' || b.dataset.id === ''
      );
      if (btnAll) btnAll.classList.add('active');
      return;
    }
    const btn = Array.from(buttons).find(b => String(b.dataset.id) === String(idOrNull));
    if (btn) btn.classList.add('active');
  }

  function ready(fn) {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fn);
    else fn();
  }

  ready(async function initDropdown() {
    try {
      const area = document.getElementById('collectionsArea');
      if (!area) return;

      // Flex для всей полосы кнопок
      area.style.display = 'flex';
      area.style.flexWrap = 'nowrap';
      area.style.alignItems = 'center';
      area.style.gap = '10px';

      // Каталог-кнопка (в начало)
      let wrapper = area.querySelector('.catalog-wrapper');
      if (!wrapper) {
        wrapper = document.createElement('div');
        wrapper.className = 'catalog-wrapper';
        wrapper.style.position = 'relative';
        wrapper.style.flex = '0 0 auto';
        area.insertBefore(wrapper, area.firstChild);
      }
      let btn = wrapper.querySelector('.catalog-button');
      if (!btn) {
        btn = document.createElement('button');
        btn.className = 'catalog-button';
        btn.innerHTML = 'Каталог <i class="ri-arrow-right-s-line"></i>';
        btn.style.position = 'relative';
        btn.style.zIndex = '1006';
        wrapper.appendChild(btn);
      }

      // Меню ­– отдельный портал в body
      let menu = document.querySelector('body > .catalog-menu.portal-mounted');
      if (!menu) {
        menu = document.createElement('div');
        menu.className = 'catalog-menu hidden portal-mounted';
        menu.style.position = 'fixed';
        menu.style.zIndex = '10060';
        menu.style.minWidth = '180px';
        menu.style.maxHeight = '60vh';
        menu.style.overflowY = 'auto';
        menu.style.display = 'flex';
        menu.style.flexDirection = 'column';
        document.body.appendChild(menu);
      }

      // Гарантировать реальное скрытие
      (function ensureHiddenCSS() {
        if (!document.getElementById('catalog-menu-hidden-style')) {
          const st = document.createElement('style');
          st.id = 'catalog-menu-hidden-style';
          st.textContent = `.catalog-menu.hidden { display: none !important; }`;
          document.head.appendChild(st);
        }
      })(); // [15][14]

      // Подгружаем коллекции (отдельно для меню, не для полосы)
      let collections = [];
      try {
        const res = await fetch('/show_collections', { credentials: 'same-origin' });
        if (res.ok) collections = await res.json();
      } catch (e) { /* ничего страшного */ }

      function buildMenuItems() {
        menu.innerHTML = '';
        // Только один раз "Смотреть все"
        const allItem = document.createElement('div');
        allItem.className = 'catalog-menu-item';
        allItem.textContent = 'Смотреть все';
        allItem.dataset.id = '';
        menu.appendChild(allItem);

        // Без дубля "Смотреть все"
        collections
          .filter(col => String(col.title).trim() !== 'Смотреть все' && String(col.id ?? '').trim() !== '')
          .forEach(col => {
            const item = document.createElement('div');
            item.className = 'catalog-menu-item';
            item.textContent = col.title;
            item.dataset.id = col.id;
            menu.appendChild(item);
          });
      }
      buildMenuItems();

      function placeMenuNearButton() {
        const r = btn.getBoundingClientRect();
        const menuWidth = Math.max(180, menu.getBoundingClientRect().width || 180);
        const padding = 8;
        let left = r.left;
        left = Math.max(padding, Math.min(window.innerWidth - padding - menuWidth, left));
        const top = r.bottom + 6;
        menu.style.left = `${left}px`;
        menu.style.top = `${top}px`;
      }

      function openMenu() {
        placeMenuNearButton();
        menu.classList.remove('hidden');
        btn.classList.add('open');
      }
      function closeMenu() {
        menu.classList.add('hidden');
        btn.classList.remove('open');
      }

      // Кнопка — обязательно stopPropagation, чтобы не поймать capture-вне сразу
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (menu.classList.contains('hidden')) openMenu();
        else closeMenu();
      }); // [14][13]

      // Выбор пункта — закрывать
      menu.addEventListener('click', async (e) => {
        const item = e.target.closest('.catalog-menu-item');
        if (!item) return;
        const id = item.dataset.id || null;

        try {
          if (typeof initAllProductsFeed === 'function' && typeof initCollectionFeed === 'function') {
            if (!id) {
              await initAllProductsFeed();
              setActiveCollectionButton('');
            } else {
              await initCollectionFeed(id);
              setActiveCollectionButton(id);
            }
          }
        } catch {}
        closeMenu();
      }); // [14]

      // Клик/тач/указатель вне — закрыть (capture для WebView)
      function isOutside(target) {
        return !wrapper.contains(target) && !menu.contains(target);
      }
      const outsideClose = (e) => {
        const t = e.target;
        if (isOutside(t)) closeMenu();
      };

      // Захватываем максимально ранние события, т.к. в WebView они могут не всплыть корректно
      document.addEventListener('pointerdown', outsideClose, true);
      document.addEventListener('mousedown', outsideClose, true);
      document.addEventListener('click', outsideClose, true);
      window.addEventListener('touchstart', outsideClose, { passive: true, capture: true });
      window.addEventListener('touchend', outsideClose, { passive: true, capture: true }); // [13][1]

      // Переукладка при изменениях вьюпорта
      window.addEventListener('resize', () => {
        if (!menu.classList.contains('hidden')) placeMenuNearButton();
      });
      window.addEventListener('scroll', () => {
        if (!menu.classList.contains('hidden')) placeMenuNearButton();
      }, true);

      // Чтобы не перекрывал overlay (в Telegram WebView бывают собственные слои)
      const overlay = document.getElementById('overlay');
      if (overlay) {
        const z = window.getComputedStyle(overlay).zIndex;
        if (!z || Number(z) >= 10060) overlay.style.zIndex = '10050';
      }

    } catch (err) {
      console.error('[dropdown] init failed:', err);
    }
  });
})();
