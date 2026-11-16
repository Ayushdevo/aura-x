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

test('resume data is rendered as text in all portfolio sections', () => {
  const elements = new Map();
  const document = { getElementById(id) {
    if (!elements.has(id)) elements.set(id, { innerHTML: '', style: {}, addEventListener() {} });
    return elements.get(id);
  } };
  const data = {
    skills: { languages: [payload], machine_learning_deep_learning: [], generative_ai_llm: [], data_engineering: [], deployment_tools: [] },
    experience: [{ company: payload, role: payload, duration: payload, location: payload, highlights: [payload] }],
    education: [{ institution: payload, degree: payload, duration: payload, location: payload, coursework: [payload] }],
    projects: [{ name: payload, date: payload, details: [payload], tech_stack: [payload] }],
    certifications: [payload], key_achievements: [payload], life_quotes: ['quote'],
  };
  const renderCode = source.slice(source.indexOf('    function renderResume('), source.indexOf('    loadPortfolioData();'));
  runInNewContext(`${escapeCode}\n${renderCode}\nrenderResume(data);`, { document, data, setInterval() {}, setTimeout() {} });
  for (const id of ['skill-languages', 'experience-list', 'education-list', 'projects-list', 'certifications-list', 'achievements-list']) {
    assert.doesNotMatch(elements.get(id).innerHTML, /<img/);
    assert.match(elements.get(id).innerHTML, /&lt;img/);
  }
});
