/**
 * Setas de navegação dos carrosséis da Home. Em touch (celular/tablet), o
 * scroll nativo por arraste já funciona sem JS — as setas são um reforço
 * para uso com mouse/teclado.
 */
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-carousel]").forEach((wrapper) => {
    const trilho = wrapper.querySelector(".voxter-carousel");
    const btnEsquerda = wrapper.querySelector("[data-carousel-prev]");
    const btnDireita = wrapper.querySelector("[data-carousel-next]");
    if (!trilho) return;

    const distancia = () => Math.max(trilho.clientWidth * 0.8, 200);

    btnEsquerda?.addEventListener("click", () => {
      trilho.scrollBy({ left: -distancia(), behavior: "smooth" });
    });
    btnDireita?.addEventListener("click", () => {
      trilho.scrollBy({ left: distancia(), behavior: "smooth" });
    });
  });
});
