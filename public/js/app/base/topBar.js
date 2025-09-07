class TopBar extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `
      <header class="topbar">
        <div class="text-logo">4FORMS</div>
      </header>
    `;
  }
}
customElements.define('topBar', TopBar);