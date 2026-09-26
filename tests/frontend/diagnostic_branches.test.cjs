const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const test = require('node:test');
const context = { window: { KGFoundation: { state: {}, escapeHtml: String, t: x => x } } };
vm.createContext(context);
vm.runInContext(fs.readFileSync('frontend/app/detail.js', 'utf8'), context);
const kg = context.window.KGFoundation;

test('chains keep separate actions and conditions for a shared failure node', () => {
  const nodes = ['failure', 'symptom-a', 'symptom-b', 'action-a', 'action-b'].map(node_id => ({ node_id }));
  const relations = [
    ['MAY_INDICATE', 'symptom-a', 'failure', 'a'],
    ['MAY_INDICATE', 'symptom-b', 'failure', 'b'],
    ['RESOLVED_BY', 'failure', 'action-a', 'a'],
    ['RESOLVED_BY', 'failure', 'action-b', 'b'],
  ].map(([relation_type, from_id, to_id, branch_lineage_id]) => ({ relation_type, from_id, to_id, branch_lineage_id }));
  const model = { nodiPerId: new Map(nodes.map(n => [n.node_id, n])), legamiPerNodo: new Map([['failure', relations]]), grafo: { diagnostic_records: [
    { record: { branch_lineage_id: 'a', conditions: [{ text: 'Only if voltage is below 5 V', applies_to: 'action', step_index: 0 }] } },
  ] } };
  const chains = kg.catenePerCausa(model, nodes[0]);
  assert.equal(chains.length, 2);
  assert.equal(chains[0].indizi[0].node_id, 'symptom-a');
  assert.equal(chains[0].azioni.length, 1);
  assert.equal(chains[0].azioni[0].node_id, 'action-a');
  assert.equal(chains[1].azioni[0].node_id, 'action-b');
  assert.match(kg.condizioniCatena(chains[0]), /Only if voltage is below 5 V/);
  assert.equal(kg.condizioniCatena(chains[1]), '');
  relations.pop();
  assert.equal(kg.catenePerCausa(model, nodes[0])[1].azioni.length, 0);
});
