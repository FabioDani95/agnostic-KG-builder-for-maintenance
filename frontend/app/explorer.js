(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};
  const esc = root.escapeHtml;
  const SVGNS = "http://www.w3.org/2000/svg";

  /* Le posizioni sopravvivono a un cambio di filtro o di vista: il grafo che
     l'operatore ha disposto resta dove l'ha messo. */
  const posizioni = new Map();
  root.dimenticaPosizioni = (prefisso) => {
    [...posizioni.keys()].forEach((chiave) => {
      if (!prefisso || chiave.startsWith(prefisso)) posizioni.delete(chiave);
    });
  };

  const elemento = (nome, attributi) => {
    const nodo = document.createElementNS(SVGNS, nome);
    Object.entries(attributi || {}).forEach(([chiave, valore]) => nodo.setAttribute(chiave, valore));
    return nodo;
  };

  /** Punto in cui il segmento verso (dx,dy) esce dalla pillola. */
  const bordo = (nodo, dx, dy) => {
    const mezzaL = nodo.w / 2 + 3;
    const mezzaH = nodo.h / 2 + 3;
    const scalaX = dx === 0 ? Infinity : mezzaL / Math.abs(dx);
    const scalaY = dy === 0 ? Infinity : mezzaH / Math.abs(dy);
    const scala = Math.min(scalaX, scalaY);
    return { x: nodo.x + dx * scala, y: nodo.y + dy * scala };
  };

  const tronca = (testo, limite) => (testo.length > limite ? `${testo.slice(0, limite - 1)}…` : testo);

  /**
   * Costruisce il grafo una volta sola e poi tocca solo gli attributi: una
   * selezione non ricostruisce niente, quindi non si perde né lo zoom, né la
   * posizione, né il fuoco da tastiera.
   */
  root.creaExplorer = function creaExplorer(contenitore, dati, api) {
    const chiave = (id) => `${dati.chiaveFonte}::${id}`;

    const nodi = dati.nodi.map((voce) => {
      const dimensione = root.dimensioniNodo(tronca(voce.etichetta, 24));
      const memoria = posizioni.get(chiave(voce.id));
      return {
        ...voce, ...dimensione,
        x: memoria ? memoria.x : null,
        y: memoria ? memoria.y : null,
        fx: memoria && memoria.fissato ? memoria.x : null,
        fy: memoria && memoria.fissato ? memoria.y : null,
        vx: 0, vy: 0,
      };
    });
    const perId = new Map(nodi.map((nodo) => [nodo.id, nodo]));

    const svg = elemento("svg", { class: "grafo-svg", tabindex: "0", role: "application" });
    svg.setAttribute("aria-label", api.descrizione);
    const definizioni = elemento("defs");
    ["freccia", "freccia-viva"].forEach((nome) => {
      const marcatore = elemento("marker", {
        id: nome, markerWidth: "9", markerHeight: "9", refX: "8", refY: "3", orient: "auto",
      });
      marcatore.appendChild(elemento("path", { d: "M0,0 L8,3 L0,6 z", class: nome }));
      definizioni.appendChild(marcatore);
    });
    svg.appendChild(definizioni);

    const scena = elemento("g", { class: "grafo-scena" });
    const stratoArchi = elemento("g", { class: "grafo-archi" });
    const stratoNodi = elemento("g", { class: "grafo-nodi" });
    scena.appendChild(stratoArchi);
    scena.appendChild(stratoNodi);
    svg.appendChild(scena);
    contenitore.appendChild(svg);

    const simulazione = root.creaSimulazione(nodi, dati.archi, { centroX: 0, centroY: 0 });

    /* — archi — */
    const archi = simulazione.legami.map((legame, indice) => {
      const originale = dati.archi[indice] || {};
      const gruppo = elemento("g", { class: "arco" });
      const linea = elemento("line", { class: "arco-linea", "marker-end": "url(#freccia)" });
      const presa = elemento("line", {
        class: "arco-presa", role: "button", tabindex: "-1",
        "data-arco": originale.id || "",
      });
      presa.appendChild(elemento("title")).textContent =
        `${legame.da.etichetta} — ${originale.etichettaTipo || ""} — ${legame.a.etichetta}`;
      gruppo.appendChild(linea);
      gruppo.appendChild(presa);
      stratoArchi.appendChild(gruppo);
      return { gruppo, linea, presa, da: legame.da, a: legame.a, id: originale.id };
    });

    /* — nodi — */
    const disegni = nodi.map((nodo) => {
      const gruppo = elemento("g", {
        class: `nodo tipo-${nodo.tipo}`, role: "button", tabindex: "-1",
        "data-nodo": nodo.id,
        "aria-label": `${api.etichettaTipo(nodo.tipo)}: ${nodo.etichetta}. ${api.testoOccorrenze(nodo.occorrenze)}`,
      });
      gruppo.appendChild(elemento("rect", {
        class: "nodo-corpo", x: -nodo.w / 2, y: -nodo.h / 2,
        width: nodo.w, height: nodo.h, rx: nodo.h / 2,
      }));
      const testo = elemento("text", { class: "nodo-testo", x: 0, y: 4, "text-anchor": "middle" });
      testo.textContent = tronca(nodo.etichetta, 24);
      gruppo.appendChild(testo);
      if (nodo.lacuna || nodo.difetto) {
        gruppo.appendChild(elemento("circle", {
          class: nodo.difetto ? "nodo-segno difetto" : "nodo-segno lacuna",
          cx: nodo.w / 2 - 3, cy: -nodo.h / 2 + 3, r: 5,
        }));
      }
      const titolo = elemento("title");
      titolo.textContent = `${api.etichettaTipo(nodo.tipo)}: ${nodo.etichetta}`;
      gruppo.appendChild(titolo);
      stratoNodi.appendChild(gruppo);
      return { gruppo, nodo };
    });

    /* — inquadratura — */
    let k = 1; let tx = 0; let ty = 0;
    const misure = () => contenitore.getBoundingClientRect();

    const applicaVista = () => {
      scena.setAttribute("transform", `translate(${tx} ${ty}) scale(${k})`);
      if (api.onZoom) api.onZoom(k);
    };

    const inquadra = () => {
      const riquadro = simulazione.riquadro();
      const area = misure();
      if (!area.width || !area.height) return;
      const larghezza = Math.max(1, riquadro.maxX - riquadro.minX);
      const altezza = Math.max(1, riquadro.maxY - riquadro.minY);
      /* Sotto una certa scala le etichette non si leggono più: meglio aprire
         un po' più vicini e lasciare che sia l'operatore a spostare la vista. */
      k = Math.min(1.15, Math.max(0.34, Math.min((area.width - 80) / larghezza, (area.height - 80) / altezza)));
      tx = area.width / 2 - ((riquadro.minX + riquadro.maxX) / 2) * k;
      ty = area.height / 2 - ((riquadro.minY + riquadro.maxY) / 2) * k;
      applicaVista();
    };

    const versoScena = (clientX, clientY) => {
      const area = misure();
      return { x: (clientX - area.left - tx) / k, y: (clientY - area.top - ty) / k };
    };

    /* — disegno di un fotogramma — */
    const dipingi = () => {
      disegni.forEach(({ gruppo, nodo }) => {
        gruppo.setAttribute("transform", `translate(${nodo.x.toFixed(1)} ${nodo.y.toFixed(1)})`);
      });
      archi.forEach(({ linea, presa, da, a }) => {
        const dx = a.x - da.x;
        const dy = a.y - da.y;
        const partenza = bordo(da, dx, dy);
        const arrivo = bordo(a, -dx, -dy);
        [linea, presa].forEach((segmento) => {
          segmento.setAttribute("x1", partenza.x.toFixed(1));
          segmento.setAttribute("y1", partenza.y.toFixed(1));
          segmento.setAttribute("x2", arrivo.x.toFixed(1));
          segmento.setAttribute("y2", arrivo.y.toFixed(1));
        });
      });
    };

    const ricorda = () => nodi.forEach((nodo) => posizioni.set(chiave(nodo.id), {
      x: nodo.x, y: nodo.y, fissato: nodo.fx != null,
    }));

    let animazione = 0;
    let vivo = true;
    const ciclo = () => {
      if (!vivo) return;
      const inMoto = simulazione.passo();
      dipingi();
      if (inMoto) animazione = window.requestAnimationFrame(ciclo);
      else { animazione = 0; ricorda(); }
    };
    const anima = () => { if (!animazione && vivo) animazione = window.requestAnimationFrame(ciclo); };

    /* Alla prima apertura il grafo si presenta già sedimentato: nessuno deve
       guardare i fotogrammi in cui i nodi si respingono. */
    const nuovi = nodi.filter((nodo) => !posizioni.has(chiave(nodo.id))).length;
    simulazione.stabilizza(nuovi ? 260 : 40);
    dipingi();
    inquadra();
    ricorda();

    /* — trascinamento di un nodo, pan della scena — */
    let presa = null;
    svg.addEventListener("pointerdown", (evento) => {
      if (evento.button !== 0) return;
      const bersaglio = evento.target.closest("[data-nodo]");
      svg.setPointerCapture(evento.pointerId);
      if (bersaglio) {
        const nodo = perId.get(bersaglio.dataset.nodo);
        const punto = versoScena(evento.clientX, evento.clientY);
        presa = { tipo: "nodo", nodo, scartoX: nodo.x - punto.x, scartoY: nodo.y - punto.y, mosso: false };
        nodo.fx = nodo.x; nodo.fy = nodo.y;
        bersaglio.classList.add("in-mano");
      } else {
        presa = { tipo: "scena", x: evento.clientX, y: evento.clientY, tx, ty, mosso: false };
        svg.classList.add("in-pan");
      }
    });

    svg.addEventListener("pointermove", (evento) => {
      if (!presa) return;
      presa.mosso = true;
      if (presa.tipo === "nodo") {
        const punto = versoScena(evento.clientX, evento.clientY);
        presa.nodo.fx = punto.x + presa.scartoX;
        presa.nodo.fy = punto.y + presa.scartoY;
        simulazione.riscalda(0.22);
        anima();
      } else {
        tx = presa.tx + (evento.clientX - presa.x);
        ty = presa.ty + (evento.clientY - presa.y);
        applicaVista();
      }
    });

    const rilascia = (evento) => {
      if (!presa) return;
      svg.releasePointerCapture?.(evento.pointerId);
      if (presa.tipo === "nodo") {
        svg.querySelector(".in-mano")?.classList.remove("in-mano");
        /* Il nodo trascinato resta dove l'operatore l'ha messo: la disposizione
           è una sua decisione, non un effetto della fisica. Doppio clic o
           "Ridisponi" lo restituiscono alla simulazione. */
        if (!presa.mosso) { presa.nodo.fx = null; presa.nodo.fy = null; }
      } else {
        svg.classList.remove("in-pan");
      }
      const eraNodo = presa.tipo === "nodo" && !presa.mosso;
      const nodoPremuto = presa.nodo;
      presa = null;
      ricorda();
      if (eraNodo) api.onSelezione("nodo", nodoPremuto.id);
    };
    svg.addEventListener("pointerup", rilascia);
    svg.addEventListener("pointercancel", rilascia);

    svg.addEventListener("click", (evento) => {
      const arco = evento.target.closest("[data-arco]");
      if (arco && arco.dataset.arco) api.onSelezione("arco", arco.dataset.arco);
    });

    /* Doppio clic: il nodo torna alla simulazione. */
    svg.addEventListener("dblclick", (evento) => {
      const bersaglio = evento.target.closest("[data-nodo]");
      if (!bersaglio) return;
      const nodo = perId.get(bersaglio.dataset.nodo);
      nodo.fx = null; nodo.fy = null;
      simulazione.riscalda(0.4);
      anima();
    });

    svg.addEventListener("wheel", (evento) => {
      evento.preventDefault();
      const area = misure();
      const puntoX = evento.clientX - area.left;
      const puntoY = evento.clientY - area.top;
      const fattore = Math.exp(-evento.deltaY * 0.0016);
      const nuovo = Math.min(2.6, Math.max(0.12, k * fattore));
      tx = puntoX - ((puntoX - tx) / k) * nuovo;
      ty = puntoY - ((puntoY - ty) / k) * nuovo;
      k = nuovo;
      applicaVista();
    }, { passive: false });

    /* — tastiera: si passa da un nodo all'altro nella direzione della freccia — */
    const vicinoNellaDirezione = (partenza, dirX, dirY) => {
      let migliore = null;
      let punteggio = Infinity;
      nodi.forEach((nodo) => {
        if (nodo === partenza) return;
        const dx = nodo.x - partenza.x;
        const dy = nodo.y - partenza.y;
        const avanti = dx * dirX + dy * dirY;
        if (avanti <= 12) return;
        const laterale = Math.abs(dx * dirY - dy * dirX);
        const costo = avanti + laterale * 2.2;
        if (costo < punteggio) { punteggio = costo; migliore = nodo; }
      });
      return migliore;
    };

    const daFuoco = (nodo) => {
      const disegno = disegni.find((voce) => voce.nodo === nodo);
      if (!disegno) return;
      disegni.forEach((voce) => voce.gruppo.setAttribute("tabindex", "-1"));
      disegno.gruppo.setAttribute("tabindex", "0");
      disegno.gruppo.focus();
      /* Se il nodo è fuori dall'inquadratura la vista lo raggiunge. */
      const area = misure();
      const schermoX = nodo.x * k + tx;
      const schermoY = nodo.y * k + ty;
      const margine = 70;
      if (schermoX < margine) tx += margine - schermoX;
      if (schermoX > area.width - margine) tx -= schermoX - (area.width - margine);
      if (schermoY < margine) ty += margine - schermoY;
      if (schermoY > area.height - margine) ty -= schermoY - (area.height - margine);
      applicaVista();
    };

    svg.addEventListener("keydown", (evento) => {
      const DIREZIONI = {
        ArrowRight: [1, 0], ArrowLeft: [-1, 0], ArrowDown: [0, 1], ArrowUp: [0, -1],
      };
      const corrente = perId.get(
        (evento.target.closest("[data-nodo]") || {}).dataset?.nodo || api.selezione().id
      ) || nodi[0];
      if (evento.key === "Escape") { evento.preventDefault(); api.onSelezione("", ""); return; }
      if (evento.key === "Enter" || evento.key === " ") {
        if (!corrente) return;
        evento.preventDefault();
        api.onSelezione("nodo", corrente.id);
        return;
      }
      if (!DIREZIONI[evento.key] || !corrente) return;
      evento.preventDefault();
      const prossimo = vicinoNellaDirezione(corrente, ...DIREZIONI[evento.key]);
      if (prossimo) daFuoco(prossimo);
    });

    svg.addEventListener("focus", () => {
      if (!svg.querySelector('[data-nodo][tabindex="0"]')) {
        const scelto = perId.get(api.selezione().id) || nodi[0];
        if (scelto) daFuoco(scelto);
      }
    });

    /* — evidenziazione: solo classi, nessuna ricostruzione — */
    const evidenzia = (selezione) => {
      const intorno = new Set();
      if (selezione.kind === "node") {
        intorno.add(selezione.id);
        simulazione.legami.forEach((legame) => {
          if (legame.da.id === selezione.id) intorno.add(legame.a.id);
          if (legame.a.id === selezione.id) intorno.add(legame.da.id);
        });
      } else if (selezione.kind === "relation") {
        const arco = archi.find((voce) => voce.id === selezione.id);
        if (arco) { intorno.add(arco.da.id); intorno.add(arco.a.id); }
      }
      const attivo = intorno.size > 0;
      disegni.forEach(({ gruppo, nodo }) => {
        gruppo.classList.toggle("scelto", selezione.kind === "node" && nodo.id === selezione.id);
        gruppo.classList.toggle("spento", attivo && !intorno.has(nodo.id));
      });
      archi.forEach(({ gruppo, linea, da, a, id }) => {
        const vivoArco = selezione.kind === "relation"
          ? id === selezione.id
          : attivo && intorno.has(da.id) && intorno.has(a.id);
        gruppo.classList.toggle("vivo", Boolean(vivoArco));
        gruppo.classList.toggle("spento", attivo && !vivoArco);
        linea.setAttribute("marker-end", vivoArco ? "url(#freccia-viva)" : "url(#freccia)");
      });
    };

    const osservatore = new ResizeObserver(() => applicaVista());
    osservatore.observe(contenitore);

    return {
      evidenzia,
      inquadra,
      zoom(passoZoom) {
        const area = misure();
        const nuovo = Math.min(2.6, Math.max(0.12, k * passoZoom));
        tx = area.width / 2 - ((area.width / 2 - tx) / k) * nuovo;
        ty = area.height / 2 - ((area.height / 2 - ty) / k) * nuovo;
        k = nuovo;
        applicaVista();
      },
      ridisponi() {
        nodi.forEach((nodo) => { nodo.fx = null; nodo.fy = null; });
        root.dimenticaPosizioni(dati.chiaveFonte);
        simulazione.riscalda(1);
        anima();
        window.setTimeout(inquadra, 700);
      },
      distruggi() {
        vivo = false;
        if (animazione) window.cancelAnimationFrame(animazione);
        osservatore.disconnect();
        ricorda();
        svg.remove();
      },
    };
  };
})();
