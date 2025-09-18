const buttons = document.querySelectorAll('.menu__btn');
const panels = {
  menu1: document.getElementById('panel-menu1'),
  menu2: document.getElementById('panel-menu2'),
  menu3: document.getElementById('panel-menu3'),
  menu4: document.getElementById('panel-menu4'),
  menu5: document.getElementById('panel-menu5')
};

function showContent(menuId, button) {
    // Скрываем все панели
    const panels = document.querySelectorAll('.panel');
    panels.forEach(panel => {
        panel.hidden = true;
        panel.classList.remove('is-active');
    });

    // Убираем активный класс со всех кнопок
    const buttons = document.querySelectorAll('.menu__btn');
    buttons.forEach(btn => btn.classList.remove('active'));

    // Показываем выбранную панель и активируем кнопку
    const selectedPanel = document.getElementById(`panel-${menuId}`);
    if (selectedPanel) {
        selectedPanel.hidden = false;
        selectedPanel.classList.add('is-active');
    }
    
    button.classList.add('active');

    // Загружаем коллекции при переходе на вкладку "Категории"
    if (menuId === 'menu3' && window.collectionsManager) {
        window.collectionsManager.loadCollections();
    }
}


