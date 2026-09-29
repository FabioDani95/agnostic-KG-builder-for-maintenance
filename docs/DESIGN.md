# Design del prototipo frontend

Decisioni visive prese una volta sola. Ogni schermata usa **solo** questi valori; un valore
nuovo si aggiunge qui prima di usarlo. Il brief è [PROMPT_FRONTEND.md](PROMPT_FRONTEND.md),
sezione 4; in caso di conflitto prevale la sezione 4.

## 1. Principi

1. **Chiarezza.** Ogni schermata ha un titolo che dice che cosa è e un solo pulsante principale.
2. **Deferenza.** Il grafo e i dati comandano; l'interfaccia è neutra e si fa da parte.
3. **Profondità dagli strati.** Superfici piene una sopra l'altra; il vetro solo sopra il grafo.
4. **Ogni elemento ha una funzione.** Se toglierlo non fa perdere un dato o un'azione, si toglie.

Due famiglie di schermate:

| Famiglia | Schermate | Fondo |
| --- | --- | --- |
| Documento | Libreria, Manuale (versioni), Nuovo grafo, Domande per te | chiaro |
| Palco | Esecuzione dal vivo, Grafo finito | scuro: il grafo occupa tutto, pannelli di vetro sopra |

Regola: dove comanda il grafo il fondo è scuro, altrove chiaro. I colori dei nodi sono tarati
una volta sola per il fondo scuro.

## 2. Griglia e spaziature

- Unità: **8 px**. Ogni misura (margini, spazi, altezze, larghezze fisse) è un multiplo di 8.
  Fanno eccezione solo i bordi da 1 px e i contorni del focus da 2 px.
- Scala degli spazi: `8, 16, 24, 32, 48, 64`. Niente altri valori.
- Schermo minimo: **1280 × 800**. È un prototipo da scrivania, non si progetta per il telefono.

**Documento.** Contenitore centrato largo al massimo **1128 px**: 12 colonne da 72 px con 11
spazi da 24 px. Margini laterali di almeno 48 px, uguali a sinistra e a destra.

- Tutti i bordi sinistri cadono sull'inizio di una colonna. Titolo, tabella e pulsanti
  condividono la stessa linea sinistra (colonna 1) e la stessa linea destra (colonna 12).
- Spazio verticale: 48 px tra barra in alto e titolo, 32 px tra titolo e contenuto,
  24 px tra blocchi dello stesso livello.

**Palco.** Il grafo riempie la finestra. Sopra galleggiano, con 16 px di distacco dai bordi:

- barra in alto alta 64 px, a tutta larghezza;
- pannello sinistro largo **288 px**, pannello destro largo **360 px**, alti fino al fondo meno 16 px;
- i contatori del grafo in una riga alta 48 px, in basso al centro, allineata tra i due pannelli.

## 3. Tipografia

Font di sistema: `-apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Helvetica Neue", sans-serif`.
Due pesi: **400** (regular) e **600** (semibold). Maiuscole normali ovunque, niente `text-transform`,
niente spaziatura tra lettere aggiunta.

| Nome | Dimensione / interlinea | Peso | Uso |
| --- | --- | --- | --- |
| `title` | 34 / 40 | 600 | titolo della schermata, uno per schermata |
| `heading` | 22 / 32 | 600 | titolo di un pannello o di una sezione |
| `body-large` | 17 / 24 | 400 o 600 | domanda per te, affermazioni del sistema, nome del nodo selezionato |
| `body` | 15 / 24 | 400 o 600 | testo corrente, celle di tabella, pulsanti, campi |
| `small` | 13 / 16 | 400 o 600 | intestazioni di colonna, etichette dei campi, legenda, riferimenti di pagina |

- I numeri nelle tabelle, nei contatori e nei tempi usano `font-variant-numeric: tabular-nums`
  e sono allineati a destra.
- Il testo del manuale resta com'è, nella lingua originale. Si cita tra virgolette basse « » nelle
  frasi in italiano.
- Riga di testo lunga al massimo 72 caratteri circa (8 colonne) nei blocchi di lettura.

## 4. Colore

### Neutri (Documento)

| Token | Valore | Uso |
| --- | --- | --- |
| `--bg` | `#f5f5f7` | fondo della pagina |
| `--surface` | `#ffffff` | tabelle, pannelli, campi |
| `--text` | `#1d1d1f` | testo principale |
| `--text-2` | `#6e6e73` | testo secondario (4,7:1 su `--bg`, 5,1:1 su `--surface`) |
| `--line` | `#d2d2d7` | bordi da 1 px e righe separatrici delle tabelle |
| `--fill` | `#e8e8ed` | fondo dei controlli segmentati e dei pulsanti secondari |

### Neutri (Palco)

| Token | Valore | Uso |
| --- | --- | --- |
| `--stage` | `#000000` | fondo del grafo |
| `--glass` | `rgba(28, 28, 30, 0.72)` più `backdrop-filter: blur(24px) saturate(180%)` | pannelli e barre sopra il grafo |
| `--glass-solid` | `#1c1c1e` | stesso pannello con `prefers-reduced-transparency: reduce` |
| `--text-d` | `#f5f5f7` | testo principale |
| `--text-d2` | `#a1a1a6` | testo secondario (almeno 6:1 su `--glass-solid`) |
| `--line-d` | `rgba(255, 255, 255, 0.12)` | separatori |

### Accento

Un solo colore d'accento, **`#0071e3`**, per il pulsante principale, i link e il contorno del
focus. Il testo bianco sul pulsante ha contrasto 4,6:1. Lo stesso valore vale anche sul palco.
Link nel testo: `#0066cc` sul chiaro, `#2997ff` sul palco.

### Colore con significato (solo nel grafo)

Fuori dal grafo, e dalla sua legenda, non si usa nessun colore.

**Tipi di nodo.** Sei tipi, sei colori; il tipo si legge anche dalla legenda scritta e dalla
dimensione del pallino. Verde, giallo e rosso non si usano per i nodi, perché appartengono al semaforo.

| Tipo | Nome nella UI | Colore | Raggio relativo |
| --- | --- | --- | --- |
| Asset | Macchina | `#f5f5f7` | 3 |
| Symptom | Sintomo | `#ff9f0a` | 2 |
| ErrorCode | Codice di errore | `#ff6482` | 2 |
| FailureMode | Causa | `#bf5af2` | 1,5 |
| CorrectiveAction | Azione | `#64d2ff` | 1,5 |
| Component | Componente | `#8e8e93` | 1 |

Lungo il percorso sintomo, causa, azione i colori vicini differiscono anche per luminosità
(arancio medio-chiaro, viola scuro, azzurro chiaro).

**Archi, per stato di verifica.**

| Stato | Resa |
| --- | --- |
| proposto, non ancora controllato | linea sottile grigia `#636366`, opacità 0,5 |
| verificato (verde) | linea piena `#30d158` |
| in dubbio (giallo) | linea tratteggiata `#ffd60a` |
| scartato (rosso) | sparisce con una dissolvenza di 200 ms; resta solo nell'elenco degli esclusi |

## 5. Forme, bordi, ombre

- Raggi: **12 px** per i pannelli e le tabelle, **8 px** per i controlli (pulsanti, campi,
  controlli segmentati, riga del file). Nient'altro è arrotondato, a parte i nodi del grafo.
- Bordi: 1 px `--line` sul chiaro, `--line-d` sul palco, oppure nessun bordo. Mai bordi colorati,
  mai bordi più spessi su un solo lato.
- Ombre: nessuna sulle schermate Documento. Sul palco, una sola ombra neutra per i pannelli di
  vetro: `0 8px 32px rgba(0, 0, 0, 0.32)`.
- Niente gradienti, aloni, bagliori, sfondi con macchie di colore, forme decorative.

## 6. Movimento

- Durata **200 ms**, curva `cubic-bezier(0.25, 0.1, 0.25, 1)`, solo per spiegare un cambio di
  stato: apertura di un pannello, cambio della domanda, arco che diventa verificato.
- Nel grafo un nodo nuovo cresce da 0 alla sua dimensione in 240 ms. La simulazione fisica si
  ferma appena l'utente tocca o trascina la scena e non riparte finché non si preme «Riordina».
- Fuori dal grafo niente animazioni in loop: niente spinner. L'avanzamento si mostra con una
  barra determinata («unità 4 di 8») o con il testo «In corso».
- Con `prefers-reduced-motion: reduce`: niente crescita dei nodi, niente dissolvenze, cambi
  istantanei, grafo disposto una volta e fermo.

## 7. Icone

Un solo set lineare: sei tracciati copiati da [Lucide](https://lucide.dev) (licenza ISC) in un
solo file, tratto 1,5 px, riquadro 24 px, colore del testo. Solo dove sostituiscono una parola
nota:

| Icona | Uso |
| --- | --- |
| `x` | chiudi pannello |
| `search` | dentro il campo di ricerca |
| `chevron-left` | indietro, sempre accanto alla parola della pagina precedente |
| `pause` / `play` | pausa e ripresa del replay |
| `external-link` | apri la pagina del manuale |

Ogni pulsante con sola icona ha `aria-label`. Nessuna emoji, nessuna icona decorativa, nessuna
icona sopra un titolo.

## 8. Componenti

Altezza comune **48 px** per tutti gli elementi interattivi dello stesso livello: pulsanti,
campi, controlli segmentati, righe di tabella. In questo modo il bersaglio è sempre almeno 44 px.

| Componente | Specifica |
| --- | --- |
| **Barra in alto** | 64 px. A sinistra il nome dell'app («Grafi di manutenzione», `body` 600) o «‹ Pagina precedente»; a destra al massimo due controlli. Sul chiaro: `--surface` con bordo inferiore `--line`. Sul palco: vetro. |
| **Pulsante principale** | 48 px, padding orizzontale 24 px, raggio 8, fondo `#0071e3`, testo bianco `body` 600. Uno solo per schermata. |
| **Pulsante secondario** | come il principale, fondo `--fill`, testo `--text`. |
| **Pulsante semplice** | solo testo `#0066cc`, stessa altezza e padding, per azioni minori («Apri la pagina 20»). |
| **Campo** | 48 px, raggio 8, bordo 1 px `--line`, fondo `--surface`, testo `body`. Etichetta `small` 600 sopra, a 8 px, sempre visibile. |
| **Controllo segmentato** | 48 px, fondo `--fill`, raggio 8, segmenti uguali; il segmento scelto ha fondo `--surface` e testo 600. Per scelte esclusive: filtro della libreria, chi risponde ai dubbi, filtro per semaforo, velocità del replay. |
| **Tabella** | dentro un pannello `--surface` con raggio 12 e bordo 1 px. Intestazione alta 48 px, `small` 600 `--text-2`. Righe da 48 px separate da una linea 1 px `--line`. Padding orizzontale delle celle 16 px. Numeri a destra. Riga intera cliccabile, con fondo `--bg` al passaggio e contorno di focus. |
| **Pannello** | `--surface` (chiaro) o vetro (palco), raggio 12, padding 24. Titolo `heading`. Un pannello non contiene altri pannelli. |
| **Elenco** | righe da 48 px (una riga di testo) o da 72 px (due righe: `body` e `small`), separate da una linea. Niente schede. |
| **Barra di avanzamento** | alta 8 px, raggio 0, fondo `--fill` o `--line-d`, riempimento `--text` o `--text-d`. Testo del valore accanto, mai dentro. |
| **Focus** | contorno 2 px `#0071e3` con 2 px di distacco su ogni elemento interattivo (`:focus-visible`). |

Stati vuoti ed errori: una frase che dice che cosa succede e, se esiste, un pulsante per
rimediare. Esempi: «Nessun manuale corrisponde a “pompa”.», «Il file non è un PDF leggibile.
Scegline un altro.». Niente illustrazioni.

## 9. Schermate

Gli schemi mostrano solo la disposizione; i testi tra parentesi quadre sono dati veri, letti
dalle esecuzioni.

### 9.1 Libreria (Documento)

```text
┌ barra 64: Grafi di manutenzione ─────────────────────────── [Cerca…] ┐
│                                                                      │
│ Grafi                                              [Nuovo grafo]     │  title + pulsante principale
│                                                                      │
│ [Tutti | Da rivedere | Approvati]                                    │  controllo segmentato
│ ┌────────────────────────────────────────────────────────────────┐   │
│ │ Manuale  Macchina  Pagine  Versione  Relazioni verif.  Domande  Stato │
│ │ [LG LMH2235ST] [Forno a microonde] [49] [attuale r1] [291] [10] [Da approvare] │
│ └────────────────────────────────────────────────────────────────┘   │
```

Colonne sulla griglia a 12: Manuale 3, Macchina 3, Pagine 1, Versione 1, Relazioni verificate 2,
Domande aperte 1, Stato 1. La ricerca filtra per manuale, macchina, marca e modello. Clic sulla
riga: apre il Manuale.

### 9.2 Manuale (Documento)

Titolo = nome della macchina. Sotto, a sinistra (6 colonne), un elenco di dati con etichetta e
valore su due colonne (Marca, Modello, Tipo, Pagine, Origine: campagna o caricato). Sotto, la
tabella delle versioni in ordine di data: Data, Iterazione, Ripetizione, Codice (7 caratteri
del commit), Relazioni verificate, Domande aperte, Esito. Clic su una riga: apre il Grafo
finito di quella versione. Pulsante principale: «Rigioca l'esecuzione» (replay della versione
scelta).

### 9.3 Nuovo grafo (Documento)

Colonna centrale larga 8 colonne (744 px), allineata alla griglia.

1. Area di trascinamento: rettangolo alto 160 px, bordo 1 px `--line` continuo, testo
   «Trascina qui il manuale in PDF» e pulsante semplice «Scegli un file».
2. Riga del file (dopo il caricamento): nome del file, e a destra in colonne «Pagine [18]»,
   «Dimensione [2,1 MB]». Se il PDF è già nella libreria lo dice a parole.
3. Campi Macchina, Marca, Modello, Tipo su due colonne.
4. «Chi risponde ai dubbi»: controllo segmentato Solo agente / Agente, poi io / Solo io, con
   sotto una frase che spiega la scelta attiva.
5. Stima, in una tabella di due righe: «Tempo stimato [2–5 min]», «Costo stimato [0,02–0,12 USD]»,
   e sotto «Stima da [8] esecuzioni passate, non una promessa.»; poi «Speso finora [12,81] di
   [15,00] USD».
6. Pulsante principale «Avvia estrazione». Disattivato finché mancano il file o il nome della
   macchina, o se la stima massima supera il tetto rimasto; il motivo è scritto accanto.

### 9.4 Esecuzione dal vivo (Palco)

```text
┌ barra: ‹ Libreria   [LG LMH2235ST]   Tempo [03:12]  Costo [0,041 USD]  [Pausa]  [3 domande per te] ┐
│┌ Stazioni 288 ┐                                              ┌ Relazioni trovate 360 ┐│
││ Leggi   Fatta │                                              │ [Sintomo] → [Causa]   ││
││ Mappa   Fatta │                 grafo 3D                     │ Verificata            ││
││ Estrai  In corso                                             │ …                     ││
││ unità 4 di 8  │                                              │                       ││
││ ▬▬▬▬▬▬▬▬      │                                              │                       ││
│└───────────────┘   Nodi [120]  Relazioni [140]  Verificate [96]   Legenda             │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

- **Stazioni:** sei righe da 72 px (nome e stato a parole: In attesa, In corso, Fatta; sotto il
  dettaglio in `small`). La stazione in corso ha il nome in 600, non un colore.
- **Barra in alto:** «Replay ×4» scritto accanto al tempo quando è un replay. «[N] domande per te»
  è un pulsante secondario che apre Domande per te e compare solo se N > 0.
- **Relazioni trovate:** elenco da 72 px, più recenti in alto: «[nome sorgente] → [nome
  destinazione]» e sotto, in `small`, tipo di relazione in italiano, pagina e stato a parole
  (Proposta, Verificata, In dubbio, Scartata).
- **Contatori:** tre coppie etichetta e numero in una riga, `body`, non numeri giganti.
- **Legenda:** i sei tipi, ciascuno con un pallino da 8 px del suo colore e il nome. È l'unico
  posto fuori dal grafo dove compare un cerchio colorato, perché è la chiave del grafo.
- **Clic su un nodo:** il pannello destro mostra il nodo (nome, tipo, pagine, segmenti citati con
  il loro testo, «Apri la pagina [N]») con «‹ Relazioni trovate» per tornare all'elenco.

### 9.5 Domande per te (Documento)

Colonna centrale di 8 colonne. In alto «‹ Esecuzione» e a destra «Domanda [2] di [10]» con una
barra di avanzamento.

1. Titolo `title`: la domanda in italiano («Il manuale dice questo?»).
2. «Nel manuale»: elenco dei passi citati, ciascuno con la pagina in una colonna fissa di 96 px
   («p. 19») e il testo originale; «Apri la pagina 19» apre l'immagine della pagina con il
   segmento evidenziato da un rettangolo con bordo 2 px `#0071e3`.
3. «Il sistema propone»: affermazioni numerate, frasi italiane scritte per una persona (vedi il
   piano, sezione 7), con i nomi del manuale tra « ». Il numero è testo in una colonna di 32 px,
   non un cerchio.
4. Tre pulsanti a destra della stessa riga: «Sì, è giusto» (principale), «Solo in parte»
   (secondario: apre le caselle dei numeri da tenere), «No» (secondario).
5. «Dettagli»: sezione chiusa che mostra l'enunciato tecnico originale.

### 9.6 Grafo finito (Palco)

Come l'esecuzione dal vivo, con queste differenze:

- barra in alto: «‹ [Nome del manuale]», campo «Cerca un sintomo o un codice», menu «Versione»,
  pulsante principale «Approva» solo se la versione aspetta un'approvazione e non ha domande
  aperte; altrimenti, al suo posto, «Rispondi prima alle N domande»;
- pannello sinistro: filtro per semaforo (controllo segmentato Tutti / Verificati / In dubbio) e
  la legenda;
- scegliendo un sintomo o un codice, il percorso sintomo → causa → azione resta a piena
  opacità e il resto scende a 0,15;
- pannello destro: le prove dell'arco o del nodo scelto. Per ogni occorrenza: record, stato di
  verifica a parole, testimoni a parole («struttura della pagina», «accordo delle due letture»,
  «verificatore», «revisore»), chi ha deciso, i segmenti con pagina e testo, «Apri la pagina».

## 10. Controllo prima di mostrare una schermata

Prima di mostrare una schermata a Fabio: screenshot a 1440 × 900 e a 1280 × 800, poi controllo
voce per voce. Si mostra solo se tutte le risposte sono «no», tranne le ultime quattro, che
devono essere «sì».

1. C'è un punto, un trattino o un altro carattere usato come separatore nel testo?
2. C'è una scritta piccola sopra o sotto un titolo (occhiello, sottotitolo di contorno)?
3. C'è un pallino colorato di stato? (La legenda del grafo non conta.)
4. C'è un'etichetta tutta maiuscola, un badge sopra un titolo o una riga di numeri grandi?
5. C'è un gradiente, un alone, un bagliore, un'ombra colorata o uno sfondo con macchie?
6. C'è una scheda dentro una scheda, un bordo colorato su un lato, o una griglia di schede
   uguali dove basterebbe una tabella?
7. C'è un'emoji o un'icona decorativa, o icone di famiglie diverse?
8. C'è un testo segnaposto, un numero inventato o una frase di marketing?
9. C'è colore fuori dal grafo e dalla sua legenda, a parte l'accento sulle azioni?
10. C'è più di un pulsante principale?
11. C'è una misura fuori dalla griglia a 8 px, o un bordo sinistro che non cade su una colonna?
12. Le righe e i controlli dello stesso livello hanno tutti la stessa altezza?
13. I numeri sono allineati a destra con cifre tabulari?
14. Tutto si usa da tastiera, con il focus visibile?
15. Il testo secondario ha contrasto di almeno 4,5:1?

Le misure si verificano anche con uno script nel browser: si leggono gli stili calcolati e si
segnalano i valori di spazi, altezze e raggi fuori dalla scala.
