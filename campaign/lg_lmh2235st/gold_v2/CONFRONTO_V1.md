# Confronto del gold v2 con il gold v1 – LG LMH2235ST

Il gold v2 è fatto da un'AI (Claude Opus 5.5, coordinato da Claude Fable 5.2); anche questo confronto è fatto da un'AI.
Il gold v1 (umano, 74 rami su 24 pagine: 2, 11-33) non è stato modificato. Dove v1 e v2 differiscono ha deciso il PDF.

## Conteggi

- Rami v1: 74
- Confermati: 47
- Corretti (v2 diverso e sostenuto dal PDF): 25
- Aggiunti a v2 dopo il confronto: 2 (B118, B119)
- Non supportati dal PDF: 0

La maggior parte dei 'corretti' è di granularità: v2 annota un ramo per ogni percorso del flowchart che arriva a una
casella d'azione, mette le liste di passi nelle `procedures` e divide i riquadri di sicurezza per paragrafo.
Unica differenza di contenuto: p21 passo 11 (diodo AT), dove v2 segue la logica stampata ('out of range? No -> Replace').

Elementi v2 senza controparte v1: 46
- safety_precaution: 28
- routine: 2
- fault: 2
- diagnostic_test: 3
- procedure: 11

## Rami v1

| v1 | problema | v2 | esito | nota |
|---|---|---|---|---|
| R1 | Divieto di usare il forno a porta aperta | B002 | confermato |  |
| R2 | Controlli di sicurezza prima di attivare il magnetron | B003 | confermato |  |
| R3 | Allineamento/integrità magnetron, guida d'onda, guarnizione | B004, B007, B008 | corretto | v2 separa i tre paragrafi di p2 (B007 e B008 ripetuti a p5): granularità |
| R4 | Componenti difettosi o mal regolati | B005 | confermato |  |
| R5 | Controllo fuga microonde (norma federale) | B006 | confermato |  |
| R6 | Forno acceso a vuoto (p11) | B118 | aggiunto a v2 | v2 non aveva la precauzione d'uso A di p11; il PDF la riporta |
| R7 | Foglio di alluminio (p11) | B119 | aggiunto a v2 | v2 non aveva la precauzione d'uso B di p11; il PDF la riporta |
| R8 | Trial operation dopo installazione | P002 | corretto | in v2 è una procedura routine (passi A-G), non un ramo |
| R9 | Alta tensione 4.000 V | B032 | confermato |  |
| R10 | Precauzioni fuga prima del servizio | B033, B034 | corretto | v2 divide prima/dopo l'alimentazione |
| R11 | Porta/interblocco non sicuri: non usare | B035 | corretto | v2 aggiunge le due verifiche "no defective parts" del PDF |
| R12 | Verifiche dopo la riparazione | B036 | confermato |  |
| R13 | Autodiagnosi sensore umidità/termistore | B028 | confermato |  |
| R14 | F-1 termistore PCB in corto | B029 | confermato |  |
| R15 | F-2 termistore PCB aperto | B030 | confermato |  |
| R16 | F-4 sensore umidità aperto/corto | B031 | confermato |  |
| R17 | Dead: termostati open/short | B037 | confermato |  |
| R18 | No key / not started: interruttore | B038 | confermato |  |
| R19 | O.L. non si accende a porta aperta | B039 | confermato |  |
| R20 | Not cooking / V.M., T.T.M. fermi | B040 | confermato |  |
| R21 | V.M., T.T.M. partono da soli | B041 | confermato |  |
| R22 | No Display: verifica e "Check PCB" | B113 | corretto | v2 segue il percorso fino all'azione "Replace the PCB"; "Check PCB" non è un esito |
| R23 | No Display: connettore PCB scollegato | B042 | confermato |  |
| R24 | No Display: fusibile senza continuità | B043 | confermato |  |
| R25 | No Display: filtro antidisturbo senza continuità | B044 | confermato |  |
| R26 | No Display: sostituire PCB | B045, B113, B114 | corretto | v2: un ramo per ciascuno dei 3 percorsi verso la casella 6 |
| R27 | Keypad: solo START/EZ-ON? -> Check PWB | B051, B052, B053 | corretto | "Check PWB, go to No. 4" è un rinvio: v2 prosegue fino alle azioni |
| R28 | Keypad: latch board (secondary switch) | B049 | confermato |  |
| R29 | Keypad: tensione door sensing <= 4 V | B050 | confermato |  |
| R30 | Keypad: connettore PCB | B051, B115 | corretto | due percorsi verso la stessa casella |
| R31 | Keypad: sostituire keypad | B052, B116 | corretto | due percorsi; casella stampata come domanda: ambiguous in v2 |
| R32 | Keypad: sostituire PCB | B053, B117 | corretto | due percorsi; uscita No della casella-domanda: ambiguous in v2 |
| R33 | No Heat: porta aperta/chiusa 3 volte | B054 | corretto | v2 aggiunge la causa dalla Note di p19 (Alternate explanation) |
| R34 | No Heat: continuità TAB1-TAB2 ("PCB no problem") | B055, B056, B057, B058, B059, B060, B061, B062, B063, B064 | corretto | senza azione: in v2 è un'ispezione dentro i percorsi, non un ramo |
| R35 | No Heat: D35 > 8 V -> Relay 2 | B055 | confermato |  |
| R36 | No Heat: D35 <= 8 V -> PCB | B056 | confermato |  |
| R37 | No Heat: latch board | B057 | confermato | v2 ambiguous: manca la freccia verso il passo 5 (p19-20) |
| R38 | No Heat: connettore trasformatore AT | B058 | confermato | ambiguous in v2 (stessa freccia mancante) |
| R39 | No Heat: resistenza trasformatore AT | B059 | confermato | ambiguous in v2 |
| R40 | No Heat: connettore condensatore AT | B060 | confermato | ambiguous in v2 |
| R41 | No Heat: resistenza condensatore AT | B061 | confermato | ambiguous in v2 |
| R42 | No Heat: connettore diodo AT | B062 | confermato | ambiguous in v2 |
| R43 | No Heat: resistenza diodo AT | B063 | corretto | p21 stampa "out of range? No -> Replace the diode": v2 segue la stampa (v1 la aveva corretta) |
| R44 | No Heat: connettore magnetron | B064 | confermato | ambiguous in v2 (percorso via 11 Yes) |
| R45 | Turntable: motore fermo -> sostituire | B066 | confermato |  |
| R46 | Turntable: lampada accesa a porta chiusa | B067 | confermato |  |
| R47 | Turntable: D37 / RY1 -> sostituire PCB | B068, B069 | corretto | v2: due percorsi (D37 No; D37 Yes e RY1 No) |
| R48 | Turntable: RY1 beep ("PCB No Problem") | B069 | corretto | senza azione: in v2 è un'ispezione dentro B069 |
| R49 | Turns on automatically: porta 3 volte | B065 | corretto | v2 aggiunge la causa dalla Note di p19 |
| R50 | Turns on automatically: latch board | B070 | confermato |  |
| R51 | Turns on automatically: sostituire motore piatto | B071 | confermato | ambiguous in v2 (rimedio stampato dopo domanda sulla lampada) |
| R52 | Turns on automatically: sostituire PCB | B072, B073, B074 | corretto | v2: tre percorsi (4 V No; D37 No; RY1 No) |
| R53 | Turns on automatically: RY1 beep ("PCB No Problem") | B074 | corretto | senza azione: in v2 è un'ispezione dentro B074 |
| R54 | Misura fuga microonde | B075, B077, B078, P003 | corretto | v2 separa procedura (P003), test (B075) e sicurezza (B077, B078) |
| R55 | Emissione > 5 mW/cm2 su forno certificato | B075 | corretto | in v2 sono azioni condizionate del test di fuga B075 |
| R56 | Forno funziona a porta aperta | B076 | confermato |  |
| R57 | Registrazione misure e taratura annuale | P004, B080 | corretto | in v2 procedura routine P004 più ramo routine B080 |
| R58 | Misura potenza d'uscita | P005 | corretto | in v2 procedura routine (nessun valore atteso né rimedio) |
| R59 | Regolazione interblocchi / latch board | P006, B081, B083 | corretto | v2: procedura P006 più test B081 (gioco) e B083 (sequenza) |
| R60 | Fuga dopo regolazione interblocchi | B084 | confermato |  |
| R61 | Test primary interlock switch | B085 | confermato |  |
| R62 | Test secondary interlock switch | B086 | confermato |  |
| R63 | Test monitor switch | B087, B088 | confermato | l'ultima azione v1 è in v2 il ramo di sicurezza B088 |
| R64 | Condizioni di sicurezza per i test componenti | B091, B092 | corretto | v2 divide nei due riquadri di p30 |
| R65 | Test trasformatore | B093 | confermato |  |
| R66 | Test magnetron | B094 | confermato |  |
| R67 | Test condensatore | B095 | confermato |  |
| R68 | Test diodo | B096 | confermato |  |
| R69 | Test Relay 2 | B097 | confermato |  |
| R70 | Test motore ventilazione | B098 | confermato |  |
| R71 | Test motore piatto | B099 | confermato |  |
| R72 | Test filtro antidisturbo | B100 | confermato |  |
| R73 | Test fusibile AT | B101 | confermato |  |
| R74 | Test touch key board e avvertenze | B102, B103 | corretto | v2 separa le avvertenze di servizio in B103 |

## Elementi v2 assenti in v1

Quasi tutti stanno su pagine che v1 non annotava (1, 3-10, 34-49). Quelli su pagine di v1 sono segnati con *.

- **safety_precaution** (28): B001, B009*, B010*, B011, B013, B014, B015, B016, B017, B018, B019, B020, B021, B022, B023, B024, B025, B026, B079*, B082*, B089*, B090*, B104, B105, B106, B110, B111, B112
- **routine** (2): B027, P001
- **fault** (2): B046*, B048*
- **diagnostic_test** (3): B107, B108, B109
- **procedure** (11): P008, P009, P010, P011, P012, P013, P014, P015, P016, P017, P018

Note: B046 e B048 sono i riquadri 'Dead' e 'No display' di p14; B079, B082, B089, B090 sono avvertenze
di p25, p27 e p29 che v1 non annotava a parte; B009, B010 sono gli ultimi paragrafi di sicurezza di p2.
