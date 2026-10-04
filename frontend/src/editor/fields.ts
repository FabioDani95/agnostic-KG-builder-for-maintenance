import { tr } from "../i18n/i18n";
const LABELS: Record<string, string> = {
  name: "Nome",
  description: "Descrizione",
  instruction_text: "Istruzioni",
  code: "Codice",
  asset_type: "Tipo di macchina",
  brand: "Marca",
  model: "Modello",
  category: "Categoria",
  severity: "Gravità",
  material_context: "Contesto materiale",
  action_type: "Tipo di azione",
  action_kind: "Tipo di azione",
  related_measurements: "Misure associate",
  source_type: "Tipo di fonte",
  source_title: "Titolo della fonte",
  source_reference: "Riferimento della fonte",
  expected_outcome: "Risultato atteso",
  system: "Sistema",
};
export const fieldLabel = (name: string) =>
  tr(LABELS[name] ?? (name.endsWith("_id") ? "Identificativo" : name));
