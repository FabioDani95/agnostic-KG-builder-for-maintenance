# Pagine del manuale: grizzly_g0872 (gold v2, fatto da un'AI)

Ogni pagina del file PDF, che cosa contiene e se è diagnostica. Generato da `gold.json`
con `scripts/kg_gold_v2.py render-pages`: non modificarlo a mano.

| Pagina | Contenuto | Diagnostica | Perché |
| ---: | --- | :---: | --- |
| 1 | cover | no | Copertina: modello G0872 60W 17"x23", copyright. Nessun item. |
| 2 | safety, legal | no | Riquadro WARNING 'leggi il manuale' (annotato in b2-1 insieme a p6/p12/p18) e avviso Prop 65 (legale, non item). |
| 3 | toc | no | Indice: serve per i riferimenti pagina stampata -> PDF (+2). |
| 4 | contact info | no | Contatti assistenza e accuratezza manuale: amministrativo, nessun item. |
| 5 | controls, identification | no | Figura di identificazione componenti: solo inventario componenti. |
| 6 | controls | no | Pannello comandi A-L e riquadro 'read manual' (b2-1). Pulse button 'per troubleshooting' e' descrizione, non item. |
| 7 | controls | no | Componenti M-S (amperometro, interruttore luce, USB, E-stop, manovella Z, tubo laser, presa): descrizioni, solo inventario. |
| 8 | controls | no | Pannello connessioni ausiliarie T-X e sistemi ausiliari Y-AA: descrizioni, solo inventario. |
| 9 | glossary, error codes | sì | Glossario con 4 codici di errore macchina (Frame Slop, Name Over Lap, XSlop Over, YSlop Over): solo significato. |
| 10 | specifications | no | Data sheet: dimensioni, elettrico, sistemi ausiliari, motori. Nessun item. |
| 11 | specifications | no | Data sheet: laser, taglio, tavola, materiali, accessori. Nessun item. |
| 12 | safety | no | Simboli di sicurezza e 7 avvisi generali (OWNER'S MANUAL accorpato in b2-1). |
| 13 | safety | sì | 17 avvisi generali: safety (incluso EXPERIENCING DIFFICULTIES, B028), DAMAGED PARTS come condition_maintenance (B026). |
| 14 | safety | no | Avvisi laser (safety): incendio, ustioni, riflessi, dispositivi di sicurezza; B032 'materials catch fire' riclassificato safety_precaution. Nessun item core/extended. |
| 15 | safety | sì | Avvisi fumi tossici: safety (incluso EXPERIENCING DIFFICULTIES/OSHA, B046), fault sistema di filtrazione/scarico malfunzionante (B040), condition_maintenance guarnizioni (B044). |
| 16 | power supply, safety | no | Alimentazione: requisito del circuito prima dell'installazione (B047, routine), safety su messa a terra/sovraccarico/elettricista. Nessun item core/extended. |
| 17 | power supply, safety | sì | Messa a terra: terra fisica <= 5 Ohm (routine B051), cavo o spina danneggiati (fault B055), dubbio sulla messa a terra (safety B054), prolunghe. |
| 18 | setup, safety | sì | Setup/unpacking (solo OCR): danni da trasporto (fault), precauzioni montaggio, pulizia specchi (condition_maintenance), riquadri accorpati. |
| 19 | setup, inventory | sì | Inventario componenti principali A-I; NOTICE e parti mancanti (fault). |
| 20 | setup, inventory | no | Inventario parti sfuse J-AA: trascritte nei componenti, item routine b19-1. |
| 21 | setup, site considerations | no | Requisiti del sito: routine e una safety. Nessun item diagnostico. |
| 22 | setup procedure | no | Sollevamento e posizionamento (procedura routine), livellamento, verifica sito. |
| 23 | setup procedure | sì | Installazione water chiller (procedura routine 7 passi), bolle d'aria nel tubo (condition_maintenance B074), requisito climi desertici >100F (routine B073). |
| 24 | setup procedure, safety | sì | Installazione pompa aria (procedura routine) e ventola di scarico: fault odore sgradevole, 3 safety. |
| 25 | setup procedure | no | Installazione ventola di scarico (procedura routine 8 passi), minimo 200 CFM, rete metallica. |
| 26 | setup procedure, test run | sì | Test Run passi 1-7, fault 'unusual problem during test run', 2 safety. |
| 27 | test run, component test | sì | Test Run passi 8-13: 4 test (finecorsa X, Y, interblocco porta, E-stop) con rimedio sostituzione; DANGER Class 4 accorpato in b14-1. |
| 28 | operation, safety | no | Inizio SECTION 4: panoramica operativa in 16 passi (routine), 2 WARNING e un NOTICE sulla formazione. Nessun contenuto diagnostico; nessun passo del Test Run su questa pagina. |
| 29 | software, controls | no | Descrizione dell'interfaccia RDCam (Figure 31): solo descrizione di comandi software, nessun item. |
| 30 | software, operation | no | Procedure software: importazione artwork e salvataggio .RD (passi 1-5). Routine, non diagnostico. |
| 31 | software, operation | no | Salvataggio .RD passi 6-13 (impostazioni Layer Parameter, Device USB:Auto). Routine. |
| 32 | operation, safety | sì | Panoramiche chiller/pompa aria/aspiratore; allarme di surriscaldamento del chiller (soglia 122F/50C) con rimedi -> fault; ispezione pezzo (materiali vietati, corpi estranei). |
| 33 | operation, controls | no | Trasferimento file .RD passi 1-4; layout pannello comandi (Figure 37), schermate di avvio. Routine. |
| 34 | operation | no | Trasferimento file .RD passi 5-10 con schermate menu. Routine. |
| 35 | operation, safety, error codes | sì | Fine trasferimento (passi 11-13) con messaggio 'Name Over Lap' (codice con solo significato); inizio Operating Laser con DANGER laser classe 4 e 2 WARNING. |
| 36 | operation, safety | no | Operating Laser passi 4-14 (scelta tavolo, focale, selezione file) e NOTICE spazio testa-pezzo. Routine. |
| 37 | operation | sì | Operating Laser passi 15-29; amperometro oltre il valore nominale causato da guasto imminente del tubo o guasti elettrici -> fault (2 cause). |
| 38 | operation, safety | sì | Setting Focal Length (solo testo OCR p38.o1): procedura 6 passi (~9mm, focus gauge 53mm), DANGER ripetuto; distanza eccessiva/insufficiente -> fuoco diffuso, tagli scadenti, fumo -> 2 fault. |
| 39 | operation | no | Worktime preview (5 passi) e TrackFrame passi 1-2. Routine. |
| 40 | operation, error codes | sì | TrackFrame passi 3-6; errori 'XSlop Over', 'YSlop Over', 'Frame slop' = immagine fuori dall'area di lavoro, ripetere passi 1-6 -> 3 error_code. |
| 41 | accessories, safety | no | SECTION 5 Accessories: codici ricambio T30342 tubo laser, T30334 tavolo honeycomb, T30337 chiller, T30336 aspiratore, T30335 pompa aria; WARNING accessori non approvati. |
| 42 | maintenance schedule, safety, cleaning | sì | SECTION 6: WARNING scollegare alimentazione; schedule Ongoing (4 condizioni di arresto), Daily, Weekly, Monthly; Cleaning & Protecting (2 NOTICE); Lubrication (olio ISO 10). |
| 43 | cleaning, lubrication, safety | no | Pulizia cabinet, superfici alberi/guide, ispezione parti mobili prima/dopo ogni uso (routine B139), inizio pulizia/lubrificazione assi X/Y. Safety e routine, non diagnostica. |
| 44 | lubrication, adjustment | sì | Lubrificazione assi X/Y passi 3-9; fermo del motore passo-passo se mosso troppo veloce (fault); gioco testa su asse X -> eccentrici (fault); descrizione sollevamento Z. |
| 45 | lubrication, cleaning | sì | Pulizia/lubrificazione sollevamento Z (contaminazione pesante -> condition); Belts & Pulleys, NOTICE cinghie, inizio ispezione cinghie. |
| 46 | maintenance, laser components | sì | Ispezione cinghie passi 3-6 (deflessione uguale o binding; crepe/denti danneggiati -> sostituzione p53; accumulo sui denti -> tacche nel taglio); manutenzione tubo laser e introduzione ottiche (descrittive, nessun rimedio stampato). |
| 47 | cleaning, safety | no | Linee guida pulizia ottiche (divieti), Cleaning Laser Optics Method 1 passi 1-4. Solo safety e routine (i rami condizionali sono a p48). |
| 48 | cleaning | sì | Method 1 passi 5-6 e Method 2 (Drop and Drag): macchie residue -> ripetere; dopo seconda pulizia -> sostituire ottiche (4 condition_maintenance). |
| 49 | maintenance | sì | Water Chiller System (6 passi: schermo radiatore, tubi, acqua/alghe, bolle, livello 3-6") e Cleaning Air Pump Filter (7 passi: filtro, tubi/coperchio). |
| 50 | maintenance, storage | sì | Exhaust Fan (8 passi: perdite condotti, schermi) e Storing Machine (svuotare l'acqua dal tubo, cassa con essiccanti, manutenzione prima del rimessaggio). |
| 51 | troubleshooting table | sì | Tabella Electrical: 2 sintomi, 9+5=14 coppie causa-rimedio. |
| 52 | troubleshooting table | sì | Tabella Operations: 3 sintomi, 2+12+6=20 coppie causa-rimedio. |
| 53 | repair procedure, component test | sì | Regolazione cinghie sincrone: linee guida tensione, test deflessione X 6mm e Y 8mm. |
| 54 | repair procedure | sì | Solo OCR: Z-axis belt (non regolabile, squadratura tavola), sostituzione cinghie X/Y, inizio rimozione tubo laser (passi 1-3). |
| 55 | repair procedure, safety | sì | Rimozione tubo laser passi 4-14 con avvertenze (acqua residua, spout di vetro, selle). |
| 56 | repair procedure, safety | sì | Installazione tubo laser passi 1-7, figura 87 compartimento. |
| 57 | repair procedure, safety | sì | Installazione passi 8-16: tubi acqua, priming, bolle d'aria, livello serbatoio. |
| 58 | repair procedure, safety | sì | Installazione passi 17-24: cavi anodo/catodo, gap 1-1 1/2", selle; avviso chiller OFF. |
| 59 | repair procedure, safety | sì | Allineamento raggio: DANGER classe 4, percorso con 3 specchi, passi 1-11 (impostazioni potenza). |
| 60 | repair procedure, component test | sì | Allineamento passi 12-16: gauge, verifica Pulse angolo superiore sinistro, figura 97/98. |
| 61 | repair procedure, component test | sì | Allineamento passi 17-25: regolazione Mirror #1, angolo inferiore sinistro, mirror alignment gauge. |
| 62 | repair procedure, component test | sì | Allineamento passi 26-35: angolo inferiore destro, Mirror #2, chiusura. |
| 63 | repair procedure, safety | sì | Solo OCR: sostituzione specchi e focus lens. |
| 64 | wiring, safety | sì | Introduzione Sezione 8 e riquadro WARNING 'Wiring Safety Instructions' (7 avvertenze safety + WIRE/COMPONENT DAMAGE come condition_maintenance B243); legenda colori. |
| 65 | wiring diagram | no | Schema elettrico: controller ST908(EC), DRO, USB, driver passo-passo X/Y 2DM420, motori X/Y, finecorsa X/Y, filtro FT127-10, arresto d'emergenza, leakage protection, presa 110V, trasformatore TL-150D-B, amperometro, tubo laser, alimentatore HV WK60S, LED worklight, proximity switch, water protection. Solo inventario; richiamo 'READ ELECTRICAL SAFETY ON PAGE 62' (= PDF 64). |
| 66 | electrical components, photos | no | Foto: Fig.107 componenti del quadro elettrico (pannello Light/USB, controller, trasformatore, driver, filtro, alimentatore HV), Fig.108 controller, Fig.109 driver X/Y. Solo inventario. |
| 67 | electrical components, photos | no | Foto: Fig.110 alimentatore HV (etichetta DANGER leggibile in foto -> b67-1), Fig.111 pulsante emergenza, Fig.112 filtro, Fig.113 digital readout, Fig.114 trasformatore (etichetta 115/230V leggibile -> b67-2). Solo sicurezza. |
| 68 | exploded view, parts | no | Esploso 'Main' (cabinato, porte, tubo laser, cabinet di estensione), rif. 101-149. Solo inventario. |
| 69 | parts list | no | Main Parts List, rif. 101-149 (manca 119). Trascritto nell'inventario tranne la viteria generica. |
| 70 | exploded view, parts | no | Esploso 'Gantry & Optics' con riquadri per leadscrew assembly (202), mirror assembly front (207), rear (232) e laser head (222). Solo inventario. |
| 71 | parts list | no | Gantry & Optics Parts List, rif. 201-252 con sottoassiemi 202-x, 207-x, 222-x, 232-x. Trascritto nell'inventario tranne la viteria generica. |
| 72 | parts, photos | no | Foto 'Electrical & Accessories' rif. 300-338 (quadro elettrico, chiller, ventilatore, pompa aria, accessori/attrezzi). Solo inventario. |
| 73 | parts list | no | Electrical & Accessories Parts List, rif. 300-317 e 318-338 (mancano 335-337). Trascritto nell'inventario. |
| 74 | labels, parts list, safety | sì | Labels & Cosmetics rif. 400-409 con disegni delle etichette (testi 404-407 leggibili -> item safety) e WARNING sulla sostituzione delle etichette staccate/illeggibili (condition_maintenance b74-1): diagnostica. |
| 75 | command tree, controls | no | Appendice: Command Tree (Status Screen, Main Menu, File Management, Job Setup, Time Preview, Format, Speed Adjust). Nessun comando diagnostico/errore; solo la frase 'check www.grizzly.com ... if this one seems out of date' (routine b75-1). |
| 76 | command tree, controls | no | Command Tree (Cont.): Min/Max Power, Root Setup (Axis Reset, Manual Set, Laser Set, Origin Setup, Language, Set as/Default Fact Para 'N/A Factory Setup Only'). Nessun codice o comando diagnostico. |
| 77 | blank | no | Pagina bianca (immagine vuota, nessun testo). |
| 78 | blank | no | Pagina bianca (immagine vuota, nessun testo). |
| 79 | warranty | no | Warranty & Returns: testo legale/amministrativo e QR registrazione garanzia. Non item. |
| 80 | back cover, advertisement | no | Quarta di copertina (solo immagine): logo grizzly.com TOOL WEBSITE, 'Buy Direct and Save with Grizzly', 'ORDER 24 HOURS A DAY! 1-800-523-4777', loghi carte di credito. Nessun contenuto tecnico. |
