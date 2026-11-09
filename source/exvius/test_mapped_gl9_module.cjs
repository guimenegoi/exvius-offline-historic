const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = __dirname;
const BASE = 0x400023000000n;
let correctSignatures = true;
let maps = [
  '400020800000-400022c49000 r--p 00000000 103:02 100 /data/app/lib/arm64/libexviustest.so',
  '400023000000-400026620000 r--p 00000000 103:02 101 /data/app/lib/arm64/libgame.so',
  '400026621000-40002699a000 rw-p 03620000 103:02 101 /data/app/lib/arm64/libgame.so',
].join('\n');

class Pointer {
  constructor(value) {
    this.value = typeof value === 'bigint' ? value : BigInt(value);
  }
  add(offset) {
    return new Pointer(this.value + BigInt(offset));
  }
  readU32() {
    if (!correctSignatures) return 0;
    if (this.value === BASE) return 0x464c457f;
    if (this.value === BASE + 0x1e5b51cn) return 0xfc170fec;
    if (this.value === BASE + 0x1e49e34n) return 0xd10283ff;
    return 0;
  }
  toString() { return '0x' + this.value.toString(16); }
}
const notes = [];
globalThis.Process = {arch: 'arm64'};
globalThis.File = {readAllText(file) {
  assert.equal(file, '/proc/self/maps');
  return maps;
}};
globalThis.ptr = value => new Pointer(value);
globalThis.Module = {getGlobalExportByName(name) {
  if (name === '__dynamic_cast') return new Pointer(0x10000n);
  throw Error('Not exported');
}};

(async () => {
  const exportsSource = fs.readFileSync(path.join(root, 'gl9_export_offsets.js'), 'utf8');
  const {GL9_OFFSETS} = await import(
    'data:text/javascript;base64,' + Buffer.from(exportsSource).toString('base64'));
  globalThis.__gl9Offsets = GL9_OFFSETS;
  assert(Object.keys(GL9_OFFSETS).length >= 400);
  for (const prefix of ['_ZN13GachaTopScene', '_ZN9GateScene', '_ZN9HomeScene']) {
    assert(Object.keys(GL9_OFFSETS).some(name => name.startsWith(prefix)),
      'Missing generated runtime prefix: ' + prefix);
  }

  const helperSource = fs.readFileSync(path.join(root, 'mapped_game_module.js'), 'utf8')
    .replace("import { GL9_OFFSETS } from './gl9_export_offsets.js';",
      'const GL9_OFFSETS = globalThis.__gl9Offsets;');
  const {findMappedGameModule} = await import(
    'data:text/javascript;base64,' + Buffer.from(helperSource).toString('base64'));
  const module = findMappedGameModule(message => notes.push(message));
  assert(module);
  assert.equal(module.name, 'libgame.so');
  assert.equal(String(module.base), '0x400023000000');
  assert.equal(String(module.getExportByName('_ZN10TitleScene9setLayoutEv')),
    '0x400024e5b51c');
  assert(String(module.getExportByName('_ZN9HomeScene9setLayoutEv')).startsWith('0x4000'));
  assert.equal(String(module.getExportByName('__dynamic_cast')),
    String(new Pointer(BASE + 0x2dba408n)), 'C++ RTTI cast is exported by pinned libgame');
  assert.equal(String(module.getExportByName('_ZN20TfaEventInfoResponse9readParamEiiPKcS1_b')),
    String(new Pointer(BASE + 0x193d8d8n)),
    'Dynamically named response reader must be present');
  assert.equal(module.findExportByName('_ZNNotRealFnEv'), null);
  assert.throws(() => module.getExportByName('_ZNNotRealFnEv'), /GL9 mapped export missing/);
  assert(notes.some(note => note.includes('STARTUP_MAPPED_GAME_READY')));

  globalThis.Process.arch = 'x64';
  assert.equal(findMappedGameModule(), null, 'No fallback for an x86 agent');
  globalThis.Process.arch = 'arm64';
  correctSignatures = false;
  assert.equal(findMappedGameModule(message => notes.push(message)), null,
    'Reject unrecognized/modified clients');
  assert(notes.some(note => note.includes('STARTUP_MAPPED_GAME_SIGNATURE_MISMATCH')));
  correctSignatures = true;
  maps = '400020800000-400022c49000 r--p 00000000 /data/app/lib/arm64/libexviustest.so';
  assert.equal(findMappedGameModule(), null, 'Must wait until libgame is mapped');
  globalThis.File.readAllText = () => {throw Error('unavailable');};
  assert.equal(findMappedGameModule(), null, 'Unavailable memory map is not an error');
  console.log('Mapped GL9 module: pinned signatures, correct addresses, imports and fail-closed paths passed');
})().catch(error => {console.error(error); process.exitCode = 1;});
