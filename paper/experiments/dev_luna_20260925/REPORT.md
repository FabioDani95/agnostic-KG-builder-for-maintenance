# Risultati del pilot di estrazione

Campagna di sviluppo sui quattro manuali già osservati. Modello: GPT-6 Luna. Nessun gold fornito al generatore. Configurazione corrente con escalation disabilitata.

| Manuale | Stato | Tempo totale (s) | Generazione (s) | Chiamate | Costo contabilizzato USD | Nodi / relazioni | Review | Gold storico: autonomi / totale |
|---|---|---:|---:|---:|---:|---|---:|---|
| Eastman Eagle S3L | completed | 258.934 | 236.545 | 21 | 0.030195 | 144 / 145 | 44 | 3/8 |
| Danfoss Active Power Filter | completed | 114.825 | 102.323 | 16 | 0.016793 | 35 / 34 | 23 | 0/8 |
| Graco Check-Mate 200 Pump | completed | 106.154 | 99.301 | 15 | 0.016008 | 42 / 41 | 10 | 0/18 |
| Powermax30 AIR plasma cutting system | completed | 654.585 | 606.277 | 63 | 0.093336 | 134 / 132 | 82 | Non disponibile |

Durata campagna, incluso smoke test e avvio dei processi: 1152.319 secondi.
Registro cumulativo: {"absolute_budget_usd": 15.0, "committed_usd": 0.156349335, "active_reserved_usd": 0.0, "remaining_usd": 14.843650665, "reservation_count": 116, "finalized_count": 116}

Il cap è 15 USD complessivi. La tabella riporta il costo contabilizzato: stima sui token osservati più importo massimo prenotato per i tentativi senza consumo osservabile. Non è una fattura. results.json separa estimated_usd (parte calcolabile dai token), charged_usd (importo prudenziale complessivo) e unknown_cost_calls. Preparazione e overhead sono separati dalla generazione nei timing.json.

## Interpretazione e limiti

Nodi, relazioni e validità dello schema non misurano da soli la correttezza diagnostica. I risultati sul gold storico usano il matching già adottato nella campagna precedente: sono indicatori di sviluppo da controllare manualmente. Il gold è limitato alle parti annotate; Hypertherm non ha un gold. Non attribuire un cambiamento rispetto a v11 al solo modello: anche codice e configurazione differiscono.

I grafi restano sottoposti ai gate di revisione. Le liste diagnostic_paths_for_review.md servono al controllo dei tecnici, non sono istruzioni manutentive approvate.

## File

manifest.json identifica PDF e commit; runtime_profile.json congela configurazione e dipendenze; real_call_budget.jsonl contiene tutte le prenotazioni/finalizzazioni; timing.json misura le durate; generation_response.json e graph.json conservano gli output; historical_gold_evaluation.json conserva i confronti dove disponibili. results.json è il riepilogo strutturato.
