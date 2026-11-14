# Confronto gold v2 con gold v1: Grizzly G0872

Il gold v2 è fatto da un'AI (annotatore, verificatore e confronto con v1); manca una revisione umana.
Il gold v1 è manuale (Fabio Daniele, 2026-09-28) e copre 20 pagine PDF (9, 26, 27, 32, 35, 37, 39, 40, 42, 46,
48-52, 54, 60-62, 64). Gold v1 letto in sola lettura; dove v1 e v2 differiscono ha deciso il PDF (testo delle
pagine 40, 52, 61 ricontrollato).

## Conteggi

- Rami v1: 66 (164 claim).
- Confermati: 56.
- Corretti (v2 diverso e supportato dal PDF): 10 (R1, R3, R4, R6, R10, R11, R19, R20, R52, R66).
- Aggiunti a v2 dopo il confronto: 0.
- Non supportati dal PDF: 0.
- Elementi v2 senza controparte v1: 202 (su 245 rami + 28 procedure)
  - safety_precaution: 109
  - routine: 63 (43 rami + 20 procedure routine)
  - fault: 12
  - condition_maintenance: 10
  - procedure (extended): 6
  - diagnostic_test: 2

Il gold v2 non è stato modificato: ogni ramo v1 ha una controparte in v2 e nessuna differenza dà ragione a v1.

Regola usata: differenze solo di divisione delle azioni (v1 separa "Inspect/replace" o "A or B" in più azioni,
v2 tiene la frase come stampata o aggiunge il controllo esplicito prima della riparazione) contano come
confermato. "Corretto" = v2 diverso per struttura del ramo, causa, azioni o categoria.

## Rami v1

| v1 | problema (breve) | v2 | esito | nota |
|---|---|---|---|---|
| R1 | Codice "Frame Slop" | B110 | corretto | v1 solo significato (p9); v2 unisce p9 e p40 e aggiunge l'azione stampata a p40 "repeat Steps 1–6" (TrackFrame, P013). |
| R2 | Codice "Name Over Lap" | B098 | confermato | Solo significato, nessuna azione, come v1. |
| R3 | Codice "XSlop Over" | B108 | corretto | Come R1. |
| R4 | Codice "YSlop Over" | B109 | corretto | Come R1. |
| R5 | Problema insolito durante il test run | B084 | confermato | |
| R6 | Test limit switch: la testa si muove | B087, B088 | corretto | v1 un ramo per i due assi; v2 un test per asse x e uno per asse y (p27 "Repeat Steps 8–9 on y-axis"). |
| R7 | Test interlock sportello: il laser pulsa | B089 | confermato | v2 come diagnostic_test con condizione "If the laser does audibly beep". |
| R8 | Test Emergency Stop: la macchina non si spegne | B090 | confermato | Come R7. |
| R9 | Allarme surriscaldamento chiller | B094 | confermato | v2 mette le condizioni stampate ("regularly", "extreme heat"). |
| R10 | Amperometro oltre il valore in mA | B104, B105 | corretto | Le due cause stampate (guasto del tubo laser, guasti elettrici) in due rami v2; v1 una sola causa unita. |
| R11 | Errori XSlop/YSlop/Frame slop durante TrackFrame | B108, B109, B110 + P013 | corretto | v1 un ramo con i passi del TrackFrame come azioni; v2 un ramo per codice con "repeat Steps 1–6" e i passi nella procedura P013 (p39-40). |
| R12 | Bulloni di montaggio allentati | B113 | confermato | v2 aggiunge il controllo "Observe" prima di "Shut down". |
| R13 | Ottiche laser danneggiate | B114 | confermato | Come R12. |
| R14 | Cavi usurati o danneggiati | B115 | confermato | Come R12. |
| R15 | Altra condizione non sicura | B116 | confermato | Come R12. |
| R16 | Cinghie sinistra/destra con flessione diversa | B145 | confermato | v2 aggiunge il rinvio al controllo della flessione. |
| R17 | Gradino o tacca nel percorso di taglio | B146 | confermato | v1 due azioni, v2 una frase unica come stampata. |
| R18 | Cinghie con crepe o denti danneggiati | B144 | confermato | v2 aggiunge l'ispezione con torcia (p45). |
| R19 | Residui sulla lente/specchio (ottiche montate) | B157, B158 | corretto | v2 due rami: ripetere i passi 2–5; sostituire se restano dopo la seconda pulizia, con la causa stampata "permanently burned into surface". |
| R20 | Residui sulle ottiche smontate | B159, B160 | corretto | Come R19 (passi 2–4). |
| R21 | Griglia ventola radiatore ostruita | B162 | confermato | |
| R22 | Perdite in tubi e raccordi del chiller | B163 | confermato | "Repair or replace" in una azione in v2. |
| R23 | Acqua scolorita o con alghe | B164 | confermato | |
| R24 | Filtro in spugna bucato o strappato | B168 | confermato | |
| R25 | Tubo o coperchio filtro crepato | B169 | confermato | |
| R26 | Perdite nel condotto di scarico | B170 | confermato | "Patch or replace" in una azione in v2. |
| R27 | Tavola fuori squadra (cinghia asse Z allentata) | B215 | confermato | v2 separa il controllo con comparatore dalla rotazione delle viti. |
| R28 | Allineamento angolo in alto a sinistra (specchio 1) | B232 | confermato | Il posizionamento della testa è in `conditions` e in P026. |
| R29 | Allineamento angolo in basso a sinistra (specchi 1-2) | B233 | confermato | Come R28. |
| R30 | Allineamento angolo in basso a destra (specchi 2-3) | B235 | confermato | Come R28. |
| R31 | Non si avvia / Emergency Stop premuto o guasto | B177 | confermato | |
| R32 | Non si avvia / tensione o circuito errati | B178 | confermato | |
| R33 | Non si avvia / interruttore scattato o fusibile | B179 | confermato | "Reset ... or replace fuse" in una azione in v2. |
| R34 | Non si avvia / corto in pompa, chiller o ventola | B180 | confermato | |
| R35 | Non si avvia / cavi rotti o corrosi | B181 | confermato | |
| R36 | Non si avvia / massa del telaio | B182 | confermato | |
| R37 | Non si avvia / tubo laser guasto | B183 | confermato | |
| R38 | Non si avvia / alimentatore o controller | B184 | confermato | |
| R39 | Non si avvia / scheda computer | B185 | confermato | |
| R40 | Vibrazione / motore o componente allentato | B186 | confermato | |
| R41 | Vibrazione / cinghie o pulegge | B187 | confermato | |
| R42 | Vibrazione / montaggio sul banco | B188 | confermato | Tre alternative in una azione in v2, come stampate. |
| R43 | Vibrazione / pezzo allentato | B189 | confermato | Una azione in v2, come stampata. |
| R44 | Vibrazione / cuscinetti motore passo-passo | B190 | confermato | |
| R45 | Chiavetta non letta / formato errato | B191 | confermato | |
| R46 | Chiavetta non letta / file non salvato con RDCam | B192 | confermato | |
| R47 | Taglio scarso / errore CNC o percorso | B193 | confermato | |
| R48 | Taglio scarso / velocità o potenza errate | B194 | confermato | |
| R49 | Taglio scarso / fuoco non regolato | B195 | confermato | |
| R50 | Taglio scarso / laser storto | B196 | confermato | |
| R51 | Taglio scarso / percorso ostruito da fumo | B197 | confermato | |
| R52 | Taglio scarso / laser non taglia il pezzo | B198 | corretto | v1 senza azione; la cella 6 di p52 (t1.r3) stampa "Workpiece material beyond machine capability", annotata in v2. |
| R53 | Taglio scarso / kerf troppo largo | B199 | confermato | |
| R54 | Taglio scarso / vibrazione o gioco della testa | B200 | confermato | |
| R55 | Taglio scarso / pezzo che si muove | B201 | confermato | |
| R56 | Taglio scarso / dente di sega | B202 | confermato | |
| R57 | Taglio scarso / tubo laser guasto | B203 | confermato | |
| R58 | Taglio scarso / trasformatore, alimentatore, controller | B204 | confermato | |
| R59 | Tubo laser spento / chiller non raffredda | B205 | confermato | |
| R60 | Tubo laser spento / corto in pompe o ventola | B206 | confermato | |
| R61 | Tubo laser spento / alimentatore tubo | B207 | confermato | |
| R62 | Tubo laser spento / connessioni del tubo | B208 | confermato | |
| R63 | Tubo laser spento / impianto elettrico | B209 | confermato | |
| R64 | Tubo laser spento / tubo laser guasto | B210 | confermato | |
| R65 | Cavi o componenti danneggiati durante un lavoro | B243 | confermato | v2 come condition_maintenance. |
| R66 | Cablaggio diverso dal manuale | B238 | corretto | v2 classifica la nota di p64 come safety_precaution (nessun guasto della macchina) e aggiunge i due atti stampati: confrontare la data di fabbricazione e raccogliere matricola e data prima di chiamare. |

## Elementi v2 senza controparte v1

Quasi tutti sono su pagine che v1 non annota; quelli su pagine v1 sono avvertenze, routine o item che v1 non
aveva incluso.

- safety_precaution (109): B001 (p2); B006-B011 (p12); B012-B025, B027, B028 (p13); B029-B038 (p14);
  B039, B041-B043, B045, B046 (p15); B048-B050 (p16); B052-B054, B056 (p17); B057, B059 (p18); B068 (p21);
  B079-B081 (p24); B085, B086 (p26); B091, B093 (p28); B095-B097 (p32); B099-B101 (p35); B102 (p36); B111 (p41);
  B112, B129-B131 (p42); B132-B136, B138, B140 (p43); B152 (p46); B153-B156 (p47); B167 (p49); B174 (p50);
  B216 (p54); B217-B220 (p55); B221 (p56); B225-B227 (p57); B230 (p58); B231 (p59); B234 (p62); B236, B237 (p63);
  B239-B242, B244-B246 (p64); B247 (p66); B248 (p67); B250-B253 (p74).
- routine, rami (43): B047 (p16); B051 (p17); B061 (p19); B064-B067, B069 (p21); B070, B071 (p22);
  B072, B073, B075 (p23); B076, B077 (p24); B082, B083 (p25); B103 (p37); B117-B123, B125-B128 (p42);
  B137, B139 (p43); B147-B149 (p46); B161, B165, B166 (p49); B172, B173, B175, B176 (p50); B224 (p57); B254 (p75).
- routine, procedure (20): P001-P012 (p22-39: installazione, test run, uso, RDCam, fuoco, preview);
  P014-P021 (p43-50: pulizia, lubrificazione, manutenzione chiller, pompa aria, scarico).
- fault (12): B040 (p15), B055 (p17), B058 (p18), B062, B063 (p19), B078 (p24), B106, B107 (p38, distanza di
  fuoco), B141, B142 (p44), B211, B212 (p53, tensione cinghie).
- condition_maintenance (10): B026 (p13), B044 (p15), B060 (p18), B074 (p23), B124 (p42), B143 (p45), B171 (p50),
  B222 (p57), B229 (p58), B249 (p74).
- procedure, extended (6): P022 regolazione cinghie (p53), P023 sostituzione cinghie (p54), P024 rimozione tubo
  laser (p54-55), P025 installazione tubo laser (p56-58), P027 specchi, P028 lente di focalizzazione (p63).
- diagnostic_test (2): B213, B214 (p53, flessione cinghie asse X e Y).

P013 (TrackFrame) e P026 (allineamento del raggio) hanno controparte parziale in v1: v1 copia i loro passi come
azioni di R11 e R28-R30.
