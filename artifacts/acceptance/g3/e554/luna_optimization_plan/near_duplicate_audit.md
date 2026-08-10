# Audit dei near-duplicate Luna

Questo audit è un controllo offline di candidati, non una lista di merge da applicare. La revisione ha zero duplicati esatti dopo normalizzazione; lo script lessicale produce 40 coppie candidate, molte delle quali sono correttamente concetti parent/child. Le otto famiglie seguenti rendono evidente la necessità di canonicalizzazione globale e, allo stesso tempo, il rischio di un fuzzy merge aggressivo.

| Tipo | Variante A | Variante B | Disposizione preliminare | Motivo |
|---|---|---|---|---|
| Component | Linear Rail | Linear Rails | auto-merge candidate | variazione morfologica; verificare contesto/proprietà |
| Component | Gear Rack | Gear Racks | auto-merge candidate | variazione morfologica; verificare contesto/proprietà |
| Component | Fume Extractor | Laser Fume Extractor | adjudication | il secondo può essere un sottotipo/istanza più specifica |
| Component | Brass laser beam nozzle | Brass laser nozzle | contextual merge candidate | variante lessicale forte, ma richiede stessa identità/evidenza |
| CorrectiveAction | Contact qualified Eastman service personnel | Contact qualified service personnel | adjudication | istruzione simile, ma il vicinato delle FailureMode e il contesto possono differire |
| CorrectiveAction | Adjust Pause Plunger | Adjust pause plunger activation pressure | contextual merge candidate | stessa famiglia d'azione; verificare se il primo è più generico e quali relazioni/evidenze sostiene |
| CorrectiveAction | Increase fume extractor vacuum pressure | Increase Vacuum Pressure | contextual merge candidate | una variante è isolata; possibile duplicato, ma il contesto materiale è obbligatorio |
| FailureMode | Safety label damaged | Safety labels are damaged | contextual merge candidate | variazione morfologica quasi equivalente; verificare evidenza e relazioni distinte |

Altre coppie lessicali mostrano perché il token containment non può decidere: `Fume Extractor`/`Fume extractor filter`, `Diagnostic Cabinet`/`Diagnostic cabinet fans`, `Laser Pointer`/`Laser Pointer Cable`, `Tool Holder`/`Tool holder assembly`, `Theta Motor`/`Theta Motor Cable`. Sono assieme/parte o generico/specifico, non sinonimi automatici.

## Regola di accettazione

- stesso tipo è necessario ma non sufficiente;
- normalizzazione esatta o pura morfologia può essere auto-merge soltanto senza conflitti di proprietà, material context, evidenza o vicinato;
- parent/child, generico/specifico, condizioni diverse e azioni con semantica diversa non vengono fusi;
- i contextual candidate richiedono confronto di quote, anchor e archi incidenti;
- gli incerti rimangono distinti e diventano un solo item di adjudication per gruppo;
- dopo ogni merge si rieseguono domain/range, grounding, completezza, 8/8 gold e 0/3 pairing vietati.

Nessuno di questi nomi deve entrare nei prompt, nelle euristiche o nel codice di produzione: sono test di accettazione sulla baseline congelata.
