/**
 * Controle do player de streaming.
 *
 * Limitação conhecida: o player embutido pela SuperFlixAPI roda em um
 * <iframe> de outro domínio, e a API não documenta nenhum mecanismo
 * (postMessage, etc.) para o VoxterFlix ler o tempo exato de reprodução
 * de dentro desse iframe. Por isso o progresso é uma ESTIMATIVA baseada
 * no tempo decorrido desde que o player carregou, comparado à duração do
 * título (quando a OMDb informa). Não é 100% preciso (não detecta pausa
 * ou avanço manual dentro do player), mas é honesto sobre o que é possível
 * medir sem acesso ao player interno — e é reportado como aproximação.
 */
document.addEventListener("DOMContentLoaded", () => {
  const container = document.querySelector("[data-player-container]");
  if (!container) return;

  const wrapper = container.querySelector(".voxter-player-wrapper");
  const iframe = container.querySelector("iframe");
  const loading = container.querySelector("[data-player-loading]");

  if (iframe) {
    iframe.addEventListener("load", () => loading?.classList.add("d-none"), { once: true });
    // Caso o "load" nunca dispare (bloqueio de terceiros, rede lenta),
    // não deixamos o overlay de carregamento preso para sempre.
    setTimeout(() => loading?.classList.add("d-none"), 8000);
  }

  document.querySelector("[data-fullscreen-btn]")?.addEventListener("click", () => {
    if (wrapper.requestFullscreen) {
      wrapper.requestFullscreen();
    }
  });

  iniciarRegistroDeProgresso(container);
});

function getCookie(nome) {
  const valor = `; ${document.cookie}`;
  const partes = valor.split(`; ${nome}=`);
  return partes.length === 2 ? partes.pop().split(";").shift() : "";
}

function iniciarRegistroDeProgresso(container) {
  const dados = container.dataset;
  if (!dados.imdbId) return;

  const inicio = Date.now();
  const duracao = parseInt(dados.duration || "0", 10);

  const enviarProgresso = (usarKeepalive = false) => {
    const decorrido = Math.floor((Date.now() - inicio) / 1000);
    const payload = JSON.stringify({
      imdb_id: dados.imdbId,
      season: dados.season || 0,
      episode: dados.episode || 0,
      progress_seconds: decorrido,
      duration_seconds: duracao,
      title: dados.title || "",
      poster: dados.poster || "",
      type: dados.type || "",
    });

    fetch(dados.progressUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: payload,
      keepalive: usarKeepalive,
    }).catch(() => {
      /* Falha ao registrar progresso não deve interromper a reprodução. */
    });
  };

  const intervalo = setInterval(() => {
    if (!document.hidden) enviarProgresso();
  }, 20000);

  window.addEventListener("beforeunload", () => {
    clearInterval(intervalo);
    enviarProgresso(true);
  });
}
