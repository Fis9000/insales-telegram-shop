document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('productSearch');
  const area = document.getElementById('productsArea');
  if (!input || !area) {
    console.warn('productSearch или productsArea не найдены');
    return;
  }

  const getCards = () => Array.from(area.querySelectorAll('.product-card'));
  const getTitle = (card) => (card.querySelector('.product-title')?.textContent || '');

  // Нормализация: убрать диакритики и понизить регистр
  const norm = (s) =>
    s
      .normalize('NFD')                 // разложить символы на базу + диакритики
      .replace(/[\u0300-\u036f]/g, '')  // удалить комбинируемые диакритики
      .toLowerCase()
      .trim();

  // Фильтрация карточек
  const applyFilter = () => {
    const q = norm(input.value);
    getCards().forEach(card => {
      const title = norm(getTitle(card));
      const match = q === '' || title.includes(q);
      card.style.display = match ? '' : 'none';
    });
  };

  // Реакция при вводе
  input.addEventListener('input', applyFilter); // обновляет сразу при наборе

  // Enter: блокируем submit, сворачиваем клаву, но не забываем применить фильтр
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.keyCode === 13) {
      e.preventDefault();     // блокируем submit формы по Enter
      applyFilter();          // применяем поиск прямо сейчас
      input.blur();           // сворачиваем клавиатуру на мобильных
      if (document.activeElement && typeof document.activeElement.blur === 'function') {
        document.activeElement.blur(); // подстраховка
      }
    }
  });
});
