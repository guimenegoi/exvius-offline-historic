const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

(async () => {
  const source = fs.readFileSync(path.join(__dirname, 'title_menu.js'), 'utf8');
  const {applyHistoricalStatus, refreshHistoricalStatus} = await import(
    'data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
  // These are exported symbols of the pinned Global 9.0.0 libgame.so.
  // Every native UI predicate must use the same global feature projection,
  // not a separate list of 2024 visibility flags.
  const native = fs.readFileSync(path.join(__dirname, 'android_test.js'), 'utf8');
  for (const feature of ['panel_quest', 'expedition', 'modern_event_modes',
                         'emblem_event', 'comeback_quest']) {
    assert.match(native, new RegExp("'" + feature + "'"), feature + ' missing native hook');
  }
  assert.match(native, /HISTORIC_HOME_ICON feature=/);
  const notes = [];
  applyHistoricalStatus({historical_preview: true, historical_month: '2016-06',
    historical_features: {arena: false, colosseum: true, expedition: false}}, x => notes.push(x));
  assert.equal(globalThis.__EXVIUS_HISTORICAL_PREVIEW__, true);
  assert.equal(globalThis.__EXVIUS_HISTORICAL_FEATURES__.arena, false);
  assert.equal(globalThis.__EXVIUS_HISTORICAL_FEATURES__.colosseum, true);
  assert.match(notes.at(-1), /month=2016-06/);
  const bridge = (name, sig, args) => {
    assert.equal(name, 'titleAction');
    assert.equal(args[0], 'status');
    return JSON.stringify({historical_preview: true, historical_month: '2016-07',
      historical_features: {arena: false, expedition: false}});
  };
  assert.equal(refreshHistoricalStatus(bridge).historical_month, '2016-07');
  assert.equal(globalThis.__EXVIUS_HISTORICAL_PREVIEW__, true);
  assert.equal(globalThis.__EXVIUS_HISTORICAL_FEATURES__.colosseum, undefined);
  const unavailable = refreshHistoricalStatus(() => { throw Error('Android game is not ready'); },
    x => notes.push(x));
  assert.equal(unavailable, null);
  assert.equal(globalThis.__EXVIUS_HISTORICAL_PREVIEW__, true,
    'A transient bridge error does not clear a previously validated historic save');
  applyHistoricalStatus({historical_preview: false, historical_month: null});
  assert.equal(globalThis.__EXVIUS_HISTORICAL_PREVIEW__, false);
  assert.equal(globalThis.__EXVIUS_HISTORICAL_FEATURES__, null);
  console.log('Historical status is re-read and stays consistent across Title and Home.');
})().catch(error => {console.error(error);process.exitCode=1});
