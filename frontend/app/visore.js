(function () {
  "use strict";
  /* Il visore è una finestra a sé: si apre da un documento e non porta con sé
     né la barra laterale né lo stato dell'applicativo. Serve a guardare, non a
     decidere — nessuna azione qui cambia niente di quello che è stato caricato.

     Quello che mostra non lo interpreta: le righe arrivano dagli stessi
     adattatori che le trasformeranno in dichiarazioni, così la cella che
     l'operatore controlla è la cella da cui nascerà una dichiarazione. */
  const root = window.KGFoundation = window.KGFoundation || {};
  const app = document.getElementById("app");
  const esc = root.escapeHtml;
  const t = root.t;

  const parametri = new URL(window.location.href).searchParams;
  const sourceId = parametri.get("source_id") || "";
  const workspaceId = parametri.get("workspace_id") || "";

  const stato = { fonte: null, tabelle: null, foglio: 0, errore: "" };

  const applicaTema = () => {
    document.documentElement.dataset.theme = localStorage.getItem("kg.theme")
      || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  };

  const sigla = (fonte) => {
    const punto = String(fonte.file_name || "").lastIndexOf(".");
    const estensione = punto > 0 ? fonte.file_name.slice(punto + 1) : "";
    return (estensione || fonte.source_kind || "").slice(0, 4).toUpperCase();
  };

  const misura = (byte) => {
    if (!byte && byte !== 0) return "";
    if (byte < 1024) return `${byte} B`;
    if (byte < 1024 * 1024) return `${Math.round(byte / 1024)} kB`;
    return `${(byte / (1024 * 1024)).toFixed(1)} MB`;
  };

  const indirizzoContenuto = (inline) =>
    `/api/sources/${encodeURIComponent(sourceId)}/content${inline ? "?disposition=inline" : ""}`;

  const tabella = (foglio) => `
    <div class="tabella-wrap visore-tabella">
      <table class="tabella">
        <thead><tr>
          <th class="visore-riga-numero">#</th>
          ${foglio.columns.map((nome) => `<th>${esc(nome)}</th>`).join("")}
        </tr></thead>
        <tbody>
          ${foglio.rows.map((riga, indice) => `<tr>
            <td class="visore-riga-numero">${indice + 1}</td>
            ${riga.map((cella) => `<td>${esc(cella)}</td>`).join("")}
          </tr>`).join("")}
        </tbody>
      </table>
    </div>`;

  const corpo = () => {
    if (stato.errore) {
      return `<div class="stato-pagina"><strong>${esc(t("vis.errore"))}</strong>
        <p>${esc(stato.errore)}</p>
        <a class="btn secondario" href="${esc(indirizzoContenuto(false))}" download>${esc(t("vis.scarica"))}</a></div>`;
    }
    if (!stato.fonte) return `<div class="stato-pagina"><strong>${esc(t("ui.caricamento"))}</strong></div>`;
    if (stato.fonte.source_kind === "pdf") {
      /* Il PDF lo mostra il lettore del browser: è già lì, sa cercare nel testo
         e stampare, e non chiede di caricare nessuna libreria. */
      return `<iframe class="visore-pdf" src="${esc(indirizzoContenuto(true))}"
        title="${esc(stato.fonte.file_name || "")}"></iframe>`;
    }
    if (!stato.tabelle) return `<div class="stato-pagina"><strong>${esc(t("ui.caricamento"))}</strong></div>`;
    const fogli = stato.tabelle.tables || [];
    if (!fogli.length) {
      return `<div class="stato-pagina"><strong>${esc(t("vis.vuoto"))}</strong>
        <p>${esc(t("vis.vuotoTesto"))}</p></div>`;
    }
    const foglio = fogli[Math.min(stato.foglio, fogli.length - 1)];
    return `
      ${fogli.length > 1 ? `<div class="barra">
        <div class="segmento" role="tablist">
          ${fogli.map((voce, indice) => `<button type="button" class="tab" role="tab" data-foglio="${indice}"
            aria-selected="${indice === stato.foglio}">${esc(voce.name)}</button>`).join("")}
        </div>
      </div>` : ""}
      <div class="visore-scorri">
        ${tabella(foglio)}
        <p class="visore-conto">
          ${esc(t(foglio.truncated ? "vis.righeTagliate" : "vis.righe",
            { n: foglio.rows.length, tot: foglio.row_count }))}
        </p>
      </div>`;
  };

  const disegna = () => {
    const fonte = stato.fonte;
    app.innerHTML = `
      <main class="main" style="width:100%">
        <header class="topbar">
          <h1 class="visore-titolo">
            ${fonte ? `<span class="nav-sigla ${fonte.source_kind === "pdf" ? "sigla-pdf" : "sigla-dati"}"
              aria-hidden="true">${esc(sigla(fonte))}</span>` : ""}
            <span class="visore-nome">${esc(fonte ? fonte.file_name : t("ui.caricamento"))}</span>
          </h1>
          <span class="spacer"></span>
          ${fonte && fonte.size_bytes ? `<span class="visore-peso">${esc(misura(fonte.size_bytes))}</span>` : ""}
          <div class="comandi">
            <a class="cmd" href="${esc(indirizzoContenuto(false))}" download>${esc(t("vis.scarica"))}</a>
          </div>
        </header>
        <div class="visore-corpo">${corpo()}</div>
      </main>`;

    app.querySelectorAll("[data-foglio]").forEach((bottone) => {
      bottone.onclick = () => {
        stato.foglio = Number(bottone.dataset.foglio);
        disegna();
      };
    });
  };

  applicaTema();
  disegna();

  (async () => {
    try {
      if (!sourceId || !workspaceId) throw new Error(t("vis.senzaDocumento"));
      const fonti = await root.api(`/api/workspaces/${encodeURIComponent(workspaceId)}/sources`);
      stato.fonte = fonti.find((voce) => voce.source_id === sourceId) || null;
      if (!stato.fonte) throw new Error(t("vis.senzaDocumento"));
      document.title = `${stato.fonte.file_name} · Nexus`;
      disegna();
      if (stato.fonte.source_kind !== "pdf") {
        stato.tabelle = await root.api(`/api/sources/${encodeURIComponent(sourceId)}/rows`);
      }
    } catch (errore) {
      stato.errore = errore.message;
    } finally {
      disegna();
    }
  })();
})();
