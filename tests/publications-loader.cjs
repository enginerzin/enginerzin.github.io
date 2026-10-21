const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const code = fs.readFileSync(path.join(root, 'assets/publications.js'), 'utf8');
async function load(data, ok = true) {
  const elements = Object.fromEntries(['publicationList','pubCount','pubSearch','pubType'].map(id => [id, {value:'', innerHTML:'', textContent:'', addEventListener(event, fn) {this[event] = fn;}}]));
  const requests = [];
  vm.runInNewContext(code, {document: {getElementById: id => elements[id]}, fetch: async url => {requests.push(url); return {ok, json: async () => data};}});
  await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(requests, ['assets/publications.json']);
  return elements;
}
(async () => {
  const unavailable = JSON.parse(fs.readFileSync(path.join(root, 'assets/publications.json')));
  let e = await load(unavailable);
  assert.match(e.pubCount.innerHTML, /not yet been verified/);
  assert.equal(e.publicationList.innerHTML, '');
  e = await load({}, false);
  assert.match(e.pubCount.innerHTML, /unavailable/);
  // Synthetic data checks loader behavior without posing as real publications.
  e = await load({publications:[{title:'Older',authors:['Example'],year:'2000',category:'Journal Articles'}, {title:'<Newest>',authors:['Sample'],year:'2025',category:'Conference and Workshop Papers'}]});
  assert.match(e.pubCount.textContent, /2 publications/);
  assert.ok(e.publicationList.innerHTML.indexOf('2025') < e.publicationList.innerHTML.indexOf('2000'));
  assert.match(e.publicationList.innerHTML, /&lt;Newest&gt;/);
  e.pubSearch.value = 'Example'; e.pubSearch.input();
  assert.match(e.pubCount.textContent, /1 publication shown/);
  e.pubSearch.value = ''; e.pubType.value = 'Conference and Workshop Papers'; e.pubType.change();
  assert.match(e.pubCount.textContent, /1 publication shown/);
  e.pubSearch.value = 'no match'; e.pubSearch.input();
  assert.match(e.publicationList.innerHTML, /No publications match/);
  console.log('Loader checks passed: local fetch, unavailable/error state, rendering, ordering, escaping, search, type filter, no matches.');
})().catch(error => {console.error(error); process.exitCode = 1;});
