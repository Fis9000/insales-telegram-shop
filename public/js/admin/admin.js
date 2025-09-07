const buttons = document.querySelectorAll('.menu__btn');
const panels = {
  menu1: document.getElementById('panel-menu1'),
  menu2: document.getElementById('panel-menu2'),
  menu3: document.getElementById('panel-menu3')
};

function showContent(menuKey, btn) {
  // показать нужную секцию
  Object.values(panels).forEach(p => p.setAttribute('hidden', ''));
  panels[menuKey]?.removeAttribute('hidden');

  // активная кнопка
  buttons.forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
}

