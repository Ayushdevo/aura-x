const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { runInNewContext } = require('node:vm');
const { test } = require('node:test');
const source = readFileSync('frontend/app.js', 'utf8');
const escapeCode = source.slice(source.indexOf('function escapeHtml'), source.indexOf('document.addEventListener'));
const chatCode = source.slice(source.indexOf('    function appendMessage('), source.indexOf('    function appendTypingIndicator('));
const analysisCode = source.slice(source.indexOf('    function renderCompatibilityResults('), source.indexOf('    // --- Interactive 3D Bot'));
const payload = '<img src=x onerror=alert(1)>';

test('chat messages escape user and assistant markup', () => {
  const chatMessages = { appendChild(el) { this.last = el; } };
  const document = { createElement() { return { classList: { add() {} }, innerHTML: '' }; } };
  const context = { document, chatMessages, payload };
  runInNewContext(`${escapeCode}\n${chatCode}\nappendMessage('user', payload + '\\nnext');`, context);
  assert.doesNotMatch(chatMessages.last.innerHTML, /<img/);
  assert.match(chatMessages.last.innerHTML, /&lt;img .*&gt;<br>next/);
});

test('compatibility output escapes model-provided text', () => {
  const analysisResults = { innerHTML: '' };
  const document = { getElementById() { return {}; } };
  const result = { fit_verdict: payload, matching_skills: [payload], skills_to_learn: [payload], strengths: [payload], gaps_analysis: payload, compatibility_score: 50 };
  runInNewContext(`${escapeCode}\n${analysisCode}\nrenderCompatibilityResults(result);`, { analysisResults, document, result, setTimeout() {} });
  assert.doesNotMatch(analysisResults.innerHTML, /<img/);
  assert.equal((analysisResults.innerHTML.match(/&lt;img/g) || []).length, 5);
});
