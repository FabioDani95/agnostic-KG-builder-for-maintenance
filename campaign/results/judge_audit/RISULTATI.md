# Revisione del giudice dei KPI: risultati

Revisore Fabio Daniele, 2026-09-29, circa 40 minuti, 40 coppie delle esecuzioni F
([foglio](REVISIONE_GIUDICE.md), [chiave](chiave_non_aprire.json)). Punteggio con
`scripts/kg_v3_judge_audit.py --score`. IC95 Wilson.

| Il giudice aveva detto | Coppie | Uguale per il revisore (U) | Errore del sistema (S) | Gold discutibile (G) |
| --- | --- | --- | --- | --- |
| diverse (rami mancati) | 32 | 7 = 22% [0,11; 0,39] | 21 = 66% [0,48; 0,80] | 4 = 12% [0,05; 0,28] |
| uguali (controllo) | 8 | 6 | 1 | 1 |

**Lettura.** La maggior parte dei rami mancati manca davvero: quando il giudice dice «diverso» ha
ragione circa due volte su tre. Sbaglia per difetto circa una volta su cinque, e nel controllo
sbaglia anche per eccesso una volta su otto: gli errori vanno in entrambe le direzioni, quindi
correggere il giudice cambierebbe il recall di poco. Il gold è discutibile in circa un caso su otto.
Sono 40 coppie: le proporzioni sono indicative.

**Errori del sistema (21), dalle note:**

- *Rimedio della causa vicina nelle celle con elenchi numerati* (Grizzly A008, A010, A022, A028, A039;
  ABB A017): la causa N viene collegata ai rimedi di un'altra causa della stessa riga. È la
  regressione delle tabelle di Grizzly nell'iterazione F.
- *Ramo sbagliato del diagramma* (LG A004, A024, A025, A037; A019 nel controllo): un'azione viene
  data all'esito di un'altra domanda o a un altro ramo del diagramma, oppure si perde la condizione del
  ramo (D35 sopra 8 V).
- *Test dei componenti letti come guasti* (LG A014, A030, A033; Haas A002): la tabella dà solo valori
  normali e una procedura di verifica; il grafo afferma un guasto («Suspected … fault», «avvolgimento a
  massa») che il manuale non dice. La regola 15 dell'iterazione F va rivista.
- *Assistenza condizionata e contesto* (Lincoln A021, A026, A040): l'assistenza «se i controlli non
  risolvono» legata al problema sbagliato o senza la sua condizione.
- *Passi mancanti di una procedura* (Grizzly A027, LG A009, A036, A038).

**Gold discutibile (4 più 1 nel controllo):** Graco A005 (il rimedio «Thin the material» appartiene alla
riga «No material output», non a «Speed of application too slow»); Grizzly A007 (perdite da cercare
trattate come già accertate); LG A003 e A020 (precauzioni di p. 2 trattate come problema); ABB A018
(il guasto dell'altro drive usato come problema). Il gold non è stato modificato.
