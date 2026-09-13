/**
 * Pré-visualização da cor do avatar ao escolher uma opção no formulário
 * de perfil (feedback visual imediato, sem precisar salvar para ver).
 */
document.addEventListener("DOMContentLoaded", () => {
  const seletorAvatar = document.querySelector("[data-avatar-select]");
  const preview = document.querySelector("[data-avatar-preview]");
  if (!seletorAvatar || !preview) return;

  const atualizarPreview = () => {
    preview.className = "voxter-avatar voxter-avatar-lg voxter-avatar-" + seletorAvatar.value;
  };

  seletorAvatar.addEventListener("change", atualizarPreview);
  atualizarPreview();
});
