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
      "L'applicazione legge il manuale di una macchina e ne ricava un grafo di manutenzione: una mappa che collega sintomi e codici di errore a cause possibili, controlli e interventi. I collegamenti estratti conservano le pagine e le parole del manuale su cui si basano, così puoi capire il percorso e controllarne le prove.",
    sections: [
      {
        id: "a-cosa-serve",
        heading: "A cosa serve",
        body: [
          "Davanti a un guasto, chi fa manutenzione parte da quello che vede: un sintomo o un codice sul display. Il grafo permette di partire da lì e arrivare alle cause possibili e agli interventi, senza sfogliare il manuale.",
          "Il grafo è pensato per essere controllato: per ogni relazione estratta puoi vedere lo stato della verifica, le prove nel manuale e l'eventuale decisione di un agente o di una persona. Una relazione è il collegamento tra due elementi; gli elementi sono chiamati anche nodi.",
          "Per esempio, se un manuale associa «la pompa non parte» a «alimentazione assente» e prescrive «controllare l'alimentazione», il grafo può rappresentare quel percorso in tre nodi. Se il manuale elenca più cause, vedrai più rami: dovrai valutare quale corrisponde alla situazione osservata.",
          "La consultazione parte dalla macchina e dalla versione del manuale corrette. Il grafo organizza quello che è stato estratto: l'assenza di un sintomo nei risultati non dimostra che quel guasto sia impossibile o che il manuale non ne parli. Aprire le pagine citate aiuta anche a leggere il contesto e le condizioni dell'intervento.",
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
          "Sintomo e causa hanno ruoli diversi: «la pompa non parte» descrive ciò che osservi; «alimentazione assente» propone una spiegazione. Allo stesso modo, «controllare il cavo» è un controllo, mentre «sostituire il cavo» è un intervento: la presenza di un'azione nel percorso non significa sempre che si sia già trovata la soluzione.",
          "Alcuni manuali indicano un controllo o un rimedio senza dare un nome alla causa. In questi casi il sistema può assegnare un nome per rappresentare il ramo; nel pannello del nodo trovi l'indicazione «Causa non scritta nel manuale». Leggi le prove per distinguere ciò che la fonte dice dalla formulazione usata per organizzarlo.",
          "Uno stesso nodo può avere più nomi e comparire in più pagine. Una relazione può avere più occorrenze, cioè più passaggi del manuale in cui viene descritta: ciascuno conserva le proprie prove e condizioni.",
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
          "Se stai imparando, puoi cominciare da un grafo già presente nella libreria: aprilo, cerca un sintomo, scegli una relazione e confrontala con la pagina originale. Il replay di un'esecuzione permette poi di osservare le fasi della costruzione senza avviare un'altra estrazione.",
          "Tieni separate due verifiche: l'approvazione riguarda la versione nel suo insieme, mentre il verde o il giallo riguarda una singola relazione. Un grafo approvato può conservare dubbi; potrai riconoscerli e filtrarli anche dopo l'approvazione.",
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
            "In basso: la lingua (IT o EN, cambia tutta l'interfaccia), questa guida e le impostazioni.",
          ],
          "Passando con il mouse su un'icona ne vedi il nome.",
          "Nella libreria puoi cercare per nome, marca, modello o tipo di macchina e scegliere «Tutti», «Da rivedere» o «Approvati». «Da rivedere» comprende anche grafi che hanno ancora domande aperte. Aprendo la riga di un manuale trovi il PDF, la versione attuale e la cronologia delle versioni; l'icona di azione sulla riga porta direttamente al grafo o all'esecuzione.",
          "La Guida si può leggere in ordine con i collegamenti al capitolo precedente e successivo. L'indice a sinistra cambia capitolo; «In questa pagina», quando visibile, porta ai singoli paragrafi. Puoi tornare a una schermata dell'applicazione dalla barra laterale in qualunque momento.",
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
          "Scegli il documento relativo al modello e alla revisione che vuoi consultare, con le sezioni di diagnosi leggibili. Un PDF con testo selezionabile facilita la lettura; una scansione dipende anche dalla qualità delle immagini e dalla disponibilità del riconoscimento dei caratteri. Il fatto che il caricamento riesca non garantisce che tutte le pagine siano leggibili.",
          "Dopo il caricamento controlla nome del file e numero di pagine. Con «Cambia» puoi scegliere un altro PDF prima dell'avvio. Se il file è danneggiato o non è un PDF, l'applicazione mostra il problema e ti permette di sceglierne un altro.",
          "Il riconoscimento di un manuale già presente si basa sul contenuto del file, non sul suo nome. Una nuova estrazione dello stesso PDF conserva le versioni precedenti; un PDF diverso, anche se parla della stessa macchina, viene trattato come un altro manuale.",
        ],
      },
      {
        id: "macchina",
        heading: "2. La macchina",
        body: [
          "Appena caricato il PDF, un modello leggero legge le prime pagine e compila da solo marca, modello e tipo di macchina (per esempio «aspiratore»). Mentre legge vedi solo un segno che gira; poi i campi si riempiono e restano modificabili. Il nome del manuale nella libreria si compone da questi tre.",
          "Legge una pagina alla volta finché ha abbastanza testo, al massimo cinque; se il PDF è una scansione senza testo guarda l'immagine della copertina. Scrive solo quello che trova: se un dato non c'è, il campo resta vuoto.",
          "Controlla sempre i campi prima di partire. Serve almeno la marca o il modello.",
          "Per un manuale nuovo puoi correggere i dati dopo la lettura automatica: usa la marca e la sigla come sono scritte sul documento e un tipo breve, per esempio «compressore». Questi campi aiutano a riconoscere il manuale nella libreria; la lettura delle prime pagine serve a identificarlo, mentre l'estrazione delle informazioni di diagnosi avviene dopo l'avvio.",
          "Se l'identificazione automatica fallisce, i campi possono essere compilati a mano. Se invece scegli un manuale dalla libreria, o carichi un PDF riconosciuto come duplicato, vengono riutilizzati i dati già registrati e i campi sono bloccati.",
        ],
      },
      {
        id: "dubbi",
        heading: "3. Chi risponde ai dubbi",
        body: [
          "Durante l'estrazione alcuni collegamenti restano incerti. Puoi decidere chi li controlla:",
          [
            "Solo agente: un modello esamina i dubbi senza passarli normalmente a te; quelli che non risolve possono restare aperti. L'approvazione finale resta tua.",
            "Agente, poi io: l'agente risponde ai dubbi che sa risolvere; quelli su cui non è sicuro arrivano a te.",
            "Solo io: i dubbi arrivano a te.",
          ],
          "In ogni caso a una persona arriva al massimo un certo numero di domande, di solito 10 (si cambia nelle impostazioni). Le più importanti vengono prima; le altre restano nel grafo come «non verificate».",
          "«Agente, poi io» è la scelta iniziale dell'interfaccia. «Solo io» ti permette di controllare direttamente i dubbi di estrazione; «Solo agente» affida quella revisione al modello. La scelta riguarda i dubbi, mentre la mappa delle pagine viene comunque sottoposta all'agente e l'approvazione di un nuovo grafo avviato da qui richiede una persona.",
          "Una domanda può raccogliere più affermazioni dello stesso passaggio, quindi il limite delle domande non corrisponde al numero di relazioni controllate. Ridurre il limite riduce il lavoro richiesto a te, ma può lasciare più relazioni in dubbio.",
        ],
      },
      {
        id: "stima",
        heading: "Tempo e costo stimati",
        body: [
          "La stima usa le esecuzioni di riferimento della campagna per i due manuali con il numero di pagine più vicino al tuo. Mostra l'intervallo tra i loro tempi e costi, per esempio «2–3 min». Se c'è un solo riferimento, o i valori coincidono, vedi un valore approssimativo solo, per esempio «~5 min».",
          "È un'indicazione, non una garanzia: un manuale con molte tabelle di diagnosi richiede più lavoro di uno con poche.",
          "Il riepilogo indica i costi in USD. La stima non viene ricalcolata in dettaglio per il modello, il ragionamento o le letture che scegli: cambiando le impostazioni, tempo e costo reali possono discostarsi dai riferimenti. Durante l'esecuzione puoi seguire i valori aggiornati.",
          "Se non ci sono esecuzioni di riferimento adatte, compare un trattino e l'avvio viene bloccato perché il sistema non può stimare il costo. Caricare di nuovo lo stesso file non aggiunge i riferimenti mancanti.",
        ],
      },
      {
        id: "avvio",
        heading: "L'avvio",
        body: [
          "«Avvia estrazione» si attiva quando il manuale è stato scelto, c'è almeno la marca o il modello e non ci sono operazioni o esecuzioni che impediscono di partire. Il riepilogo mostra il motivo di un eventuale blocco vicino al pulsante. Si può avere una sola estrazione in corso alla volta.",
          "Prima di premere il pulsante, ricontrolla il manuale, i dati della macchina, chi risponderà ai dubbi e le impostazioni di estrazione. L'avvio crea una nuova versione e apre la schermata in cui seguirne la costruzione.",
          "Il sistema confronta la stima massima con la spesa ancora disponibile, anche per le attività avviate dall'interfaccia. Se non rientra nei limiti, l'avvio viene rifiutato con un messaggio; quei limiti non si modificano nella finestra Impostazioni.",
          "Se c'è già un'esecuzione in corso, «Seguila» ti porta alla relativa schermata. Attendi che finisca prima di avviarne un'altra. Un messaggio di errore durante l'avvio non indica che il grafo sia stato completato: controlla la pagina del manuale per vedere se una versione è stata creata.",
        ],
      },
    ],
  },
  {
    slug: "estrazione",
    title: "Come lavora l'estrazione",
    icon: "activity",
    lead:
      "La costruzione segue sei stazioni principali: Leggi, Mappa, Estrai, Controlla, Unisci e Chiedi. Alcune correzioni richiedono ulteriori controlli. Nella schermata dell'esecuzione trovi le stazioni a sinistra: grigia in attesa, blu in corso, verde fatta. Il verde di una stazione indica che la fase è terminata, non che ogni relazione sia verificata.",
    sections: [
      {
        id: "leggi",
        heading: "Leggi",
        body: [
          "Il PDF viene scomposto in pezzi piccoli: blocchi di testo e righe delle tabelle, ciascuno collegato alla sua pagina e, quando disponibile, alla posizione del testo. Se una pagina ha poco testo o testo corrotto, il sistema tenta il riconoscimento dei caratteri quando è disponibile e nei limiti configurati. In questa fase non si usa un modello linguistico.",
          "Ogni pezzo riceve un riferimento che le fasi successive possono citare. Questo permette di tornare alla fonte senza chiedere al modello di ricopiare a memoria il passaggio.",
          "Nelle tabelle il sistema cerca di mantenere insieme problema, causa e rimedio, con le intestazioni delle colonne. Una scansione sfocata o una tabella complessa può comunque perdere testo o struttura: se un passaggio sembra incompleto, confrontalo con la pagina originale.",
        ],
      },
      {
        id: "mappa",
        heading: "Mappa",
        body: [
          "Due letture indipendenti classificano le pagine come diagnostica, procedura, ricambi o altro, usando una sintesi del contenuto. Una pagina indicata come diagnostica da almeno una lettura viene inclusa. Si aggiungono anche alcune continuazioni: per esempio una procedura vicina a una pagina diagnostica o una pagina compresa tra due pagine diagnostiche.",
          "Le pagine da leggere vengono raggruppate in unità di lettura, cercando di non spezzare le tabelle. Un agente conferma la mappa prima di proseguire.",
          "Una unità di lettura è una porzione del manuale affidata al modello insieme al contesto utile. Non corrisponde necessariamente a una pagina intera: un documento breve con molte tabelle può richiedere diverse unità.",
          "La mappa serve a concentrarsi sulla diagnosi, invece di trasformare ogni pagina in un nodo. La selezione non garantisce che ogni informazione utile sia stata trovata; le pagine prive di testo leggibile vengono segnalate separatamente.",
        ],
      },
      {
        id: "estrai",
        heading: "Estrai",
        body: [
          "Il modello legge ogni unità e propone sintomi, codici, cause, azioni e componenti, con i collegamenti e i riferimenti al testo. Per impostazione iniziale ogni unità viene letta due volte, in modo indipendente; nelle impostazioni puoi scegliere da una a tre letture. Le proposte vengono raccolte insieme e il loro accordo può contribuire alla verifica.",
          "Il sistema controlla che le citazioni esistano e che i collegamenti rispettino l'ontologia. Le proposte con errori vengono segnalate; quelle valide possono proseguire. Per alcune righe diagnostiche che non sono state usate è previsto un tentativo aggiuntivo di lettura, entro i limiti della procedura.",
          "Il grafo che vedi crescere in questa fase contiene ancora proposte. Un nodo appena comparso o una linea grigia non sono un risultato già confermato: devono passare dai controlli successivi.",
          "Quando il manuale distingue condizioni, prerequisiti, avvertenze o risultati di un test, il sistema cerca di conservarli insieme al collegamento. Sono parte del significato del ramo, non informazioni da ignorare quando si sceglie un intervento.",
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
            "verificatore: quando struttura e accordo non bastano, un modello rilegge il passaggio con le citazioni e il contesto disponibile e valuta se sostiene davvero il collegamento.",
          ],
          "Con due testimoni il collegamento è verificato (verde). Con uno solo, o con testimoni in disaccordo, è in dubbio (giallo) e diventa una domanda. Senza testimoni è scartato: resta fuori dal grafo, ma elencato nel rapporto.",
          "«Verificato» descrive il sostegno trovato nel documento per quella relazione. Non è una percentuale di certezza né la conferma che quella causa spieghi il guasto della macchina che hai davanti. L'accordo di due letture è un controllo utile, ma anche letture concordi possono sbagliare.",
          "Nel pannello delle prove puoi vedere quali testimoni hanno contribuito. Una successiva decisione di revisione può confermare o respingere la relazione; per questo leggere la decisione e il passaggio citato è più informativo del solo colore.",
        ],
      },
      {
        id: "unisci",
        heading: "Unisci",
        body: [
          "Lo stesso sintomo o la stessa causa possono comparire in più punti del manuale con parole un po' diverse. Qui diventano un elemento solo. Le somiglianze incerte le giudica un modello; elementi con codici o numeri diversi non si uniscono mai. I nomi alternativi restano registrati.",
          "In questa fase si aggiungono anche i collegamenti tra la macchina e i suoi componenti e codici: non vengono dal testo, li aggiunge il sistema.",
          "Unire due nomi serve a evitare duplicati, mantenendo i nomi alternativi e le citazioni. Non significa mettere insieme tutte le cause possibili o confondere componenti diversi: una somiglianza di parole, da sola, non basta a decidere che siano la stessa cosa.",
          "Se lo stesso collegamento compare in più passaggi, nel grafo può diventare una linea sola con più occorrenze. Le prove e le condizioni di ciascuna restano separate nel pannello. La linea può essere verde grazie a un'occorrenza verificata, mentre un altro passaggio resta in dubbio: controlla l'occorrenza pertinente al tuo caso.",
        ],
      },
      {
        id: "chiedi",
        heading: "Chiedi",
        body: [
          "I collegamenti in dubbio che vengono dallo stesso punto del manuale diventano una domanda sola. Risponde prima l'agente, se previsto; quello che resta arriva a te, fino al massimo stabilito.",
          "Alla fine dell'esecuzione compare un riquadro che dice com'è andata e qual è il prossimo passo.",
          "I dubbi possono riguardare ciò che dice una riga, l'identità di due nomi simili o una pagina non leggibile. Raggrupparli per passaggio ti permette di confrontare più affermazioni con la stessa fonte senza rispondere a una domanda per ogni linea del grafo.",
          "Una risposta può richiedere di separare elementi o ricontrollare una parte del risultato. Per questo puoi vedere un'ulteriore verifica dopo l'unione o nuove domande dopo aver applicato le prime risposte. Le relazioni che restano irrisolte mantengono il loro stato di dubbio.",
        ],
      },
      {
        id: "fermare",
        heading: "Fermare un'esecuzione",
        body: [
          "«Ferma» interrompe l'estrazione in corso. Il lavoro fatto fino a quel momento resta salvato.",
          "Puoi anche lasciare la schermata: l'estrazione continua e la spia blu nella barra a sinistra ti riporta lì.",
          "Usa «Ferma» quando vuoi interrompere davvero il lavoro; cambiare pagina non lo interrompe. Il tempo e il costo già sostenuti non vengono annullati. I dati salvati fino all'interruzione non equivalgono a una versione completata e approvata.",
          "Se l'esecuzione non riesce o viene interrotta, la libreria e il registro ti permettono di vedere dove si è fermata. «Nuova versione» avvia una nuova estrazione del manuale; il comando «Riprendi» nel replay, invece, riprende soltanto la riproduzione degli eventi.",
        ],
      },
    ],
  },
  {
    slug: "domande",
    title: "Domande e approvazione",
    icon: "question",
    lead:
      "Le domande servono a sciogliere i dubbi dell'estrazione. Presentano il testo disponibile e quello che il sistema propone; quando il passaggio non basta, puoi aprire la pagina originale. Le risposte aggiornano singole decisioni, mentre l'approvazione finale riguarda l'intera versione del grafo.",
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
          "Apri una riga per andare al passo indicato. Il numero arancio nella barra laterale conta i manuali la cui versione attuale aspetta una persona: non è il totale delle domande o delle relazioni in dubbio.",
          "Questa pagina riassume le versioni attuali. Per controllare una versione precedente, apri il manuale e scegli la relativa voce nella cronologia. Se rispondi ai dubbi di una versione della campagna, l'applicazione ti sposta sulla copia creata per le tue risposte.",
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
          "Leggi prima «Nel manuale», poi ogni affermazione di «Il sistema propone». Chiediti se quel passaggio collega davvero il problema, la causa e l'azione indicati, incluse le condizioni. Un intervento tecnicamente plausibile non va confermato se il testo mostrato non lo sostiene.",
          "Per esempio, se una domanda contiene tre affermazioni e la fonte sostiene soltanto la prima e la terza, scegli «Solo in parte», seleziona 1 e 3 e premi «Tieni le affermazioni scelte». Le altre vengono respinte. Serve almeno una selezione; se nessuna è sostenuta, usa «No».",
          "Le domande sui nomi usano «Sì, la stessa» o «No, diverse»: valuta se i due nomi indicano davvero lo stesso elemento. Per una pagina illeggibile puoi scegliere di saltarla o inviare una trascrizione. La trascrizione viene conservata nel rapporto per una successiva estrazione; non genera automaticamente nuovi nodi nella versione corrente.",
          "Le domande vengono presentate una alla volta e ogni risposta inviata viene salvata. Puoi lasciare la schermata e tornare per completare quelle rimaste; le selezioni o il testo che non hai ancora inviato non sono una risposta registrata.",
        ],
      },
      {
        id: "applicare",
        heading: "Applicare le risposte",
        body: [
          "Quando hai risposto a tutte le domande presentate, «Applica le risposte» riprende l'esecuzione usando il lavoro salvato e aggiorna il grafo con le tue decisioni. Le parti già completate vengono riutilizzate; eventuali controlli necessari dopo le modifiche possono richiedere altro lavoro. Attendi l'esito prima di valutare il grafo aggiornato.",
          "Una tua conferma o un tuo rifiuto valgono più dei controlli automatici.",
          "Inviare una risposta e applicarla sono due passaggi distinti: finché ci sono risposte da applicare, l'approvazione resta bloccata. Dopo l'applicazione puoi tornare al grafo, aprire le relazioni coinvolte e verificare la decisione registrata nelle prove.",
          "La pagina indica anche quanti dubbi restano oltre il limite di domande: quelle relazioni possono essere presenti, ma restano fuori dalla parte verificata. La ripresa richiede che non ci sia un'altra esecuzione attiva e che rimanga spazio nei limiti di spesa; in caso di blocco viene mostrato il motivo.",
        ],
      },
      {
        id: "approvare",
        heading: "Approvare il grafo",
        body: [
          "L'ultimo passo è l'approvazione. Nel grafo trovi «Approva» quando tutte le domande presentate sono state risposte e le risposte sono state applicate; dalla schermata delle domande puoi anche scegliere «Rifiuta». Per registrare la decisione l'esecuzione riprende brevemente usando lo stato salvato. Nei grafi avviati dall'interfaccia decide una persona.",
          "I grafi della campagna di valutazione sono stati approvati in automatico e lo indicano con «Approvato dal sistema». Se rispondi a una domanda di uno di questi grafi, la prima risposta ne crea una copia su cui continui a lavorare: l'originale non cambia.",
          "Prima di approvare, controlla di essere sulla versione giusta, cerca alcuni sintomi o codici del manuale e confronta i percorsi con le pagine citate. Valuta anche le relazioni in dubbio e i contesti delle azioni: una versione può essere approvata conservando relazioni non verificate.",
          "Approvare registra la tua decisione sul risultato complessivo; non trasforma tutte le linee gialle in verdi. «Rifiuta» registra invece che la versione non è approvata, senza cancellare il manuale e la sua cronologia. La dicitura «Approvato dal sistema» indica una decisione automatica del flusso, non una revisione umana delle informazioni.",
        ],
      },
      {
        id: "passi",
        heading: "A che punto è un grafo",
        body: [
          "Nella pagina di un manuale la versione attuale mostra tre passi: estrazione, domande, approvazione. Una spia verde con la spunta indica un passo fatto, arancio un passo che aspetta te, rossa un passo non riuscito.",
          "Sotto i passi c'è sempre un solo pulsante principale: il prossimo passo da fare.",
          "«In corso» invita a seguire la costruzione; le domande aperte richiedono di rispondere e poi applicare; «Controlla e approva» porta alla revisione finale. Se la versione non è riuscita, puoi vedere il punto dell'interruzione. Queste indicazioni descrivono il flusso di lavoro, mentre i contatori «Verificate», «In dubbio» ed «Escluse» descrivono le relazioni.",
          "Non dedurre il completamento dal numero di nodi o dalla sola fine dell'estrazione. Controlla l'esito della versione e il prossimo passo: la costruzione può essere terminata e aspettare ancora la tua approvazione.",
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
          "Scegli un nodo per leggerne nome, citazioni e relazioni; scegli una linea per capire il collegamento tra i suoi due estremi. Dal pannello puoi passare dal nodo a una relazione e dalla relazione ai nodi coinvolti, continuando a esplorare il percorso.",
          "La posizione nello spazio serve a rendere il grafo esplorabile. Due nodi vicini non indicano necessariamente una relazione: il significato viene dalle linee e dalla loro descrizione. «Riordina» e «Inquadra» cambiano la vista, senza cambiare le informazioni salvate.",
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
          "Il colore di un nodo indica il suo tipo, mentre quello di una linea indica lo stato della relazione. Un nodo colorato non è, da solo, un elemento verificato: apri il collegamento che ti interessa per leggere le prove.",
          "I filtri cambiano la vista, senza eliminare dati. I nodi che non partecipano alle relazioni mostrate possono sparire dalla vista; i contatori della legenda e della barra in basso riassumono invece l'intera versione. Per questo i numeri possono essere maggiori degli elementi che vedi dopo un filtro.",
          "Per concentrarti sulla diagnosi puoi nascondere nelle impostazioni le relazioni aggiunte dal codice. Quelle linee descrivono l'appartenenza di componenti e codici alla macchina; non sono un ulteriore testimone della causa o dell'intervento.",
        ],
      },
      {
        id: "cercare",
        heading: "Cercare un sintomo o un codice",
        body: [
          "Scrivi nel campo di ricerca in alto (il tasto «/» ci porta subito il cursore) e scegli un risultato. Il grafo mette in evidenza il percorso di diagnosi: dal sintomo o codice alle cause, dalle cause alle azioni e ai componenti. Il resto si attenua. «Mostra tutto il grafo» torna alla vista completa.",
          "La ricerca considera i sintomi e i codici di errore, inclusi i loro nomi alternativi, e accetta anche una parte del testo. Non cerca tutti i tipi di nodo. Se un nome di componente non restituisce risultati, puoi esplorare quel componente nel grafo e dal pannello delle relazioni.",
          "Per esempio, cerca una parte di «pompa non parte», scegli il sintomo e apri la linea verso una causa. Poi segui la relazione verso il controllo o l'intervento e leggi le prove. Se ci sono più cause, il percorso le evidenzia senza scegliere automaticamente quella corretta per il caso reale.",
          "La ricerca evidenzia il percorso mantenendo i filtri attivi. Se una parte sembra mancare, torna a «Tutte» e verifica anche l'impostazione sulle relazioni aggiunte dal codice. Se non trovi un sintomo, prova un altro termine presente nel manuale e controlla la versione selezionata e il PDF.",
        ],
      },
      {
        id: "prove",
        heading: "Le prove",
        body: [
          "Scegliendo un nodo o un collegamento, a destra compaiono le prove: le righe del manuale con la pagina, lo stato, i testimoni che lo sostengono e, se qualcuno ha deciso, chi. «Apri la pagina» mostra la pagina originale con il testo citato evidenziato, quando la sua posizione è nota.",
          "Il pannello si chiude con la croce o con il tasto Esc.",
          "Nel dettaglio di un nodo trovi anche gli eventuali nomi alternativi e l'elenco delle relazioni collegate. Nel dettaglio di una relazione trovi i due estremi, lo stato complessivo e le occorrenze. Ogni occorrenza ha il proprio passaggio e può avere testimoni, decisioni e condizioni differenti.",
          "Leggi «Vale se», «Prima», «Attenzione», «Risultato atteso» e «Ordine» quando compaiono: precisano quando il collegamento è applicabile e come va interpretata l'azione. Un risultato atteso da un controllo non è un fatto già osservato sulla tua macchina.",
          "I numeri di pagina seguono l'ordine del PDF, che può differire dalla numerazione stampata nel manuale. L'evidenziazione compare solo se il sistema conosce la posizione del testo; una pagina senza evidenziazione può comunque essere la fonte corretta. In quel caso cerca il passaggio citato nell'immagine della pagina.",
        ],
      },
      {
        id: "dal-vivo",
        heading: "Il grafo che cresce",
        body: [
          "Durante un'estrazione il grafo si costruisce sotto i tuoi occhi: i nodi nuovi compaiono man mano e i collegamenti cambiano colore quando vengono controllati. In basso vedi i contatori e l'ultima relazione trovata. Quando l'estrazione finisce si apre il grafo, con il prossimo passo in alto a destra.",
          "Le estrazioni passate per cui è disponibile una registrazione si possono rigiocare con «Rigioca l'esecuzione», a velocità 1×, 4× o 16×, con pausa. Rigiocare non costa nulla: non chiama nessun modello.",
          "Durante la costruzione i contatori possono cambiare anche in diminuzione: i controlli possono scartare proposte e l'unione può raccogliere più nomi in un solo nodo. Il numero più alto visto durante l'estrazione non è necessariamente il numero finale di informazioni conservate.",
          "Il replay riproduce eventi di una versione già esistente. «Pausa» e «Riprendi» controllano la riproduzione, non un'estrazione reale; il costo mostrato è quello della registrazione, non una nuova spesa. Usalo per capire il processo, poi apri il grafo finale per consultare prove e stato della versione.",
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
          "Una versione del grafo e una revisione del PDF sono due cose diverse: puoi estrarre più volte lo stesso documento senza cambiare la fonte. Un PDF diverso viene registrato come un altro manuale. Le risposte su una versione dell'interfaccia aggiornano quella versione; la prima risposta su una versione della campagna crea invece una copia.",
          "La versione attuale è la più recente, non necessariamente quella approvata o più adatta alla tua consultazione. Prima di usare un percorso controlla l'esito della versione; nella pagina del manuale puoi aprire anche quelle precedenti e confrontarle passando dall'una all'altra.",
          "La colonna «Codice» identifica la versione del software con cui è stata prodotta l'estrazione, quando disponibile. Può aiutarti a distinguere risultati ottenuti in momenti diversi, ma non è un codice di errore della macchina né un voto di qualità del grafo.",
        ],
      },
      {
        id: "registro",
        heading: "La pagina Esecuzioni",
        body: [
          "Elenca tutte le esecuzioni di tutti i manuali, dalla più recente, con esito, durata e costo. Puoi vedere solo quelle avviate dall'interfaccia o solo quelle della campagna di valutazione, e ordinare per colonna. Una riga porta al passo giusto: il grafo, le domande o l'esecuzione in corso.",
          "Usa «Dall'interfaccia» per ritrovare il tuo lavoro e «Campagna» per consultare le esecuzioni di riferimento già presenti. Cliccando l'intestazione di una colonna ordinabile puoi confrontare date, durata o costo. L'esito ti aiuta a distinguere un'estrazione ancora in corso, una versione da approvare e una non riuscita.",
          "Un trattino o un campo vuoto indica un valore non disponibile, non un tempo o un costo uguale a zero. Per capire un'interruzione apri la riga e guarda il messaggio dell'esecuzione, invece di basarti soltanto sulla durata.",
        ],
      },
      {
        id: "costi",
        heading: "Come si forma il costo",
        body: [
          "Il costo dipende dalle chiamate ai modelli: mappa delle pagine, letture delle unità, verificatore, revisione dei nomi e agente sui dubbi, oltre a eventuali tentativi aggiuntivi. Ogni chiamata passa dal registro di spesa; prima di eseguirla viene controllato che rientri nei limiti disponibili.",
          "Anche l'identificazione automatica della macchina dopo il caricamento usa un modello e può generare un piccolo costo. Rigiocare un'esecuzione, consultare il grafo e aprire le pagine già disponibili non avviano nuove chiamate al modello.",
          "Applicare le risposte riutilizza il lavoro salvato e di norma evita di ripetere l'estrazione; eventuali nuovi controlli possono però avere un costo. Anche registrare l'approvazione richiede una ripresa, quindi il sistema verifica comunque la disponibilità di spesa prima di partire.",
          "Distingui il costo stimato nel riepilogo dal costo registrato nell'esecuzione. Se una vista indica «Costo stimato», il valore non va letto come un addebito definitivo. Un costo basso o un tempo breve, da soli, non descrivono la completezza o la correttezza del grafo.",
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
          "Lo schema descrive i ruoli degli elementi e il significato dei collegamenti. Un sintomo può indicare una causa; un codice indica una causa; la causa riguarda un componente e può essere affrontata con un'azione. La macchina è collegata ai componenti e ai codici che fanno parte del suo grafo. Nei grafi costruiti dalla pipeline a grafo connesso un componente può far parte di un altro, un'azione dice su quale componente agisce, un sintomo dove si osserva, e un rimedio che il manuale dà senza nominare una causa è collegato direttamente al sintomo o al codice.",
          "Per esempio, «la pompa non parte», «alimentazione assente» e «controllare il cavo» occupano tre ruoli diversi anche se compaiono nella stessa riga del manuale. Tenerli separati permette di collegare la stessa causa a più sintomi o di rappresentare più controlli per uno stesso problema.",
          "Lo schema è fisso per tutti i manuali: non aggiungi nuovi tipi dalla pagina Ontologia. Un grafo concreto contiene soltanto gli elementi e i collegamenti trovati per quella fonte; non deve riempire ogni possibile ramo dello schema. Avere lo stesso schema permette di leggerli nello stesso modo, senza rendere identiche le informazioni di macchine diverse.",
        ],
      },
      {
        id: "chi-crea",
        heading: "Chi crea i collegamenti",
        body: [
          "La linea continua indica i collegamenti estratti dal modello, ognuno con le sue prove nel manuale. La linea tratteggiata indica quelli aggiunti dal sistema: legano la macchina ai suoi componenti e ai suoi codici.",
          "Sotto lo schema trovi la descrizione di ogni tipo e di ogni collegamento, così come sono scritte nello schema.",
          "La distinzione tra linea continua e tratteggiata in questa pagina riguarda l'origine del collegamento. Nel grafo di un manuale, invece, il colore delle linee distingue anche lo stato della verifica. Una relazione ammessa dallo schema deve ancora avere prove per essere una relazione verificata della tua versione.",
          "I collegamenti aggiunti dal sistema aiutano a tenere la macchina collegata ai componenti e ai codici individuati. Sono riconoscibili nel pannello come «Aggiunta dal sistema» e possono essere nascosti nelle impostazioni; non sostituiscono le citazioni delle relazioni diagnostiche.",
        ],
      },
    ],
  },
  {
    slug: "impostazioni",
    title: "Impostazioni",
    icon: "settings",
    lead:
      "La rotella in basso a sinistra apre le impostazioni. Premi «Salva» per applicare le modifiche; «Annulla», la croce ed Esc chiudono senza salvarle. Le scelte di estrazione e revisione valgono per le nuove esecuzioni: una versione già avviata le conserva anche quando riprende dopo le risposte. Le preferenze di vista si applicano ai grafi dopo il salvataggio.",
    sections: [
      {
        id: "chiave",
        heading: "Chiave OpenAI",
        body: [
          "Di solito si usa la chiave già configurata sul computer. Se ne scrivi un'altra, verrà usata per le nuove estrazioni e per la lettura dei dati della macchina. La chiave viene salvata localmente; l'interfaccia mostra soltanto gli ultimi quattro caratteri della chiave in uso. «Usa .env» torna a quella di sempre.",
          "La chiave è la credenziale che permette all'applicazione di chiamare il servizio OpenAI. Il campo nasconde quello che digiti; dopo il salvataggio l'interfaccia mostra soltanto un riferimento alla chiave in uso, senza restituirne il valore completo. La credenziale viene usata per le richieste al servizio.",
          "Lascia il campo vuoto se vuoi mantenere la chiave già impostata. Se selezioni «Usa .env», premi poi «Salva» per confermare il ritorno alla chiave configurata sul computer. In assenza di una chiave utilizzabile, le operazioni che richiedono il modello possono fallire; i grafi già disponibili restano consultabili.",
        ],
      },
      {
        id: "estrazione",
        heading: "Estrazione",
        body: [
          [
            "Ragionamento: il livello di elaborazione richiesto al modello, da «Nessuno» ad «Alto». Cambiarlo può incidere su tempi, costo e risultato, senza garantire un miglioramento della qualità.",
            "Letture per unità: quante letture indipendenti vengono richieste per ogni porzione del manuale. Puoi scegliere 1, 2 o 3; il valore iniziale è 2. Con una sola lettura manca il testimone dell'accordo tra letture; aggiungerne una aumenta il lavoro richiesto al modello.",
          ],
          "Per imparare il flusso puoi mantenere i valori iniziali e controllare il risultato tramite le prove. Se cambi queste scelte, serve una nuova estrazione per osservarne l'effetto: il grafo già salvato non viene ricalcolato quando premi «Salva».",
          "Le letture per unità riguardano l'estrazione delle relazioni, non il numero di volte in cui il PDF viene caricato. La classificazione delle pagine ha il proprio processo; scegliere una lettura per unità non elimina tutti gli altri controlli.",
        ],
      },
      {
        id: "agente",
        heading: "Agente",
        body: [
          "Il modello e il ragionamento dell'agente che risponde ai dubbi al posto tuo, secondo la scelta fatta in «Chi risponde ai dubbi».",
          "L'agente è un revisore automatico: confronta le proposte con la fonte e può confermare, respingere o lasciare un dubbio irrisolto. Cambiare il suo modello riguarda questa revisione; non sostituisce il modello di estrazione. Nei nuovi avvii la stessa scelta viene usata anche per la revisione della mappa delle pagine.",
          "Per inviare i dubbi all'agente scegli «Solo agente» o «Agente, poi io» nella creazione del grafo. Con «Solo io» i dubbi di estrazione arrivano direttamente a te. Il modello e il ragionamento salvati non cambiano questa scelta di chi risponde, e l'approvazione finale resta una decisione umana.",
        ],
      },
      {
        id: "domande",
        heading: "Domande",
        body: [
          "Il numero massimo di domande che arrivano a una persona in un'estrazione. Le domande più importanti vengono prima; oltre il massimo i dubbi restano nel grafo come non verificati.",
          "Nella finestra puoi scegliere 5, 10, 15 o 20 domande; il valore iniziale è 10. Il limite riguarda la versione nel suo insieme e tiene conto delle domande già presentate anche dopo una ripresa. L'approvazione finale è un passaggio distinto e non consuma una di queste domande.",
          "Una domanda può contenere più affermazioni. Un limite di 10 domande non significa quindi 10 relazioni né garantisce che tutti i dubbi siano stati esaminati. Per aumentare il numero disponibile in una nuova estrazione, salva la scelta prima di avviarla; modificare il limite non amplia retroattivamente le domande di una versione esistente.",
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
          "Queste due scelte si applicano dopo «Salva», in tutti i grafi, senza avviare un'estrazione. Mostrare o nascondere le linee aggiunte dal codice e i nomi cambia solo la vista, non i nodi, le prove o le decisioni salvate.",
          "Se i nomi rendono affollata la vista, disattivali e usa il passaggio del mouse o il pannello del nodo per leggerli. Se vuoi vedere a colpo d'occhio quali componenti e codici appartengono alla macchina, riattiva le relazioni aggiunte dal codice. Puoi cambiare queste preferenze durante la consultazione.",
        ],
      },
    ],
  },
{
  "slug": "modifica-grafo",
  "title": "Modificare un grafo",
  "icon": "pencil",
  "lead": "Modifica grafo apre una sessione sulla versione che stai leggendo. Puoi correggere nodi, relazioni e occorrenze; solo l’accettazione finale crea una nuova versione.",
  "sections": [
    {
      "id": "percorso",
      "heading": "Modifica, Controlla, Riepilogo",
      "body": [
        "Il pulsante Modifica grafo è disponibile dopo la generazione, sul grafo aperto e nella cronologia. La barra indica sempre la versione di partenza. Se un’estrazione è ancora attiva o ci sono risposte da applicare, il motivo del blocco è visibile.",
        "In Modifica scegli Nodi, Relazioni o Grafo. Filtri, prove e collegamenti permettono di raggiungere lo stesso elemento nelle diverse viste. Modifica le celle, aggiungi o elimina elementi; Annulla modifica e Ripeti modifica valgono per questa sessione.",
        "Avanti apre Controlla: integrità, campi richiesti e facoltativi, collegamenti e fonti hanno indicatori separati. Un controllo conduce alla riga o al campo interessato. I controlli strutturali non garantiscono la correttezza tecnica.",
        "Avanti apre Riepilogo con aggiunte, rimozioni e valori prima/dopo, incluse le verifiche invalidate e i collegamenti aggiornati dal sistema. Indietro conserva le modifiche. Una correzione fa scadere i controlli e i riconoscimenti precedenti."
      ]
    },
    {
      "id": "celle-prove",
      "heading": "Campi, relazioni e prove",
      "body": [
        "Invio conferma una cella semplice; Tab conferma e passa al controllo successivo; Esc annulla il testo della cella attiva. Descrizioni, istruzioni e liste usano un campo multilinea. Le liste si inseriscono come JSON, per esempio [\"primo\", \"secondo\"].",
        "Assente, vuoto, non dichiarato e compilato sono stati distinti. Zero e «falso» sono valori compilati. Il menu della cella distingue Svuota, Imposta senza valore e Rimuovi campo facoltativo. Identificativi e campi sconosciuti restano in sola lettura.",
        "Le relazioni ammettono soltanto estremi compatibili. Proporre la stessa tripla aggiunge un’occorrenza, senza duplicare il collegamento. Cambiare estremi o tipo crea una nuova identità. Eliminare un nodo mostra i collegamenti rimossi; eliminare l’ultima occorrenza elimina la relazione.",
        "Le parole del manuale restano in sola lettura. Nelle occorrenze puoi scegliere segmenti della fonte verificata, condizioni e un’annotazione personale. Se il PDF o il suo indice non sono verificabili, le citazioni incorporate restano leggibili; non si inventano nuove prove. Le relazioni aggiunte dal sistema restano in sola lettura."
      ]
    },
    {
      "id": "accettazione",
      "heading": "Accettare una nuova versione",
      "body": [
        "Accetta modifiche e crea nuova versione è l’unico comando che salva. Prima riconosci i dubbi residui elencati. La nuova versione viene aperta come accettata, senza un secondo Approva, e l’originale rimane invariato. Non richiede chiamate AI.",
        "Una modifica a un nodo o a un’occorrenza invalida le verifiche interessate. Accettare la versione non le rende verdi. Dopo i controlli, Conferma contenuto o Rifiuta contenuto registra una decisione umana sulla singola occorrenza: la conferma umana è distinguibile dalla verifica automatica, anche senza una fonte collegata.",
        "La cronologia conserva il padre e il numero della revisione. Scarica versione e provenienza include grafo, base congelata, differenze, controlli e decisione. Le domande dell’estrazione restano riconoscibili come contesto della fonte e le attività aperte restano in Tocca a te.",
        "Se l’esito del salvataggio è incerto, la sessione resta bloccata sullo stesso contenuto. Verifica il salvataggio apre la versione già creata oppure permette di riprovare la stessa richiesta."
      ]
    },
    {
      "id": "uscita",
      "heading": "Uscire e scartare",
      "body": [
        "Le modifiche vivono soltanto nella sessione aperta. Esci senza salvare, logo, percorso e sidebar chiedono se vuoi continuare o scartare quando ci sono modifiche. Continua a modificare conserva i valori; Esci e scarta li perde.",
        "Ricaricare o chiudere la pagina prima dell’accettazione scarta la sessione, anche tornando con la cronologia del browser. Il browser può mostrare il proprio avviso di uscita. Non esistono autosalvataggio o recupero della bozza. Una richiesta di accettazione già inviata può invece completarsi sul server."
      ]
    }
  ]
},
];
