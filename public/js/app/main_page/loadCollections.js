// ===== Загрузка коллекций и установка обработчиков (без удаления кнопки Каталог) =====
async function loadCollections() {
  try {
    const response = await fetch('/show_collections');
    if (!response.ok) throw new Error('HTTP ' + response.status);
    const collections = await response.json();

    const area = document.getElementById('collectionsArea');
    if (!area) {
      console.warn('Не найден контейнер #collectionsArea');
      return;
    }

    // Не трогаем кнопку Каталог/меню (они вне area или в её начале).
    // Удаляем только кнопки коллекций.
    area.querySelectorAll('.collections-btn').forEach(el => el.remove());

    // Кнопки коллекций
    collections.forEach((col) => {
      const btn = document.createElement('button');
      btn.className = 'collections-btn';
      btn.textContent = col.title;
      btn.dataset.id = col.id;
      area.appendChild(btn);
    });

    const collectionButtons = area.querySelectorAll('.collections-btn');
    collectionButtons.forEach((button) => {
      button.addEventListener('click', async () => {
        collectionButtons.forEach((b) => b.classList.remove('active'));
        button.classList.add('active');
        if (button.dataset.id === 'all') await initAllProductsFeed();
        else await initCollectionFeed(button.dataset.id);
              });
            });

    // Активируем первую
    const firstBtn = area.querySelector('.collections-btn');
    if (firstBtn) {
      firstBtn.classList.add('active');
      if (firstBtn.dataset.id === 'all') await initAllProductsFeed();
      else await initCollectionFeed(firstBtn.dataset.id);
    } else {
      await initAllProductsFeed();
    }

  } catch (error) {
    console.error('Ошибка при загрузке коллекций:', error);
  }
}

// ===== Старт =====
document.addEventListener('DOMContentLoaded', () => {
  loadCollections();
});
