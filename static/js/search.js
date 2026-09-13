/**
 * Alterna a visibilidade do painel de filtros avançados em telas pequenas
 * e mantém o botão "Limpar filtros" funcional (remove todos os query params).
 */
document.addEventListener("DOMContentLoaded", () => {
  const botaoFiltros = document.querySelector("[data-toggle-filtros]");
  const painelFiltros = document.querySelector("[data-painel-filtros]");

  botaoFiltros?.addEventListener("click", () => {
    painelFiltros.classList.toggle("d-none");
    const expandido = !painelFiltros.classList.contains("d-none");
    botaoFiltros.setAttribute("aria-expanded", String(expandido));
  });

  document.querySelector("[data-limpar-filtros]")?.addEventListener("click", (evento) => {
    evento.preventDefault();
    const url = new URL(window.location.href);
    const termo = url.searchParams.get("q");
    window.location.href = termo ? `${url.pathname}?q=${encodeURIComponent(termo)}` : url.pathname;
  });
});
