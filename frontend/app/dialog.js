(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};
  const esc = root.escapeHtml;

  /** Accessible, reusable confirmation surface for consequential actions. */
  root.confirmAction = function confirmAction(options) {
    const settings = options || {};
    return new Promise((resolve) => {
      const dialog = document.createElement("dialog");
      dialog.className = "modale-azione";
      dialog.innerHTML = `
        <form method="dialog" class="modale-card">
          <div class="modale-icona ${esc(settings.tone || "warning")}" aria-hidden="true">${settings.tone === "danger" ? "!" : "i"}</div>
          <div class="modale-testo">
            <h2>${esc(settings.title || "")}</h2>
            <p>${esc(settings.body || "")}</p>
            ${settings.detail ? `<p class="modale-dettaglio">${esc(settings.detail)}</p>` : ""}
          </div>
          <div class="modale-azioni">
            <button type="submit" class="btn quieto" value="cancel">${esc(settings.cancelLabel || "Annulla")}</button>
            <button type="submit" class="btn ${settings.tone === "danger" ? "pericolo" : "primario"}" value="confirm">${esc(settings.confirmLabel || "Conferma")}</button>
          </div>
        </form>`;
      document.body.appendChild(dialog);
      dialog.addEventListener("close", () => {
        const confirmed = dialog.returnValue === "confirm";
        dialog.remove();
        resolve(confirmed);
      }, { once: true });
      dialog.addEventListener("cancel", (event) => {
        event.preventDefault();
        dialog.close("cancel");
      });
      dialog.showModal();
      dialog.querySelector('[value="cancel"]')?.focus();
    });
  };
})();
