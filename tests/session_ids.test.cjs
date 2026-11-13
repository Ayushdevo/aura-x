const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { runInNewContext } = require('node:vm');
const { test } = require('node:test');
const source = readFileSync('frontend/app.js', 'utf8');
const helper = source.slice(source.indexOf('function getSessionId'), source.indexOf('document.addEventListener'));
const getSessionId = runInNewContext(`${helper}\ngetSessionId`);

test('generates a 128-bit session ID and reuses it', () => {
  let stored = null;
  let calls = 0;
  const storage = { getItem: () => stored, setItem: (_, value) => { stored = value; } };
  const crypto = { getRandomValues(bytes) { calls++; bytes.fill(171); return bytes; } };
  const id = getSessionId(storage, crypto);
  assert.match(id, /^sess_[0-9a-f]{32}$/);
  assert.equal(getSessionId(storage, crypto), id);
  assert.equal(calls, 1);
});

test('replaces a legacy predictable ID', () => {
  let stored = 'sess_short';
  const storage = { getItem: () => stored, setItem: (_, value) => { stored = value; } };
  const crypto = { getRandomValues(bytes) { bytes.fill(1); return bytes; } };
  assert.equal(getSessionId(storage, crypto), 'sess_' + '01'.repeat(16));
  assert.equal(stored, 'sess_' + '01'.repeat(16));
});
