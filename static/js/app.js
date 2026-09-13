/**
 * Comportamentos globais do VoxterFlix: fecha alertas automaticamente e
 * aplica o estado "active" no item de menu correspondente à página atual.
 */
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".voxter-alert").forEach((alerta) => {
    setTimeout(() => {
      const instancia = bootstrap.Alert.getOrCreateInstance(alerta);
      instancia.close();
    }, 6000);
  });

  const caminhoAtual = window.location.pathname;
  document.querySelectorAll(".voxter-navbar .nav-link").forEach((link) => {
    if (link.getAttribute("href") === caminhoAtual) {
      link.classList.add("active");
      link.setAttribute("aria-current", "page");
    }
  });
});
