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

  /** Punto in cui il segmento verso (dx,dy) esce dal pallino. */
  const bordo = (nodo, dx, dy) => {
    const distanza = Math.hypot(dx, dy) || 1;
    const raggio = nodo.r + 3;
    return { x: nodo.x + (dx / distanza) * raggio, y: nodo.y + (dy / distanza) * raggio };
  };

  /* Quante etichette restano accese senza selezione: i pochi nodi più
     collegati, quelli che danno il senso della forma. Tutte insieme sono
     illeggibili già a quaranta elementi. */
  const ETICHETTE_FISSE = 6;
  /* Sopra questo ingrandimento c'è posto per leggere tutti i nomi. */
  const ZOOM_ETICHETTE = 0.95;
  /* Sotto questa scala un pallino acceso in mezzo a duecento resta da cercare
     anche se è dentro l'inquadratura: scegliendo, la vista ci va sopra. */
  const ZOOM_VICINO = 0.5;
  /* Quanto ci si avvicina scegliendo: oltre, si perde il contesto attorno. */
  const ZOOM_SCELTA = 1.4;

  const tronca = (testo, limite) => (testo.length > limite ? `${testo.slice(0, limite - 1)}…` : testo);

  /**
   * Costruisce il grafo una volta sola e poi tocca solo gli attributi: una
   * selezione non ricostruisce niente, quindi non si perde né lo zoom, né la
   * posizione, né il fuoco da tastiera.
   */
  root.creaExplorer = function creaExplorer(contenitore, dati, api) {
    const chiave = (id) => `${dati.chiaveFonte}::${id}`;

    /* Quanto un elemento è collegato decide quanto è grande: i mozzi si vedono
       da soli, senza legenda e senza leggere un solo nome. */
    const grado = new Map();
    dati.archi.forEach((arco) => {
      grado.set(arco.da, (grado.get(arco.da) || 0) + 1);
      grado.set(arco.a, (grado.get(arco.a) || 0) + 1);
    });

    const nodi = dati.nodi.map((voce) => {
      const memoria = posizioni.get(chiave(voce.id));
      const raggio = root.raggioNodo(grado.get(voce.id) || 0);
      return {
        ...voce,
        r: raggio,
        /* La simulazione separa riquadri: per un pallino il riquadro è il
           pallino stesso, con un margine. Il nome, che si accende solo quando
           serve, non partecipa alla separazione — altrimenti il grafo si
           dilaterebbe per etichette che quasi sempre sono spente. */
        w: raggio * 2 + 13,
        h: raggio * 2 + 13,
        x: memoria ? memoria.x : null,
        y: memoria ? memoria.y : null,
        fx: memoria && memoria.fissato ? memoria.x : null,
        fy: memoria && memoria.fissato ? memoria.y : null,
        vx: 0, vy: 0,
      };
    });
    const perId = new Map(nodi.map((nodo) => [nodo.id, nodo]));
    const fisse = new Set([...nodi]
      .sort((a, b) => (grado.get(b.id) || 0) - (grado.get(a.id) || 0))
      .slice(0, ETICHETTE_FISSE)
      .filter((nodo) => (grado.get(nodo.id) || 0) > 0)
      .map((nodo) => nodo.id));

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
      /* Nessuna freccia finché il filo non è quello che stai guardando: a
         ottanta collegamenti le punte diventano un brulichio, e il verso lo si
         legge comunque a parole nella colonna di destra. */
      const linea = elemento("line", { class: "arco-linea" });
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
        class: `nodo tipo-${nodo.tipo}${fisse.has(nodo.id) ? " nome-fisso" : ""}`,
        role: "button", tabindex: "-1",
        "data-nodo": nodo.id,
        "aria-label": `${api.etichettaTipo(nodo.tipo)}: ${nodo.etichetta}. ${api.testoOccorrenze(nodo.occorrenze)}`,
      });
      /* Un bersaglio più largo del pallino: un elemento poco collegato è un
         disco di dodici pixel, e nessuno deve inseguirlo col puntatore. */
      gruppo.appendChild(elemento("circle", {
        class: "nodo-presa", cx: 0, cy: 0, r: Math.max(nodo.r + 9, 15),
      }));
      if (nodo.lacuna || nodo.difetto) {
        gruppo.appendChild(elemento("circle", {
          class: `nodo-alone ${nodo.difetto ? "difetto" : "lacuna"}`,
          cx: 0, cy: 0, r: nodo.r + 4,
        }));
      }
      gruppo.appendChild(elemento("circle", { class: "nodo-corpo", cx: 0, cy: 0, r: nodo.r }));
      /* Il nome vive in un gruppo suo, contro-scalato: disegnato nelle
         coordinate della scena rimpiccioliva con lo zoom, e da lontano — che è
         il modo in cui si guarda un grafo di duecento elementi — non si
         leggeva più. Così resta della stessa misura a schermo sempre. */
      const nome = elemento("g", { class: "nodo-nome" });
      const testo = elemento("text", { class: "nodo-testo", x: 0, y: 0, "text-anchor": "middle" });
      testo.textContent = tronca(nodo.etichetta, 26);
      nome.appendChild(testo);
      gruppo.appendChild(nome);
      const titolo = elemento("title");
      titolo.textContent = `${api.etichettaTipo(nodo.tipo)}: ${nodo.etichetta}`;
      gruppo.appendChild(titolo);
      stratoNodi.appendChild(gruppo);
      return { gruppo, nome, nodo };
    });

    /* — inquadratura — */
    let k = 1; let tx = 0; let ty = 0;
    let voloTimer = 0;
    const misure = () => contenitore.getBoundingClientRect();

    /* Il nome sta sotto il pallino a distanza costante sullo schermo: il
       pallino cresce con lo zoom, la scritta no. La distanza si ricalcola
       solo quando la scala cambia davvero. */
    let scalaNomi = 0;
    const disponiNomi = () => {
      if (scalaNomi === k) return;
      scalaNomi = k;
      disegni.forEach(({ nome, nodo }) => nome.setAttribute(
        "transform", `translate(0 ${(nodo.r + 13 / k).toFixed(2)}) scale(${(1 / k).toFixed(4)})`
      ));
    };

    const applicaVista = (morbido) => {
      /* Un salto di inquadratura deciso dall'applicativo si accompagna, o
         nessuno capisce da dove a dove è andata la vista. Trascinare e
         ingrandire restano invece immediati: lì la mano è dell'operatore. */
      if (morbido) {
        scena.classList.add("in-volo");
        window.clearTimeout(voloTimer);
        voloTimer = window.setTimeout(() => scena.classList.remove("in-volo"), 380);
      }
      scena.setAttribute("transform", `translate(${tx} ${ty}) scale(${k})`);
      disponiNomi();
      /* Da vicino c'è posto per tutti i nomi; da lontano sarebbero una macchia
         di testo sovrapposto, e la forma del grafo — l'unica cosa che si legge
         da lontano — sparirebbe sotto. */
      svg.classList.toggle("con-nomi", k >= ZOOM_ETICHETTE);
      if (api.onZoom) api.onZoom(k);
    };

    /* La prima inquadratura può cadere prima che il riquadro esista davvero:
       chi monta la mappa lo fa nello stesso giro in cui la disegna, e lì la
       misura è ancora zero. Finché non riesce, la si ritenta — altrimenti il
       grafo resta a cavallo dell'origine, mezzo fuori campo. */
    let inquadrato = false;
    /* Finché la vista non l'ha mossa l'operatore, l'inquadratura segue il
       riquadro. La prima misura cade quasi sempre prima che la pagina abbia
       l'altezza definitiva: fermandosi lì, il grafo restava rimpicciolito per
       una finestra che nel frattempo si era aperta — ed è così che duecento
       elementi diventavano una palla. */
    let mossaDaMano = false;

    const inquadra = () => {
      const riquadro = simulazione.riquadro();
      const area = misure();
      if (!area.width || !area.height) return;
      inquadrato = true;
      mossaDaMano = false;
      const larghezza = Math.max(1, riquadro.maxX - riquadro.minX);
      const altezza = Math.max(1, riquadro.maxY - riquadro.minY);
      /* Sotto una certa scala le etichette non si leggono più: meglio aprire
         un po' più vicini e lasciare che sia l'operatore a spostare la vista. */
      k = Math.min(1.15, Math.max(0.34, Math.min((area.width - 80) / larghezza, (area.height - 80) / altezza)));
      tx = area.width / 2 - ((riquadro.minX + riquadro.maxX) / 2) * k;
      ty = area.height / 2 - ((riquadro.minY + riquadro.maxY) / 2) * k;
      applicaVista();
    };

    /**
     * Porta la vista sulla scelta e su quello che le sta attorno.
     *
     * Con duecento pallini a un terzo di scala «si illumina» non basta: il
     * puntino acceso resta da cercare. Non si allontana mai — chi era già
     * vicino resta vicino — e non si muove affatto se quello che serve è già
     * inquadrato e abbastanza grande.
     */
    const inquadraSu = (ids) => {
      const scelti = [...ids].map((id) => perId.get(id)).filter(Boolean);
      const area = misure();
      if (!scelti.length || !area.width || !area.height) return;
      const dentro = scelti.every((nodo) => {
        const schermoX = nodo.x * k + tx;
        const schermoY = nodo.y * k + ty;
        return schermoX > 80 && schermoX < area.width - 80
          && schermoY > 60 && schermoY < area.height - 60;
      });
      if (dentro && k >= ZOOM_VICINO) return;
      mossaDaMano = true;
      let minX = Infinity; let minY = Infinity; let maxX = -Infinity; let maxY = -Infinity;
      scelti.forEach((nodo) => {
        minX = Math.min(minX, nodo.x - nodo.w / 2);
        maxX = Math.max(maxX, nodo.x + nodo.w / 2);
        minY = Math.min(minY, nodo.y - nodo.h / 2);
        maxY = Math.max(maxY, nodo.y + nodo.h / 2);
      });
      const larghezza = Math.max(1, maxX - minX);
      const altezza = Math.max(1, maxY - minY);
      k = Math.min(ZOOM_SCELTA, Math.max(k, Math.min(
        (area.width - 170) / larghezza, (area.height - 130) / altezza
      )));
      tx = area.width / 2 - ((minX + maxX) / 2) * k;
      ty = area.height / 2 - ((minY + maxY) / 2) * k;
      applicaVista(true);
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
    disponiNomi();
    inquadra();
    ricorda();

    /* — trascinamento di un nodo, pan della scena — */
    let presa = null;
    svg.addEventListener("pointerdown", (evento) => {
      if (evento.button !== 0) return;
      /* La mano vince su qualunque spostamento in corso: se si trascina mentre
         la vista sta ancora andando, si trascina subito. */
      scena.classList.remove("in-volo");
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
        mossaDaMano = true;
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
      mossaDaMano = true;
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
        /* Chi sta attorno alla scelta dice il proprio nome: è quello il modo
           di leggere un collegamento, non di indovinarlo dalla direzione. */
        gruppo.classList.toggle("vicino", attivo && intorno.has(nodo.id));
      });
      archi.forEach(({ gruppo, linea, da, a, id }) => {
        const vivoArco = selezione.kind === "relation"
          ? id === selezione.id
          : attivo && intorno.has(da.id) && intorno.has(a.id);
        gruppo.classList.toggle("vivo", Boolean(vivoArco));
        gruppo.classList.toggle("spento", attivo && !vivoArco);
        if (vivoArco) linea.setAttribute("marker-end", "url(#freccia-viva)");
        else linea.removeAttribute("marker-end");
      });
      if (attivo) inquadraSu(intorno);
    };

    const osservatore = new ResizeObserver(() => (
      inquadrato && mossaDaMano ? applicaVista() : inquadra()
    ));
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
        mossaDaMano = true;
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
