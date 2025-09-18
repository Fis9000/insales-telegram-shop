document.addEventListener("DOMContentLoaded", async () => {
  const params = new URLSearchParams(window.location.search);
  const insales_id = params.get("insales_id");
  const shop = params.get("shop");

  // Загружаем настройки из бэка
  try {
    let res = await fetch(`/admin/settings/load?insales_id=${insales_id}&shop=${shop}`);
    let data = await res.json();

    if (data.status === "ok") {
      document.querySelector("#identifierInput").value = data.identifier || "";
      document.querySelector("#passwordInput").value = data.password || "";
      document.querySelector("#tokenInput").value = data.token || "";
    }
  } catch (err) {
    console.error("Ошибка при загрузке настроек:", err);
  }

  // Сохранение
  document.getElementById("saveSettingsBtn").addEventListener("click", async () => {
    const payload = {
      insales_id,
      shop,
      identifier: document.querySelector("#identifierInput").value,
      password: document.querySelector("#passwordInput").value,
      token: document.querySelector("#tokenInput").value,
    };

    try {
      let res = await fetch("/admin/settings/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      let data = await res.json();
      if (data.status === "ok") {
        alert("Настройки сохранены!");
      } else {
        alert("Ошибка сохранения: " + (data.detail || "Неизвестно"));
      }
    } catch (err) {
      console.error(err);
      alert("Ошибка при сохранении");
    }
  });
});
