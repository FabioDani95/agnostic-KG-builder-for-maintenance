# Design del prototipo frontend

Decisioni visive e di navigazione prese una volta sola. Ogni schermata usa **solo** questi valori;
un valore nuovo si aggiunge qui (e in `frontend/src/styles/tokens.css`) prima di usarlo.

Dal 29 settembre 2026 lo stile è **industriale**, sul modello del web-client DigiFactor
(`~/web-client/DESIGN.md`, «The Control Room»): testo piccolo, spazi stretti, cornice scura con il
logo, azioni nella barra del percorso, tabelle compatte. Questa scelta di Fabio sostituisce lo
stile «alla Apple» della sezione 4 di [PROMPT_FRONTEND.md](PROMPT_FRONTEND.md); per il resto il
brief vale ancora. Il grafo 3D non cambia.

## 1. Principi

1. **Sala controllo.** Chi guarda capisce subito lo stato e che cosa fare: ogni versione dice il
   suo **prossimo passo**, e quello che aspetta una persona si vede da ogni schermata.
2. **La barra laterale porta ai luoghi, la barra del percorso contiene le azioni.** Nessun luogo
   ha due ingressi nella stessa barra; nessuna azione sta nella barra laterale.
3. **Il grafo comanda.** Nelle schermate del grafo la barra laterale resta ridotta, i pannelli
   sono agganciati ai bordi e compaiono solo quando hanno qualcosa da dire.
4. **Piatto.** La struttura la fanno bordi da 1 px e fondi diversi, non ombre.
5. **Il colore è uno stato.** Verde, arancio, rosso, blu solo per il loro significato, sempre
   con la parola accanto.
6. **Robusto.** Ogni attesa ha il suo segno, ogni errore una frase e «Riprova», ogni vista si
   può ritrovare dall'indirizzo e con «indietro».

## 2. Cornice e navigazione

Ogni schermata ha la stessa cornice, a tutta finestra.

**Barra laterale** scura (`--rail`), larga 56 px, solo icone: niente scritte accanto ai simboli, i
nomi compaiono al passaggio e al focus. In alto il solo logo, in un blocco alto quanto la barra del
percorso (48 px), così le due barre finiscono sulla stessa linea.

| Posto | Che cosa |
| --- | --- |
| Logo | la casa: tutti i grafi (libreria) |
| Tocca a te | quello che aspetta una persona; il numero arancio conta le esecuzioni ferme per te |
| Esecuzioni | tutte le esecuzioni di tutti i manuali, con tempo e costo di ciascuna |
| Ontologia | lo schema fisso che ogni grafo segue |
| In corso (solo se c'è) | spia blu che pulsa, nome del manuale: porta dritto all'esecuzione |

**Barra del percorso** alta 48 px, fondo `--crumbs`, testo 13 px: i passaggi sottolineati
separati da `›` e il titolo della pagina in grassetto (è l'`h1`, e dà il titolo alla scheda del
browser). A destra le azioni della pagina: `+ Nuovo grafo`, `+ Nuova versione`, ricerca,
versione, ✓ Approva, ■ Ferma. Se manca spazio si accorciano i passaggi, non le azioni.

**Scorciatoie:** «/» porta alla ricerca della pagina; «Esc» svuota la ricerca o chiude il
pannello di destra del grafo.

**Indirizzo:** filtro, ricerca e ordinamento della libreria stanno nell'indirizzo
(`?mostra=da-rivedere&cerca=pompa&ordina=pagine&verso=giu`).

Schermo minimo **1024 × 700**; sotto 1280 px i pannelli del grafo si stringono (232 e 304 px).

## 3. Griglia e spaziature

Unità **4 px**. Scala: `4, 8, 12, 16, 24, 32`. Altezze: controlli 32 px, righe di tabella 36 px,
intestazione di card 44 px, barra del percorso 48 px, barra di stato 28 px, voci della barra
laterale 40 px. Bordi 1 px, focus 2 px.

## 4. Tipografia

- **Onest** per tutta l'interfaccia (Google Fonts, con ripiego sul font di sistema).
- **JetBrains Mono** per codici e numeri da leggere come dati: commit, pagine, contatori, tempi,
  costi, date compatte delle tabelle, sigle dei produttori, tasti.
- Pesi 400, 500, 600, 700. Numeri con `tabular-nums`, allineati a destra nelle tabelle.
- Maiuscole normali nel testo (frase, non «Title Case»). In maiuscolo, via CSS, solo i titoli
  delle card e dei pannelli e le etichette dei dati (11–12 px, spaziatura 0,05–0,06 em).

| Nome | Dimensione / interlinea | Peso | Uso |
| --- | --- | --- | --- |
| `title` | 18 / 24 | 700 | la domanda in «Domande per te» |
| `heading`, `large` | 14 / 20 | 600 / 400 | nome del nodo scelto, valori dei dati |
| `body` | 13 / 20 | 400 | testo, celle, pulsanti, campi |
| `small` | 12 / 16 | 400 o 600 | intestazioni di colonna, dettagli, legenda |
| `label` | 11 / 16 | 600, maiuscolo | titoli dei pannelli scuri, etichette dei dati |

Il testo del manuale e le descrizioni dello schema restano nella loro lingua.

## 5. Colore

Palette **grafite calda** (stone), scelta da Fabio il 30 settembre 2026 fra quattro proposte.
Valori in `tokens.css`.

| Token | Valore | Uso |
| --- | --- | --- |
| `--rail` | `#1c1917` | barra laterale, pannelli del grafo (`--panel-d`) |
| `--accent` | `#d97706` | posto attivo nella barra laterale, nodo del logo; link `#b45309` |
| `--crumbs` | `#e7e5e4` | barra del percorso |
| `--primary` | `#292524` | pulsante principale, segmento scelto; `#0c0a09` al passaggio |
| `--head` | `#e7e5e4` | intestazione delle tabelle, fondo dei controlli disattivati |
| `--row` | `#f5f5f4` | righe delle tabelle; `--subtle` `#fafaf9` al passaggio, nelle intestazioni di card e come fondo pagina |
| `--text` / `--text-2` | `#1c1917` / `#78716c` | testo principale e secondario |
| `--line` / `--line-soft` | `#d6d3d1` / `#e7e5e4` | righe tra le righe di tabella / bordi di card |
| `--stage` | `#0c0a09` | fondo del grafo e dello schema |
| `--text-d` / `--text-d2` | `#e7e5e4` / `#a8a29e` | testo sui pannelli scuri |

**Segnali** (solo come stato, sempre con la parola): `--ok` `#16a34a` approvato, fatto;
`--warn` `#f97316` tocca a te, da approvare, incompleto; `--stop` `#ef4444`
non riuscita; `--run` `#3b82f6` in corso. Nei distintivi il fondo è la tinta
chiara dello stesso colore e il testo la tinta scura. Sul scuro il pulsante principale è chiaro
(`--crumbs`).

**Grafo** (invariato). Tipi di nodo: Macchina `#f5f5f7`, Sintomo `#ff9f0a`, Codice di errore
`#ff6482`, Causa `#bf5af2`, Azione `#64d2ff`, Componente `#8e8e93`. Archi: proposto grigio
`#636366` a 0,5; verificato `#30d158`; in dubbio `#ffd60a` tratteggiato; scartato sparisce;
aggiunto dal codice grigio più tenue. Lo schema dell'Ontologia usa gli stessi colori.

## 6. Forme, bordi, ombre

- Raggio **4 px** ovunque (2 px per targhette e numeri dei passi). Cerchi solo per nodi,
  legenda e spie dei passi.
- Ombre solo per ciò che sta sopra: l'elenco dei risultati della ricerca, il riquadro di fine
  esecuzione sul grafo, i suggerimenti della barra laterale.
- Niente gradienti. Un solo motivo ammesso: il bordo tratteggiato dell'area in cui si trascina
  il PDF.

## 7. Movimento

150 ms, `cubic-bezier(0.25, 0.1, 0.25, 1)`, solo per un cambio di stato. I pulsanti si
schiacciano appena (0,97). Due movimenti continui, perché dicono che qualcosa sta lavorando: la
spia «In corso» che pulsa e il segno di caricamento che gira. Nel grafo un nodo nuovo cresce in
240 ms; la fisica si ferma al primo tocco. Con `prefers-reduced-motion` niente pulsazione né
crescita, e il caricamento gira lento.

## 8. Icone e logo

- Un solo set lineare, da [Lucide](https://lucide.dev) (licenza ISC), tratto 1,75, 16 px accanto
  a un testo, 20 px nella barra laterale. Nelle azioni l'icona sta accanto alla parola; da sola
  solo nelle righe delle tabelle (apri il grafo, rigioca) e per chiudere, sempre con
  `aria-label` e suggerimento.
- **Logo:** dado esagonale con un grafo a tre nodi, il nodo in alto arancio. Nella barra
  laterale e come favicon (`frontend/public/favicon.svg`).
- **Produttori:** la sigla su una targhetta scura in mono (ABB, AC per Atlas Copco, GRA per
  Graco), mai il loro marchio. I manuali si chiamano ovunque «marca modello».

## 9. Componenti

| Componente | Specifica |
| --- | --- |
| **Pulsante principale** | 32 px, padding 12 px, fondo `--primary`, testo bianco 600. Uno per schermata: di solito il prossimo passo. |
| **Pulsante secondario** | come il principale, fondo `--fill` `#f1f5f9`. Sul scuro fondo `#1e293b`. |
| **Pulsante della barra** | trasparente sul fondo della barra, `--head` al passaggio. |
| **Campo** | 32 px, bordo `--line`, raggio 4. Etichetta 12 px 600 sopra, a 4 px; `*` rosso se obbligatorio, bordo rosso se manca. Con scorciatoia, il tasto `/` a destra. |
| **Controllo segmentato** | fondo `--fill`, segmento scelto pieno `--primary` e testo bianco (sul scuro: pieno `--crumbs`). |
| **Scelta con spiegazione** | righe con pallino, nome e frase: per le scelte che cambiano il costo o il lavoro di una persona (chi risponde ai dubbi). |
| **Card** | bordo 1 px `--line-soft`, raggio 4. Intestazione 44 px su `--subtle` con titolo maiuscolo e conteggio, a destra una nota o le azioni della card. Corpo 12 px, oppure una tabella a filo. |
| **Tabella** | intestazione 36 px su `--head`, 12 px 700; le colonne ordinabili hanno la freccia. Righe 36 px su `--row`, separate da 1 px `--line`; riga intera cliccabile con focus visibile; azioni della riga in un'ultima colonna senza titolo. |
| **Distintivo di stato** | 20 px, quadratino da 8 px del colore del segnale e la parola. |
| **Passi** | tre celle affiancate (Estrazione, Domande, Approvazione): spia (✓ verde fatto, arancio tocca a te, contorno arancio facoltativo, ✕ rosso fermo, vuota in attesa), nome, stato a parole. |
| **Cifre** | una riga di celle: etichetta maiuscola sopra, valore in mono sotto. |
| **Pannello agganciato** | fondo `--panel-d`, bordo 1 px `#1e293b` verso il grafo. Sezioni 12 × 16 px; titolo `label` in `--text-d2`; ✕ in alto a destra. Sinistro 264 px, destro 352 px. |
| **Barra di stato** | 28 px sotto il grafo: contatori in mono e, a destra, una riga di contesto (ultima relazione trovata). |
| **Riquadro di fine esecuzione** | sul grafo, in basso al centro: com'è andata (tempo, costo, relazioni) e il prossimo passo. Si chiude con ✕. |
| **Attesa ed errore** | segno che gira al posto del contenuto; errore rosso scuro con icona, frase e «Riprova». |

Stati vuoti: una frase che dice che cosa succede e, se esiste, il pulsante per rimediare.

## 10. Schermate

**Grafi** (casa). Barra: `+ Nuovo grafo`. Card «Manuali [N]» con, nell'intestazione, il filtro
Tutti / Da rivedere / Approvati e la ricerca; tabella ordinabile: Manuale (sigla e nome),
Pagine, Versione, Relazioni verificate, Domande aperte, Durata, Costo, Stato, e l'icona per aprire
subito il grafo (o seguire l'esecuzione).

**Tocca a te.** «Aspettano te»: le esecuzioni ferme per una persona, con il prossimo passo
(«Rispondi alle 10 domande», «Controlla e approva»). «In corso», se c'è. «Dubbi nei grafi
approvati»: domande rimaste senza risposta, che non bloccano nulla.

**Esecuzioni.** Card «Esecuzioni [N]»: Tutte / Dall'interfaccia / Campagna; tabella ordinabile: Data, Manuale, Versione, Esito, Durata, Costo. Una riga porta al suo passo.

**Ontologia.** Lo schema disegnato su fondo scuro, a colonne dai tipi di partenza (Macchina,
Sintomo) alle azioni; tratto pieno per le relazioni estratte dal modello, tratteggio per quelle
aggiunte dal codice. Sotto, tipi di nodo (con proprietà, `*` obbligatorie) e relazioni.

**Manuale.** Barra: Grafi › [macchina], `+ Nuova versione`. Card «Macchina» (cinque celle).
Card «Versione attuale»: i passi, le cifre (verificate, in dubbio, escluse, domande, durata,
costo), il prossimo passo come pulsante principale, «Apri il grafo», «Rigioca l'esecuzione».
Card «Versioni [N]»: Data, Versione, Codice, Verificate, Durata, Domande, Costo, Esito, ▷.

**Nuovo grafo** (e nuova versione, con `?manuale=`). A sinistra tre passi numerati che diventano
✓: 1 Manuale (carica un PDF o scegli dalla libreria; «Cambia» per un altro file), 2 Macchina (dopo il
caricamento un modello leggero legge le prime pagine: gira solo il segno nell'intestazione, poi i
campi si compilano e restano modificabili; nessuna frase, un avviso solo se la lettura non riesce), 3 Chi risponde ai dubbi. A destra il **riepilogo**, fermo mentre si
scorre: manuale, pagine, dubbi, tempo e costo stimati, il motivo se non si può partire
(un'esecuzione già in corso, manuale o nome mancanti) e ▷ «Avvia estrazione». Niente budget o
totali di spesa nell'interfaccia: solo tempo e costo di ogni grafo (Fabio, 30 settembre 2026).

**Esecuzione (e replay).** Barra: Grafi › [macchina] › Esecuzione (o Replay); a destra tempo e
costo in mono, velocità e pausa del replay, «Ferma», «N domande per te», «Apri il grafo».
Pannello sinistro: le sei stazioni (spia, nome, fase a parole, dettaglio; avanzamento di
Estrai) e la legenda. Al centro il grafo che cresce. Nessuna colonna a destra: compare solo per
un nodo scelto. Barra di stato: contatori e ultima relazione trovata. Alla fine il riquadro
«Estrazione finita» con il prossimo passo, o «L'esecuzione si è fermata» con il motivo.

**Grafo finito.** Barra: Grafi › [macchina] › [versione]; a destra la ricerca di un sintomo o
un codice, il menu della versione, «Rispondi alle N domande» oppure ✓ «Approva». Pannello
sinistro: filtro delle relazioni, percorso scelto, legenda, versione, vista (Riordina,
Inquadra). Il pannello destro con le prove compare solo per un nodo o un arco scelto.

**Domande per te.** Barra: Grafi › [macchina] › Grafo › Domande per te; a destra «Domanda N di
M» e l'avanzamento. Colonna di lettura larga al massimo 800 px.

## 11. Controllo prima di mostrare una schermata

Screenshot a 1440 × 900 e a 1024 × 768, poi:

1. Si capisce in un colpo d'occhio che cosa fare dopo, e c'è un solo pulsante principale?
2. Ogni luogo ha un solo ingresso nella barra laterale, e le azioni stanno nella barra del percorso?
3. Il colore compare solo come stato (con la parola) o nel grafo e nella sua legenda?
4. Righe e controlli dello stesso livello hanno la stessa altezza, sulla griglia a 4 px?
5. I numeri sono in cifre tabulari e allineati a destra?
6. Attese, errori e vuoti hanno il loro segno, la loro frase e, se serve, «Riprova»?
7. Niente testo segnaposto o numeri inventati?
8. Tutto si usa da tastiera, con il focus visibile, e il testo secondario ha contrasto ≥ 4,5:1?
