const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { test } = require('node:test');

test('activity section links to profiles instead of inventing contribution counts', () => {
  const html = readFileSync('frontend/index.html', 'utf8');
  const script = readFileSync('frontend/app.js', 'utf8');
  assert.match(html, /https:\/\/github.com\/Ayushdevo/);
  assert.match(html, /https:\/\/www.kaggle.com\/ayushtiwariiitg/);
  assert.doesNotMatch(html, /1,842 commits|342 kernels/);
  assert.doesNotMatch(script, /function generateHeatmap|No.*contributions.*on/);
});
