# Pagine del manuale: lg_lmh2235st (gold v2, fatto da un'AI)

Ogni pagina del file PDF, che cosa contiene e se è diagnostica. Generato da `gold.json`
con `scripts/kg_gold_v2.py render-pages`: non modificarlo a mano.

| Pagina | Contenuto | Diagnostica | Perché |
| ---: | --- | :---: | --- |
| 1 | cover, safety | no | Copertina: modello LMH2235ST, P/NO MFL06272534, CAUTION di leggere le safety precautions (b1-1). |
| 2 | safety | no | Precauzioni per l'esposizione a microonde: punti a-e e 4 bullet (b2-1..b2-9). Solo contesto. |
| 3 | safety, toc | no | Foreword (b3-1) e indice; numeri di pagina stampati = pagine PDF (verificato p2-p10 e p24). |
| 4 | specifications, switch chart | no | Specifiche e SWITCH CHART degli interlock (stati attesi a porta aperta/chiusa): tabella di riferimento, non item (le stesse misure sono i test di p29, B085-B087). Nessun item core/extended. |
| 5 | safety | no | 2. Cautions: riquadro alta tensione, 9 bullet, riquadro microwave radiation, figura magnetron, servizio solo da personale qualificato (b5-1..b5-12, b2-6, b2-7). |
| 6 | setup procedure, safety | no | 3. Installation: precautions A-D (routine p6-1), grounding instructions (b6-1) e warning sul ground prong (b6-2). |
| 7 | controls | no | 4-1. Control Panel: figura del pannello con 25 richiami numerati. Nessun item. |
| 8 | controls, operation | no | 4-2. Spiegazione dei 25 tasti; unica frase condizionale su START/ENTER dopo apertura porta (b8-1, routine). |
| 9 | wiring diagram | no | 5-1. Schema elettrico (porta aperta), connettori del control module e tabella colori fili. Solo inventario componenti. |
| 10 | key matrix | no | 5-2. Key matrix 2st/1-7 x 8-13. Nessun item. |
| 11 | safety, operation, specifications | no | Precauzioni d'uso generali, trial operation (routine), elenco sistemi di sicurezza: nessun item core/extended. Precauzioni d'uso A e B (B118, B119) aggiunte dopo il confronto con v1: sicurezza (context). |
| 12 | safety, component test, error codes | sì | Safety caution per il servizio, autodiagnosi sensore umidita'/termistore e codici F-1, F-2, F-4. |
| 13 | wiring diagram, troubleshooting table | sì | Basic Check Summary: schema elettrico con 3 riquadri sintomo/verifica (5 sintomi). |
| 14 | wiring diagram, troubleshooting table | sì | Schema 'No Display or Dead' con riquadri sintomo: Dead/fusibile (B046), Dead/termostati (B037, stesso riquadro di p13), No display/connessione (B048); titolo del flowchart di p15. |
| 15 | flowchart | sì | Flowchart No Display or Dead: 6 percorsi con azione, un ramo per percorso: riconnettere (B042), fusibile (B043), filtro (B044), PCB da 1 Yes (B045), da 3 Yes 'Check PCB' (B113), da 5 Yes (B114). |
| 16 | wiring diagram | sì | Titolo Keypad Failure e schema PCB/CN3/keypad; citata come titolo del flowchart di p17. |
| 17 | flowchart | sì | Flowchart Keypad Failure: 8 percorsi con azione: latch board (B049), PCB per door sensing (B050), riconnettere via Check PWB (B051) e via 1-3 Yes (B115), casella-domanda 5 'Replace the keypad?' (B052, B116) e PCB dopo 5 No (B053, B117), questi ultimi ambigui. |
| 18 | wiring diagram | sì | Titolo No Heat / No Cook e schema elettrico; citata come titolo del flowchart p19-21. |
| 19 | flowchart | sì | No Heat / No Cook passi 1-4 + Note: 3 esiti. |
| 20 | flowchart, component test | sì | No Heat / No Cook passi 5-7 con valori di prova del trasformatore HV: 3 esiti. |
| 21 | flowchart | sì | No Heat / No Cook passi 8-12: 5 esiti (B060-B064); passo 11 con YES/NO invertiti come stampato e passo 12 senza uscita No: ambigui. |
| 22 | flowchart | sì | Flowchart Turntable Motor Does Not Work: 4 esiti con azione + 'PCB No Problem'. |
| 23 | flowchart | sì | Flowchart Turns on automatically: 6 esiti con azione + 'PCB No Problem'; passo RY1 numerato '4' due volte (B074 ambiguo); 'Replace the turntable motor' dopo la domanda sulla lampada (probabile errore, B071 ambiguo). |
| 24 | safety, component test, test procedure | sì | 7. Microwave leakage test: CAUTION (limite 5 mW/cm2, forno che funziona a porta aperta), attrezzatura, procedura di misura. |
| 25 | component test, test procedure, safety | sì | Misura a carter rimosso / forno assemblato, limiti 5 e 1 mW/cm2, note di misura, registrazione e taratura annuale. |
| 26 | test procedure | no | 8. Power output measurement: metodo di misura con formula, senza valore atteso ne' rimedio: procedura routine P005. Nessun item core/extended. |
| 27 | adjustment procedure, component test | sì | 9-1 Interlock mechanism: regolazione latch board, controllo gap A/B 1/64" (0.5 mm), figure 23-a/23-b. |
| 28 | adjustment procedure, component test | sì | Titolo pagina 'SPECIFICATIONS' ma contenuto = seguito della regolazione interlock (step 5-7) e test di dispersione; nessuna specifica. |
| 29 | component test, safety | sì | 9-2 Interlock continuity test: primary, secondary, monitor switch; tabella lancette; warning ricambi identici con type no. |
| 30 | safety, component test | sì | 10. Component testing information: CAUTION; test trasformatore e magnetron. |
| 31 | component test | sì | Test capacitor, diode, relay 2 (tabella tempi open/close), ventilation motor. |
| 32 | component test | sì | Test turntable motor, noise filter, high voltage fuse. |
| 33 | component test, safety | sì | Test touch key board con matrice tasti e connettore FPC; NOTES di sicurezza. |
| 34 | safety, repair procedure | sì | Inizio cap. 11: IMPORTANT NOTES (scollegare l'alimentazione, ricollegare i fili secondo lo schema) e procedura A smontaggio scheda di potenza/controllo (6 passi, figure 1-3). |
| 35 | repair procedure | sì | Procedura B rimozione outer case (6 passi), figura 4 con etichette dei componenti. |
| 36 | repair procedure, wiring diagram | sì | Procedura C rimozione interlock switch (3 passi) con figure 9-10 dei fili e tabella colori fili (non item). |
| 37 | repair procedure, safety, component test | sì | Procedura D rimozione magnetron (5 passi + note: cupola, guarnizione, test perdite <5 mW/cm2) e procedura E rimozione stirrer fan (3 passi). |
| 38 | repair procedure, safety, component test | sì | Procedure F rimozione porta (note: verifica interlock e perdite), G smontaggio porta con CAUTION, H montaggio/regolazione porta, I rimozione ventilation fan assembly. |
| 39 | repair procedure, safety | sì | Procedura J rimozione turntable motor (5 passi) con note di cautela sul filo. |
| 40 | exploded view | no | Cap. 12 Exploded view, introduzione: tabella modelli e vista generale con i gruppi (door, oven cavity, interior, latch board, control panel parts). Nessun item. |
| 41 | exploded view | no | DOOR PARTS: esploso con soli numeri di posizione, senza nomi ne' codici LG. Solo inventario. |
| 42 | exploded view | no | CONTROLLER PARTS: esploso con soli numeri di posizione. Solo inventario. |
| 43 | exploded view | no | OVEN CAVITY PARTS: esploso con soli numeri di posizione. Solo inventario. |
| 44 | exploded view | no | LATCH BOARD PARTS: esploso con soli numeri di posizione. Solo inventario. |
| 45 | exploded view | no | INTERIOR PARTS(I): esploso con soli numeri di posizione. Solo inventario. |
| 46 | exploded view | no | INTERIOR PARTS(II): esploso con soli numeri di posizione. Solo inventario. |
| 47 | exploded view, repair procedure | sì | BASE PLATE PARTS: esploso con numeri di posizione e riquadro '(one assembly)' con 3 passi di sostituzione del base plate assembly (testo solo nell'immagine). |
| 48 | exploded view | no | INSTALLATION PARTS: esploso dell'installazione (mounting plate, kit 6009 con vinyl bag). Solo inventario. |
| 49 | back cover | no | Retro copertina con logo LG Electronics Inc., nessun testo tecnico. |
