const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { runInNewContext } = require('node:vm');
const { test } = require('node:test');
const source = readFileSync('frontend/app.js', 'utf8');
const helper = source.slice(source.indexOf('function escapeHtml'), source.indexOf('document.addEventListener'));
const code = source.slice(source.indexOf('    let isAnalyzing'), source.indexOf('    function renderCompatibilityResults'));

test('only one compatibility request runs at a time', async () => {
  let resolveFetch, calls = 0;
  const rendered = [];
  const ctx = { jdInput: { value: 'job' }, analyzeBtn: {}, analysisResults: {},
    renderCompatibilityResults: value => rendered.push(value),
    fetch: () => { calls++; return new Promise(resolve => { resolveFetch = resolve; }); } };
  const run = runInNewContext(`${helper}\n${code}\nrunCompatibilityAnalysis`, ctx);
  const pending = run();
  assert.equal(ctx.analyzeBtn.disabled, true);
  await run();
  assert.equal(calls, 1);
  resolveFetch({ ok: true, json: async () => ({ compatibility_score: 42 }) });
  await pending;
  assert.equal(rendered[0].compatibility_score, 42);
  assert.equal(ctx.analyzeBtn.disabled, false);
});

test('analysis control is restored after failure', async () => {
  const ctx = { jdInput: { value: 'job' }, analyzeBtn: {}, analysisResults: {},
    fetch: async () => { throw new Error('offline'); } };
  await runInNewContext(`${helper}\n${code}\nrunCompatibilityAnalysis`, ctx)();
  assert.equal(ctx.analyzeBtn.disabled, false);
  assert.match(ctx.analysisResults.innerHTML, /offline/);
});
