# Recupero controllato dell’estrazione vuota Atlas

Codice del generatore: `bec1e7c`. Il confronto principale D resta a `8abec90`.
Le due risposte originali del provider, la mappa e il gate mappa sono conservati
qui. `replay.py` documenta il programma eseguito: verifica prompt, fonte e schema
identici, riutilizza le due risposte senza costo e chiama il modello soltanto per
il recupero e le stazioni successive. Il registro è quello della campagna, con
il tetto cumulativo di 7,204403 USD che rispetta i 5 USD aggiuntivi autorizzati.

Output: `campaign/atlascopco_drb_booster/runs_empty_probe/v3_r1/`; 34/49 rami,
147 proposte e 124 archi verdi. Non è una replica indipendente. Non sostituisce
Atlas D/r3 e non entra nel totale 684/900 né nel nuovo campione cieco.

Per ripetere l’intervento servono il PDF locale e una cartella di uscita nuova;
il programma rifiuta di sovrascrivere quella esistente. Richiedere nuovamente
chiamate al modello non garantisce lo stesso recupero. I due input riutilizzati
sono invece fissati e verificati esattamente.
