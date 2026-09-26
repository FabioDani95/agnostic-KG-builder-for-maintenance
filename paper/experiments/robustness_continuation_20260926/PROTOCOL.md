# Confronto di sviluppo C9

Congelato prima delle nuove chiamate. Nessun gold tecnico disponibile; nessuna accettazione scientifica dichiarata. Stesso ledger cumulativo robustness_20260925, cap 20 USD.

Pacchetti: Hypertherm pagine fisiche 67–69 (alternative e continuazione) e 96–100 (Test 9 e sue condizioni), più Eastman 37–39. Per ciascuno confrontare Luna low/24k e Luna medium/24k, stessa sorgente e codice; due repliche sul Test 9. Non scegliere la replica migliore. Il confronto misura l'effort, non cambia modello.

Denominatori: tutti i candidati di ogni pacchetto, tutte le disposizioni, e rami sorgente identificati nell'audit manuale di sviluppo separato dal gold. Ogni recupero dichiarato richiede confronto PDF di sintomo, causa esplicita, rimedio, condizioni, prerequisiti e ordine. Stati non giudicati separati. Citazioni letterali non sono prova semantica. Nessuna soglia sul numero delle review.

Accettazione locale: almeno un caso documentale recuperato senza relazioni inventate, nessuna perdita dei rami preesistenti giudicati corretti nel probe appaiato. Registrare errori/regressioni, compresi output pubblicabili ma incompleti. Dopo un beneficio verificato, congelare sorgente/configurazione e rieseguire i quattro manuali. La verifica end-to-end usa nuove estrazioni poiché il prompt è cambiato.

La correzione umana crea una nuova revisione, ricompila e conserva i blocchi; non è un'approvazione. Il test applicativo non viene attribuito a tecnici reali. Le proposte dell'agente sono esposte alle predizioni e separate dai moduli A/B.

## Emendamento C11 prima dei run
C9 è limitato alla prima coppia Test 9; la matrice completa di pacchetti è C10. I pacchetti chiamano direttamente il compilatore e non esercitano recovery_feedback. C10 end-to-end Eastman è conservato ma non accettato: il test di integrazione ha scoperto che il feedback di recupero contaminava l’inventario sorgente. C11 separa il feedback in un messaggio escluso dalle evidenze e non ritenta predizioni prive di anchor locali. Nuova sorgente congelata source_c11.tar.gz, generatore v21; nuove estrazioni complete dei quattro manuali. I pacchetti C10 misurano solo i moduli invariati del compilatore, non certificano C11 end-to-end.

## Emendamento C12 prima delle chiamate
Il run completo C11 Hypertherm mostra che le pagine 98–99, pur disponibili come strutturali, sono assenti dai chunk diagnostici: nessun pacchetto completo Test 9 è stato creato. C12 cerca le continuazioni nella fonte intera, ancorando il recupero a un titolo iniziale già diagnostico, e registra le pagine supplementari. Il generatore diventa v22. Verifica end-to-end incrementale: tutte le richieste identiche riusano esattamente gli scambi C11, comprese le risposte fallite; solo il nuovo pacchetto 96–100 e suoi recuperi, massimo 4 chiamate, può usare rete e stesso ledger cumulativo. Sugli altri tre manuali non sono ammesse chiamate nuove; una divergenza fallisce chiusa. Questo confronto non è un’estrazione indipendente e non è un replay offline quando usa chiamate nuove. Gli usage archiviati non sono costo aggiuntivo; usare solo ledger per costo incrementale. Tutti gli artifact C11 e i fallimenti C10 sono conservati.
