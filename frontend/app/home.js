(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};
  const app = document.getElementById("app");
  const esc = root.escapeHtml;
  const t = root.t;
  const n = root.n;

  const TONO = {
    ready: "ok", ready_to_publish: "ok",
    failed_terminal: "errore",
    sources_required: "attesa", preparation_required: "attesa", processing: "attesa",
    failed_resumable: "attesa", awaiting_review: "attesa",
  };

  const applicaTema = (modo) => {
    document.documentElement.dataset.theme = modo;
    localStorage.setItem("kg.theme", modo);
    const bottone = app.querySelector("[data-tema]");
    if (bottone) {
      bottone.textContent = modo === "dark" ? "☾" : "☀";
      bottone.title = t(modo === "dark" ? "ui.temaChiaro" : "ui.temaScuro");
      bottone.setAttribute("aria-label", bottone.title);
    }
  };

  const disegna = (macchine, errore = "", caricando = false) => {
    const carte = macchine.map((macchina) => {
      const tono = TONO[macchina.status] || "";
      const aggiornato = new Date(macchina.updated_at).toLocaleString(
        root.lingua() === "en" ? "en-GB" : "it-IT",
        { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }
      );
      return `
        <a class="macchina-card entra" href="/console.html?foundation=1&workspace_id=${encodeURIComponent(macchina.workspace_id)}">
          <div>
            <strong>${esc(macchina.asset_name)}</strong>
            <small>${esc(`${macchina.brand} · ${macchina.model} · ${n(macchina.document_count, "home.doc")}`)}</small>
          </div>
          <span class="macchina-lato">
            <span class="chip">${esc(aggiornato)}</span>
            <span class="badge ${tono}"><span class="punto" aria-hidden="true"></span>${esc(t(`wstato.${macchina.status}`))}</span>
          </span>
        </a>`;
    }).join("");

    app.innerHTML = `
      <main class="main" style="width:100%">
        <header class="topbar">
          <h1>${esc(t("home.titolo"))}</h1>
          <span class="spacer"></span>
          <button class="toggle-btn lingua" type="button" data-lingua>${esc(root.siglaLingua())}</button>
          <button class="toggle-btn tema" type="button" data-tema>☀</button>
        </header>
        <div class="lavoro"><div class="elenco-macchine">
          <div class="elenco-capo">
            <div><h2 style="margin:0;font-size:22px;font-weight:640;letter-spacing:-.025em">${esc(t("home.titolo"))}</h2>
              <p>${esc(t("home.sotto"))}</p></div>
            <a class="btn primario" href="/console.html?foundation=1&new=1">${esc(t("home.nuova"))}</a>
          </div>
          ${errore ? `<div class="nota errore" role="alert"><span class="segno" aria-hidden="true">!</span>
            <strong>${esc(t("home.errore"))}</strong><span>${esc(errore)}</span></div>` : ""}
          <div class="lista">
            ${caricando ? `<p class="voce-meta">${esc(t("ui.caricamento"))}</p>` : carte || `
              <div class="vuoto"><strong>${esc(t("home.vuoto"))}</strong><p>${esc(t("home.vuotoTesto"))}</p>
                <a class="btn primario" href="/console.html?foundation=1&new=1">${esc(t("home.nuova"))}</a></div>`}
          </div>
        </div></div>
      </main>`;

    app.querySelector("[data-lingua]").onclick = () => {
      root.cambiaLingua();
      disegna(macchine, errore, caricando);
    };
    app.querySelector("[data-lingua]").title = t("ui.lingua");
    app.querySelector("[data-tema]").onclick = () =>
      applicaTema(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
    applicaTema(document.documentElement.dataset.theme
      || localStorage.getItem("kg.theme")
      || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"));
  };

  disegna([], "", true);
  root.api("/api/workspaces")
    .then((macchine) => disegna(macchine))
    .catch((errore) => disegna([], errore.message));
})();
