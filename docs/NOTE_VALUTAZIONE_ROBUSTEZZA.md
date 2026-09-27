# Valutare il grafo oltre al gold

Queste note distinguono le misure implementate nelle fasi 1–2 dalle ipotesi per un
esperimento successivo. Non modificano i gold e non dimostrano precisione semantica.
I sei manuali correnti sono materiale di sviluppo già osservato.

## Che cosa resta invisibile al recall

Il recall dei rami chiede se esiste nel grafo un percorso corrispondente a ciascun
ramo annotato. Può rimanere alto quando lo stesso grafo contiene anche collegamenti
sbagliati, cause fuse, rimedi fuori contesto o estrazioni scorrette su altre pagine.
Anche una citazione valida può sostenere soltanto una parte del fatto. La verifica
sul PDF è necessaria perché il lettore e il verificatore possono condividere lo
stesso errore di ricostruzione di una tabella.

Le misure ora introdotte rispondono a domande diverse:

- Qualità strutturale senza gold: vincoli di identità violati, cause orfane,
  problemi senza azione, duplicati, prove mancanti e cause dedotte. Un problema
  senza azioni può riprodurre fedelmente un manuale che elenca soltanto cause.
- Coppie contrastive: due voci del gold riconosciute come diverse restano nodi
  separati, con percorsi che recuperano le rispettive azioni. Le coppie generate
  per somiglianza lessicale sono candidate da rivedere, non verità acquisite.
  Questa misura non esclude ulteriori archi sbagliati fra i nodi.
- Revisione cieca: precisione di un campione anche su pagine fuori dal gold.
  Le risposte spettano a Fabio. Il campionamento favorisce intenzionalmente le
  pagine esterne: un totale non pesato descrive il campione, non l'intero grafo.
- Stabilità: Jaccard delle relazioni con nomi normalizzati. Cambiare una parafrasi
  può abbassarlo anche a significato invariato; ripetere un errore può alzarlo.

Il voto di maggioranza di tre chiamate allo stesso modello riduce una parte della
variabilità, ma non costituisce tre fonti indipendenti e non elimina errori
sistematici. Il giudice dei KPI e quello interno alla pipeline condividono una
famiglia di modelli: l'accordo non sostituisce la revisione umana.

Le tre esecuzioni riusano gli stessi rami e appartengono agli stessi manuali.
Non sono 900 osservazioni indipendenti: gli intervalli di Wilson già prodotti dai
KPI non vanno interpretati come una misura affidabile della generalizzazione a
nuovi manuali. Nel confronto operativo conviene mostrare i tre valori e la loro
variabilità per manuale. La soglia di 0–4 rami del prompt è un criterio pratico di
accettazione, non un intervallo di confidenza stimato in questo esperimento.

## Confronti utili trovati in letteratura

[RAGChecker](https://arxiv.org/abs/2408.08067) separa metriche complessive e diagnosi
dei componenti e usa controlli a livello di singola affermazione. È un riferimento
per distinguere perdita nella selezione delle pagine, perdita nell'estrazione e
mancata fedeltà alla fonte. Il suo compito è RAG, quindi i suoi risultati numerici
non sono trasferibili ai nostri grafi.

[KGCQual](https://arxiv.org/abs/2607.10212), preprint dichiarato in revisione,
propone valutazioni di entità e relazioni rispetto al testo, includendo
completezza, risoluzione, connettività e conservazione dei predicati. È pertinente
alla necessità di misure complementari al gold; l'allineamento lessicale e la
negazione leggera descritti dagli autori non bastano, da soli, a validare condizioni
operative e rimedi in tabelle complesse.

[FinReflectKG-EvalBench](https://huggingface.co/datasets/domyn/FinReflectKG-EvalBench/blob/main/README.md)
conserva giudizi di fedeltà sulle triplette insieme a motivazioni, avvisi e contesto
documentale. L'idea riutilizzabile è rendere ispezionabile il motivo del giudizio,
non assumere che un punteggio automatico misuri da solo la precisione reale.

## Esperimenti successivi proposti, non eseguiti

1. **Audit in entrambe le direzioni.** Campionare pagine o voci del manuale senza
   guardare il grafo e controllare ciò che manca; campionare separatamente archi
   del grafo e controllare ciò che il PDF sostiene. Riportare precisione e copertura
   per strato, con pesi basati sulla popolazione campionata. Serve un secondo
   revisore su una parte del campione per quantificare il disaccordo.
2. **Prove di esclusione dei rimedi.** Per contrasti approvati dall'annotatore,
   verificare sia il percorso corretto sia l'assenza di percorsi verso rimedi
   riservati all'altro caso. Introdurre perturbazioni controllate, per esempio
   scambiare due voci allineate o rimuovere una condizione da una copia di prova:
   un valutatore utile deve rilevare il cambiamento. I rimedi comuni non sono
   automaticamente errori; il carattere esclusivo va confermato sul PDF.
3. **Stabilità del significato e costo della revisione.** Allineare le relazioni
   fra esecuzioni usando provenienza e una revisione semantica indipendente, poi
   separare variazioni del nome, della causa, dell'azione e dei vincoli. Misurare
   minuti umani per manuale e per errore corretto, oltre a token e tempo macchina.
   Il confronto utile è costo per ramo verificato corretto, non costo per nodo.

Le prove di esclusione sono una possibile estensione interessante del progetto,
non una rivendicazione di novità scientifica. Un eventuale test finale richiede
manuali non usati per progettare queste correzioni e criteri congelati prima di
osservarne gli output.
