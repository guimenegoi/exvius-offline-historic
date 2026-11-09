const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

(async () => {
  const source = fs.readFileSync(path.join(__dirname, 'home_carousel.js'), 'utf8');
  const {carouselItems, carouselRelease, carouselHit, homeMenuState} = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
  assert.deepEqual(homeMenuState(0, 0), {espers: {visible: true, open: false}, expedition: {visible: false, open: false}, competitive: null},
    'No owned Esper keeps its locked icon visible; a disabled Expedition feature stays hidden');
  assert.deepEqual(homeMenuState(0, 1).expedition, {visible: true, open: false},
    'Retail Expedition flag 1 means visible but locked');
  assert.deepEqual(homeMenuState(1, 2), {espers: {visible: true, open: true}, expedition: {visible: true, open: true}, competitive: null},
    'Owning the first Esper and the open Expedition flag enable their entries');
  const preview = {expedition: false, equipment_enhancement: false};
  assert.deepEqual(homeMenuState(0, 2, preview).expedition,
    {visible: false, open: false},
    '2016 policy hides Expedition even if the final client reports it open');
  assert.deepEqual(homeMenuState(0, 2, {expedition: true}).expedition,
    {visible: true, open: true},
    'After introduction, normal native Expedition story/unlock rules remain');
  const beforeArena = homeMenuState(1, 2, {arena: false, colosseum: true, expedition: false});
  assert.deepEqual(beforeArena.competitive,
    {name: 'Colosseum', open: true, sceneId: 11000},
    'The original Colosseum native entry, not Arena, opens in June 2016');
  const sinceNovember = homeMenuState(1, 2, {arena: true, colosseum: true, expedition: false});
  assert.deepEqual(sinceNovember.competitive,
    {name: 'Arena', open: true, sceneId: null},
    'Global November 2016 moves Colosseum under the new Arena entry');
  assert.deepEqual(homeMenuState(1, 2, {}).competitive,
    {name: 'Colosseum', open: false, sceneId: null},
    'Missing historical data never makes the competition mode usable');
  const initial = carouselItems(1, 3, 640);
  assert.equal(initial[1].x, 320, 'World starts centred');
  assert.equal(initial[1].scale, 1);
  assert.equal(initial[1].opacity, 255);
  assert.equal(initial[0].x, -24);
  assert.equal(initial[2].x, 664);
  assert.equal(initial[2].scale, 0.75);
  assert.equal(initial[2].opacity, 153);
  assert.deepEqual(carouselRelease(1, 5, 640), {position: 1, dragged: false}, 'Small tap jitter does not change focus');
  assert.deepEqual(carouselRelease(1, -70, 640), {position: 2, dragged: true}, 'A deliberate left drag advances one entry without opening it');
  assert.equal(carouselRelease(2, 180, 640).position, 1, 'Right drag returns to World');
  assert.equal(carouselRelease(1, -700, 640).position, 3, 'Long drags can cross two entries');
  for (const count of [4, 5, 6]) {
    for (const focus of [-8, -1, 0, 4, 7, 12]) {
      const selected = ((focus % count) + count) % count;
      const layout = carouselItems(focus, count, 640);
      assert.equal(layout[selected].x, 320, 'Both wrap directions retain one centred option');
      assert.equal(layout.filter(c => c.opacity === 255).length, 1);
    }
  }
  const halfway = carouselItems(1.5, 3, 640);
  assert.equal(halfway[1].scale, halfway[2].scale, 'Focus transfers continuously while dragging');
  const cards = [
    {name: 'Arena', order: 1900, box: {x: 62, y: 1000, w: 258, h: 210}},
    {name: 'World', order: 2000, box: {x: 320, y: 1000, w: 344, h: 280}},
    {name: 'Vortex', order: 1900, box: {x: 546, y: 1000, w: 210, h: 210}}
  ];
  assert.equal(carouselHit(cards, {x: 170, y: 1000}), cards[1], 'The visible foreground World owns its overlap with Arena');
  assert.equal(carouselHit(cards, {x: 510, y: 1000}), cards[2], 'The exposed Vortex preview can receive focus');
  assert.equal(carouselHit(cards, {x: 60, y: 1000}), cards[0]);
  assert.equal(carouselHit(cards, {x: 320, y: 800}), undefined);
  console.log('Home carousel drag, wrap, focus and tap-jitter checks passed.');
})();
