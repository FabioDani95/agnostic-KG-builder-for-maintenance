// The guide for the people who use the interface: what each part does and the logic behind it.
// Plain words, no code. A string is a paragraph; an array of strings is a bulleted list.
import type { IconName } from "../components/Icon";

export type Block = string | string[];

export interface GuideSection {
  id: string;
  heading: string;
  body: Block[];
}

export interface GuideChapter {
  slug: string;
  title: string;
  icon: IconName;
  lead: string;
  sections: GuideSection[];
}

export const GUIDE: GuideChapter[] = [
  {
    slug: "panoramica",
    title: "Panoramica",
    icon: "graph",
    lead:
      "L'applicazione legge il manuale di una macchina e ne ricava un grafo di manutenzione: una mappa che collega i sintomi e i codici di errore alle loro cause, e le cause alle azioni che le risolvono. Ogni collegamento porta con sé la pagina e le parole del manuale da cui viene.",
    sections: [
      {
        id: "a-cosa-serve",
        heading: "A cosa serve",
        body: [
          "Davanti a un guasto, chi fa manutenzione parte da quello che vede: un sintomo o un codice sul display. Il grafo permette di partire da lì e arrivare alle cause possibili e agli interventi, senza sfogliare il manuale.",
          "Il grafo è pensato per essere controllato: ogni collegamento dice se è stato verificato, da chi, e mostra il testo del manuale che lo giustifica.",
        ],
      },
      {
        id: "cosa-contiene",
        heading: "Cosa contiene un grafo",
        body: [
          "Sei tipi di elementi, sempre gli stessi per ogni manuale:",
          [
            "Macchina: la macchina di cui parla il manuale, una per grafo.",
            "Sintomo: quello che si osserva (per esempio «la pompa non parte»).",
            "Codice di errore: un allarme o un codice mostrato dalla macchina.",
            "Causa: il motivo tecnico che può spiegare un sintomo o un codice.",
            "Azione: l'intervento che risolve la causa, oppure un controllo da fare o la richiesta di assistenza quando il manuale non indica altro.",
            "Componente: la parte della macchina coinvolta.",
          ],
          "Lo schema completo, con tutti i collegamenti ammessi, è nella sezione Ontologia.",
        ],
      },
      {
        id: "percorso",
        heading: "Il percorso in breve",
        body: [
          [
            "Carichi il manuale in PDF e controlli i dati della macchina.",
            "L'estrazione legge il manuale e costruisce il grafo; puoi seguirla dal vivo.",
            "Se restano dubbi, alcuni arrivano a te come domande semplici.",
            "Controlli il grafo e lo approvi.",
            "Da quel momento il grafo è pronto per essere consultato.",
          ],
        ],
      },
      {
        id: "dove-trovare",
        heading: "Dove trovare le cose",
        body: [
          "La barra scura a sinistra porta ai luoghi dell'applicazione; la barra in alto dice dove sei e contiene le azioni della pagina.",
          [
            "Il logo riporta all'elenco di tutti i grafi.",
            "Tocca a te raccoglie quello che aspetta una tua risposta o approvazione; il numero arancio dice quanti grafi sono fermi per te.",
            "Esecuzioni elenca tutte le estrazioni fatte, con tempi e costi.",
            "Ontologia mostra lo schema che ogni grafo segue.",
            "Quando un'estrazione è in corso compare una spia blu: porta dritto al grafo che cresce.",
            "In basso: questa guida e le impostazioni.",
          ],
          "Passando con il mouse su un'icona ne vedi il nome.",
        ],
      },
    ],
  },
  {
    slug: "nuovo-grafo",
    title: "Creare un grafo",
    icon: "plus",
    lead:
      "Un grafo nasce in tre passi: scegli il manuale, controlli i dati della macchina, decidi chi risponde ai dubbi. Il riepilogo a destra mostra tempo e costo previsti prima di partire.",
    sections: [
      {
        id: "manuale",
        heading: "1. Il manuale",
        body: [
          "Puoi trascinare un PDF nell'area apposita o sceglierlo dal computer. Se quel PDF è già nella libreria l'applicazione lo riconosce: la nuova estrazione diventa una nuova versione del grafo che esiste già.",
          "In alternativa scegli «Dalla libreria» per rifare l'estrazione di un manuale già caricato. Dalla pagina di un manuale lo stesso si ottiene con «Nuova versione».",
        ],
      },
      {
        id: "macchina",
        heading: "2. La macchina",
        body: [
          "Appena caricato il PDF, un modello leggero legge le prime pagine e compila da solo macchina, marca, modello e tipo. Mentre legge vedi solo un segno che gira; poi i campi si riempiono e restano modificabili.",
          "Legge una pagina alla volta finché ha abbastanza testo, al massimo cinque; se il PDF è una scansione senza testo guarda l'immagine della copertina. Scrive solo quello che trova: se un dato non c'è, il campo resta vuoto.",
          "Controlla sempre i campi prima di partire. È obbligatorio solo il nome della macchina.",
        ],
      },
      {
        id: "dubbi",
        heading: "3. Chi risponde ai dubbi",
        body: [
          "Durante l'estrazione alcuni collegamenti restano incerti. Puoi decidere chi li controlla:",
          [
            "Solo agente: un modello risponde a tutti i dubbi. A te resta solo l'approvazione finale.",
            "Agente, poi io: l'agente risponde ai dubbi che sa risolvere; quelli su cui non è sicuro arrivano a te.",
            "Solo io: i dubbi arrivano a te.",
          ],
          "In ogni caso a una persona arriva al massimo un certo numero di domande, di solito 10 (si cambia nelle impostazioni). Le più importanti vengono prima; le altre restano nel grafo come «non verificate».",
        ],
      },
      {
        id: "stima",
        heading: "Tempo e costo stimati",
        body: [
          "La stima viene dalle due estrazioni passate con il numero di pagine più vicino a quello del tuo manuale: per questo è un intervallo, per esempio «2–3 min». Quando i due valori coincidono vedi un valore solo, per esempio «~5 min».",
          "È un'indicazione, non una garanzia: un manuale con molte tabelle di diagnosi richiede più lavoro di uno con poche.",
        ],
      },
      {
        id: "avvio",
        heading: "L'avvio",
        body: [
          "«Avvia estrazione» si attiva quando c'è un manuale e il nome della macchina. Se non si può partire, sotto il pulsante c'è il motivo. Si può avere una sola estrazione in corso alla volta.",
          "Ogni estrazione ha un tetto di spesa: se la stima non ci sta, l'avvio viene rifiutato con un messaggio.",
        ],
      },
    ],
  },
  {
    slug: "estrazione",
    title: "Come lavora l'estrazione",
    icon: "activity",
    lead:
      "L'estrazione passa per sei stazioni, sempre nello stesso ordine. Nella schermata dell'esecuzione le vedi a sinistra, con una spia per ciascuna: grigia in attesa, blu in corso, verde fatta.",
    sections: [
      {
        id: "leggi",
        heading: "Leggi",
        body: [
          "Il PDF viene scomposto in pezzi piccoli: blocchi di testo e righe delle tabelle, ognuno con il suo posto preciso nella pagina. Le pagine senza testo passano dal riconoscimento dei caratteri. Qui non lavora nessun modello.",
          "Da questo momento ogni informazione del grafo potrà indicare esattamente da quale riga del manuale viene.",
        ],
      },
      {
        id: "mappa",
        heading: "Mappa",
        body: [
          "Un modello guarda ogni pagina e la classifica: diagnostica, procedura, ricambi, altro. Si leggono a fondo solo le pagine utili per la diagnosi, più quelle subito vicine per non perdere nulla; nel dubbio una pagina viene inclusa.",
          "Le pagine da leggere vengono raggruppate in unità di lettura, cercando di non spezzare le tabelle. Un agente conferma la mappa prima di proseguire.",
        ],
      },
      {
        id: "estrai",
        heading: "Estrai",
        body: [
          "Ogni unità viene letta da un modello che trova sintomi, codici, cause, azioni e componenti e li collega tra loro, indicando dove li ha letti. Ogni unità viene letta due volte, in modo indipendente: le due letture insieme perdono meno cose, e quando concordano danno fiducia.",
          "Un dettaglio sbagliato non fa buttare via niente: si annota e si va avanti. Se una riga di una tabella diagnostica non viene usata da nessuna lettura, viene riletta apposta.",
        ],
      },
      {
        id: "controlla",
        heading: "Controlla",
        body: [
          "Ogni collegamento cerca dei «testimoni» indipendenti:",
          [
            "struttura della pagina: i due elementi sono scritti nella stessa riga o nello stesso blocco;",
            "accordo delle due letture: entrambe lo hanno trovato;",
            "verificatore: se mancano gli altri due, un modello rilegge solo il testo citato e dice se esprime davvero quel collegamento.",
          ],
          "Con due testimoni il collegamento è verificato (verde). Con uno solo, o con testimoni in disaccordo, è in dubbio (giallo) e diventa una domanda. Senza testimoni è scartato: resta fuori dal grafo, ma elencato nel rapporto.",
        ],
      },
      {
        id: "unisci",
        heading: "Unisci",
        body: [
          "Lo stesso sintomo o la stessa causa possono comparire in più punti del manuale con parole un po' diverse. Qui diventano un elemento solo. Le somiglianze incerte le giudica un modello; elementi con codici o numeri diversi non si uniscono mai. I nomi alternativi restano registrati.",
          "In questa fase si aggiungono anche i collegamenti tra la macchina e i suoi componenti e codici: non vengono dal testo, li aggiunge il sistema.",
        ],
      },
      {
        id: "chiedi",
        heading: "Chiedi",
        body: [
          "I collegamenti in dubbio che vengono dallo stesso punto del manuale diventano una domanda sola. Risponde prima l'agente, se previsto; quello che resta arriva a te, fino al massimo stabilito.",
          "Alla fine dell'esecuzione compare un riquadro che dice com'è andata e qual è il prossimo passo.",
        ],
      },
      {
        id: "fermare",
        heading: "Fermare un'esecuzione",
        body: [
          "«Ferma» interrompe l'estrazione in corso. Il lavoro fatto fino a quel momento resta salvato.",
          "Puoi anche lasciare la schermata: l'estrazione continua e la spia blu nella barra a sinistra ti riporta lì.",
        ],
      },
    ],
  },
  {
    slug: "domande",
    title: "Domande e approvazione",
    icon: "question",
    lead:
      "Le domande servono a sciogliere i dubbi che il sistema non sa risolvere da solo. Sono poche e chiare: mostrano il testo del manuale e quello che il sistema propone, e si risponde senza cercare altrove.",
    sections: [
      {
        id: "tocca-a-te",
        heading: "Tocca a te",
        body: [
          "La sezione Tocca a te raccoglie tre gruppi:",
          [
            "Aspettano te: grafi fermi finché non rispondi o approvi. Per ciascuno c'è il prossimo passo, per esempio «Rispondi alle 10 domande».",
            "In corso: l'estrazione che sta lavorando.",
            "Dubbi nei grafi approvati: domande rimaste senza risposta in grafi già approvati. Non bloccano nulla.",
          ],
        ],
      },
      {
        id: "rispondere",
        heading: "Come si risponde",
        body: [
          "Ogni domanda mostra le righe del manuale coinvolte, con la pagina, e una o più affermazioni del sistema. Con «Apri la pagina» vedi la pagina originale.",
          [
            "«Sì, è giusto» conferma tutto.",
            "«Solo in parte» ti fa scegliere quali affermazioni tenere.",
            "«No» scarta la proposta.",
            "Per alcune domande puoi scrivere tu il testo, per esempio quando una pagina non si legge.",
          ],
          "«Dettagli» mostra la proposta nella forma tecnica, se vuoi controllarla fino in fondo.",
        ],
      },
      {
        id: "applicare",
        heading: "Applicare le risposte",
        body: [
          "Quando hai risposto a tutte le domande, «Applica le risposte» fa ripartire l'esecuzione dal punto in cui si era fermata: le tue risposte vengono inserite nel grafo senza rifare l'estrazione.",
          "Una tua conferma o un tuo rifiuto valgono più dei controlli automatici.",
        ],
      },
      {
        id: "approvare",
        heading: "Approvare il grafo",
        body: [
          "L'ultimo passo è l'approvazione: controlli il grafo e scegli «Approva» o «Rifiuta». Nell'applicazione l'approvazione è sempre di una persona.",
          "I grafi della campagna di valutazione sono stati approvati in automatico e lo indicano con «Approvato dal sistema». Se rispondi a una domanda di uno di questi grafi, la prima risposta ne crea una copia su cui continui a lavorare: l'originale non cambia.",
        ],
      },
      {
        id: "passi",
        heading: "A che punto è un grafo",
        body: [
          "Nella pagina di un manuale la versione attuale mostra tre passi: estrazione, domande, approvazione. Una spia verde con la spunta indica un passo fatto, arancio un passo che aspetta te, rossa un passo non riuscito.",
          "Sotto i passi c'è sempre un solo pulsante principale: il prossimo passo da fare.",
        ],
      },
    ],
  },
  {
    slug: "grafo",
    title: "Leggere il grafo",
    icon: "search",
    lead:
      "Il grafo occupa il centro dello schermo. A sinistra ci sono filtri, legenda e dati della versione; a destra, quando scegli qualcosa, le prove che lo giustificano.",
    sections: [
      {
        id: "muoversi",
        heading: "Muoversi nel grafo",
        body: [
          [
            "Trascina per ruotare, usa la rotella per avvicinarti o allontanarti.",
            "Al primo tocco il grafo si ferma dov'è, così puoi esplorarlo con calma. «Riordina» lo fa muovere di nuovo; «Inquadra» lo riporta tutto nello schermo.",
            "Passando sopra un nodo ne vedi il nome; nelle impostazioni puoi tenere i nomi sempre visibili.",
          ],
        ],
      },
      {
        id: "colori",
        heading: "Colori e linee",
        body: [
          "Ogni tipo di elemento ha il suo colore, indicato nella legenda con il numero di elementi. I collegamenti dicono il loro stato con il colore:",
          [
            "verde: verificato;",
            "giallo tratteggiato: in dubbio;",
            "grigio: proposto, non ancora controllato;",
            "grigio tenue: aggiunto dal sistema per legare la macchina ai suoi componenti e codici.",
          ],
          "I collegamenti scartati non compaiono. Con il filtro in alto a sinistra vedi tutti i collegamenti, solo i verificati o solo quelli in dubbio.",
        ],
      },
      {
        id: "cercare",
        heading: "Cercare un sintomo o un codice",
        body: [
          "Scrivi nel campo di ricerca in alto (il tasto «/» ci porta subito il cursore) e scegli un risultato. Il grafo mette in evidenza il percorso di diagnosi: dal sintomo o codice alle cause, dalle cause alle azioni e ai componenti. Il resto si attenua. «Mostra tutto il grafo» torna alla vista completa.",
        ],
      },
      {
        id: "prove",
        heading: "Le prove",
        body: [
          "Scegliendo un nodo o un collegamento, a destra compaiono le prove: le righe del manuale con la pagina, lo stato, i testimoni che lo sostengono e, se qualcuno ha deciso, chi. «Apri la pagina» mostra la pagina originale con il testo citato evidenziato, quando la sua posizione è nota.",
          "Il pannello si chiude con la croce o con il tasto Esc.",
        ],
      },
      {
        id: "dal-vivo",
        heading: "Il grafo che cresce",
        body: [
          "Durante un'estrazione il grafo si costruisce sotto i tuoi occhi: i nodi nuovi compaiono man mano e i collegamenti cambiano colore quando vengono controllati. In basso vedi i contatori e l'ultima relazione trovata.",
          "Le estrazioni passate si possono rigiocare con «Rigioca l'esecuzione», a velocità 1×, 4× o 16×, con pausa. Rigiocare non costa nulla: non chiama nessun modello.",
        ],
      },
    ],
  },
  {
    slug: "esecuzioni",
    title: "Esecuzioni, tempi e costi",
    icon: "activity",
    lead:
      "Ogni estrazione è un'esecuzione, e ogni esecuzione produce una versione del grafo. Tempi e costi di ciascuna sono sempre visibili.",
    sections: [
      {
        id: "versioni",
        heading: "Versioni",
        body: [
          "Un manuale può avere più versioni del suo grafo: estrazioni ripetute, fatte con impostazioni diverse, o copie nate dalle risposte alle domande. La pagina del manuale le elenca tutte; quella più recente è la versione attuale.",
          "Con il menu della versione, nella schermata del grafo, passi da una versione all'altra.",
        ],
      },
      {
        id: "registro",
        heading: "La pagina Esecuzioni",
        body: [
          "Elenca tutte le esecuzioni di tutti i manuali, dalla più recente, con esito, durata e costo. Puoi vedere solo quelle avviate dall'interfaccia o solo quelle della campagna di valutazione, e ordinare per colonna. Una riga porta al passo giusto: il grafo, le domande o l'esecuzione in corso.",
        ],
      },
      {
        id: "costi",
        heading: "Come si forma il costo",
        body: [
          "Il costo è quello dei modelli usati: la mappa, le due letture di ogni unità, il verificatore, l'agente sui dubbi. Ogni chiamata viene registrata con il suo costo, e ogni estrazione ha un tetto che non può superare.",
          "Leggere i dati della macchina dopo il caricamento costa una frazione di centesimo. Rigiocare un'esecuzione non costa nulla, e di norma nemmeno applicare le risposte: il lavoro già fatto non si ripete.",
        ],
      },
    ],
  },
  {
    slug: "ontologia",
    title: "L'ontologia",
    icon: "schema",
    lead:
      "L'ontologia è lo schema fisso che ogni grafo segue: quali tipi di elementi esistono e quali collegamenti sono ammessi tra loro. È la stessa per tutti i manuali, così i grafi si possono confrontare e usare allo stesso modo.",
    sections: [
      {
        id: "schema",
        heading: "Lo schema",
        body: [
          "La pagina Ontologia disegna lo schema con gli stessi colori del grafo, quindi fa anche da legenda. Il percorso principale va da sinistra a destra: sintomo o codice, poi causa, poi azione e componente.",
        ],
      },
      {
        id: "chi-crea",
        heading: "Chi crea i collegamenti",
        body: [
          "La linea continua indica i collegamenti estratti dal modello, ognuno con le sue prove nel manuale. La linea tratteggiata indica quelli aggiunti dal sistema: legano la macchina ai suoi componenti e ai suoi codici.",
          "Sotto lo schema trovi la descrizione di ogni tipo e di ogni collegamento, così come sono scritte nello schema.",
        ],
      },
    ],
  },
  {
    slug: "impostazioni",
    title: "Impostazioni",
    icon: "settings",
    lead:
      "La rotella in basso a sinistra apre le impostazioni. Valgono per le nuove estrazioni avviate da qui; un'estrazione già partita, anche quando riprende dopo le tue risposte, tiene quelle con cui era partita.",
    sections: [
      {
        id: "chiave",
        heading: "Chiave OpenAI",
        body: [
          "Di solito si usa la chiave già configurata sul computer. Se ne scrivi un'altra, verrà usata per le nuove estrazioni e per la lettura dei dati della macchina. La chiave resta su questo computer e non viene mai mostrata: vedi solo le ultime quattro cifre. «Usa .env» torna a quella di sempre.",
        ],
      },
      {
        id: "estrazione",
        heading: "Estrazione",
        body: [
          [
            "Ragionamento: quanto il modello riflette prima di rispondere. Più ragionamento può trovare collegamenti più sottili, ma richiede più tempo e costa di più.",
            "Letture per unità: quante volte ogni parte del manuale viene letta. Due è il valore consigliato, perché l'accordo tra due letture fa da testimone. Una costa meno ma controlla meno; tre è più prudente.",
          ],
        ],
      },
      {
        id: "agente",
        heading: "Agente",
        body: [
          "Il modello e il ragionamento dell'agente che risponde ai dubbi al posto tuo, secondo la scelta fatta in «Chi risponde ai dubbi».",
        ],
      },
      {
        id: "domande",
        heading: "Domande",
        body: [
          "Il numero massimo di domande che arrivano a una persona in un'estrazione. Le domande più importanti vengono prima; oltre il massimo i dubbi restano nel grafo come non verificati.",
        ],
      },
      {
        id: "grafo",
        heading: "Grafo",
        body: [
          [
            "Relazioni aggiunte dal codice: mostra o nasconde i collegamenti tra la macchina e i suoi componenti e codici.",
            "Nomi sempre visibili sui nodi: scrive il nome accanto a ogni nodo invece di mostrarlo solo al passaggio del mouse.",
          ],
          "Queste due scelte valgono subito, in tutti i grafi.",
        ],
      },
    ],
  },
];
