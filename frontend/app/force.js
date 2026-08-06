(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};

  /* ==========================================================================
     Simulazione a forze per un grafo di conoscenza.

     I nodi sono pallini, e la loro grandezza dice quanto sono collegati: a
     colpo d'occhio si vedono i mozzi, i grappoli e i solitari — la forma del
     sapere che c'è in un file, prima ancora di leggere un solo nome. Il nome
     si accende quando serve, e non partecipa alla separazione: se ne tenesse
     conto, il grafo si dilaterebbe per etichette quasi sempre spente.

     Nessuna libreria esterna: l'applicativo non ha dipendenze nel browser.
     ====================================================================== */

  const ALPHA_MIN = 0.0015;
  const ALPHA_DECAY = 0.022;
  const VELOCITY_DECAY = 0.62;

  /** Raggio del pallino a partire da quanti collegamenti ha. */
  root.raggioNodo = function raggioNodo(collegamenti) {
    return Math.min(17, 5.5 + Math.sqrt(Math.max(0, Number(collegamenti) || 0)) * 2.6);
  };

  root.creaSimulazione = function creaSimulazione(nodi, archi, opzioni) {
    const config = opzioni || {};
    const centroX = config.centroX || 0;
    const centroY = config.centroY || 0;
    /* Quanto si respingono. La taratura di prima era fatta sulle pillole
       larghe: con i pallini, che occupano un quinto dello spazio, la stessa
       forza impacchettava duecento elementi in una palla unica. Il termine di
       scala corregge solo i grafi piccoli, dove pochi nodi lontanissimi
       sarebbero altrettanto illeggibili; sopra la quarantina la repulsione è
       quella piena. */
    const scala = Math.sqrt(Math.max(1, nodi.length));
    const repulsione = (config.repulsione || 6400) * Math.max(1, 6.5 / scala);
    const gravita = config.gravita || 0.022;

    const indice = new Map(nodi.map((nodo) => [nodo.id, nodo]));
    const legami = archi
      .map((arco) => ({ da: indice.get(arco.da), a: indice.get(arco.a) }))
      .filter((legame) => legame.da && legame.a && legame.da !== legame.a);

    /* Un nodo molto collegato deve muoversi meno degli altri: fa da ancora. */
    const grado = new Map(nodi.map((nodo) => [nodo.id, 0]));
    legami.forEach((legame) => {
      grado.set(legame.da.id, grado.get(legame.da.id) + 1);
      grado.set(legame.a.id, grado.get(legame.a.id) + 1);
    });

    /* Disposizione iniziale a raggiera per tipo: la prima immagine è già
       ordinata e la simulazione parte da uno stato sensato invece che dal caos. */
    const perTipo = new Map();
    nodi.forEach((nodo) => {
      if (!perTipo.has(nodo.tipo)) perTipo.set(nodo.tipo, []);
      perTipo.get(nodo.tipo).push(nodo);
    });
    const tipi = [...perTipo.keys()];
    tipi.forEach((tipo, indiceTipo) => {
      const gruppo = perTipo.get(tipo);
      const angoloTipo = (indiceTipo / tipi.length) * Math.PI * 2;
      const raggio = 110 + Math.sqrt(nodi.length) * 58;
      gruppo.forEach((nodo, posizione) => {
        if (nodo.x != null) return;
        const sfasamento = ((posizione / Math.max(1, gruppo.length)) - 0.5) * 1.1;
        const distanza = raggio * (0.45 + 0.55 * ((posizione % 5) / 5 + 0.4));
        nodo.x = centroX + Math.cos(angoloTipo + sfasamento) * distanza;
        nodo.y = centroY + Math.sin(angoloTipo + sfasamento) * distanza;
      });
      gruppo.forEach((nodo) => { nodo.vx = nodo.vx || 0; nodo.vy = nodo.vy || 0; });
    });

    let alpha = 1;

    const passo = () => {
      if (alpha < ALPHA_MIN) return false;
      alpha += (0 - alpha) * ALPHA_DECAY;

      // — repulsione fra tutte le coppie —
      for (let i = 0; i < nodi.length; i += 1) {
        const a = nodi[i];
        for (let j = i + 1; j < nodi.length; j += 1) {
          const b = nodi[j];
          let dx = b.x - a.x;
          let dy = b.y - a.y;
          let d2 = dx * dx + dy * dy;
          if (d2 < 1) { dx = (i % 2 ? 1 : -1) * 0.7; dy = (j % 2 ? 1 : -1) * 0.7; d2 = 1; }
          const forza = (repulsione * alpha) / d2;
          const d = Math.sqrt(d2);
          const fx = (dx / d) * forza;
          const fy = (dy / d) * forza;
          a.vx -= fx; a.vy -= fy;
          b.vx += fx; b.vy += fy;
        }
      }

      // — molla sui legami —
      legami.forEach((legame) => {
        const a = legame.da;
        const b = legame.a;
        /* La lunghezza di riposo non dipende quasi più dalla grandezza dei
           pallini: erano le pillole a doverla allungare per non toccarsi. */
        const riposo = 108 + (a.w + b.w) / 2.4;
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const d = Math.hypot(dx, dy) || 0.01;
        const spinta = ((d - riposo) / d) * alpha * 0.42;
        /* Il nodo più collegato cede meno: la ripartizione segue i gradi. */
        const ga = grado.get(a.id) + 1;
        const gb = grado.get(b.id) + 1;
        const quotaA = gb / (ga + gb);
        const quotaB = ga / (ga + gb);
        a.vx += dx * spinta * quotaA; a.vy += dy * spinta * quotaA;
        b.vx -= dx * spinta * quotaB; b.vy -= dy * spinta * quotaB;
      });

      // — richiamo al centro, per non perdere pezzi fuori campo —
      nodi.forEach((nodo) => {
        nodo.vx += (centroX - nodo.x) * gravita * alpha;
        nodo.vy += (centroY - nodo.y) * gravita * alpha;
      });

      // — integrazione con smorzamento —
      nodi.forEach((nodo) => {
        if (nodo.fx != null) { nodo.x = nodo.fx; nodo.y = nodo.fy; nodo.vx = 0; nodo.vy = 0; return; }
        nodo.vx *= VELOCITY_DECAY;
        nodo.vy *= VELOCITY_DECAY;
        nodo.x += nodo.vx;
        nodo.y += nodo.vy;
      });

      // — separazione rettangolare: due pillole non si coprono mai —
      for (let ripetizione = 0; ripetizione < 2; ripetizione += 1) {
        for (let i = 0; i < nodi.length; i += 1) {
          const a = nodi[i];
          for (let j = i + 1; j < nodi.length; j += 1) {
            const b = nodi[j];
            const minimaX = (a.w + b.w) / 2 + 20;
            const minimaY = (a.h + b.h) / 2 + 18;
            const dx = b.x - a.x;
            const dy = b.y - a.y;
            const sovrapX = minimaX - Math.abs(dx);
            const sovrapY = minimaY - Math.abs(dy);
            if (sovrapX <= 0 || sovrapY <= 0) continue;
            /* Si separa lungo l'asse in cui la sovrapposizione è minore: il
               movimento necessario è il più piccolo possibile. */
            if (sovrapX / minimaX < sovrapY / minimaY) {
              const spinta = (sovrapX / 2) * (dx < 0 ? -1 : 1);
              if (a.fx == null) a.x -= spinta;
              if (b.fx == null) b.x += spinta;
            } else {
              const spinta = (sovrapY / 2) * (dy < 0 ? -1 : 1);
              if (a.fx == null) a.y -= spinta;
              if (b.fx == null) b.y += spinta;
            }
          }
        }
      }
      return true;
    };

    return {
      nodi,
      legami,
      passo,
      get alpha() { return alpha; },
      /** Rimette in moto la simulazione dopo un'interazione. */
      riscalda(valore) { alpha = Math.max(alpha, valore == null ? 0.32 : valore); },
      /** Fa sedimentare il grafo senza mostrare i primi fotogrammi caotici. */
      stabilizza(passi) {
        for (let i = 0; i < (passi || 220); i += 1) passo();
      },
      /** Riquadro occupato, per inquadrare il grafo nello spazio disponibile. */
      riquadro() {
        let minX = Infinity; let minY = Infinity; let maxX = -Infinity; let maxY = -Infinity;
        nodi.forEach((nodo) => {
          minX = Math.min(minX, nodo.x - nodo.w / 2);
          maxX = Math.max(maxX, nodo.x + nodo.w / 2);
          minY = Math.min(minY, nodo.y - nodo.h / 2);
          maxY = Math.max(maxY, nodo.y + nodo.h / 2);
        });
        if (!Number.isFinite(minX)) return { minX: 0, minY: 0, maxX: 1, maxY: 1 };
        return { minX, minY, maxX, maxY };
      },
    };
  };
})();
