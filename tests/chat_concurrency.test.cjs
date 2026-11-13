const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { runInNewContext } = require('node:vm');
const { test } = require('node:test');
const source = readFileSync('frontend/app.js', 'utf8');
const code = source.slice(source.indexOf('    let isSendingMessage'), source.indexOf('    function appendMessage('));

test('overlapping sends are suppressed and controls recover on success', async () => {
  let resolveFetch, calls = 0;
  const sent = [];
  const ctx = {
    chatInput: { value: 'first' }, sendBtn: {}, clearChatBtn: {}, sessionId: 's',
    chatMessages: { scrollTop: 0, scrollHeight: 1 },
    appendMessage: (role, value) => sent.push([role, value]),
    appendTypingIndicator: () => ({ remove() {} }),
    fetch: () => { calls++; return new Promise(resolve => { resolveFetch = resolve; }); },
  };
  const send = runInNewContext(`${code}\nsendMessage`, ctx);
  const first = send();
  assert.equal(ctx.sendBtn.disabled, true);
  assert.equal(ctx.clearChatBtn.disabled, true);
  ctx.chatInput.value = 'second';
  await send();
  assert.equal(calls, 1);
  resolveFetch({ ok: true, json: async () => ({ reply: 'answer' }) });
  await first;
  assert.deepEqual(sent, [['user', 'first'], ['assistant', 'answer']]);
  assert.equal(ctx.sendBtn.disabled, false);
  assert.equal(ctx.clearChatBtn.disabled, false);
});

test('controls recover when the request fails', async () => {
  const ctx = { chatInput: { value: 'hello' }, sendBtn: {}, clearChatBtn: {}, sessionId: 's',
    chatMessages: {}, appendMessage() {}, appendTypingIndicator: () => ({ remove() {} }),
    fetch: async () => { throw new Error('offline'); } };
  await runInNewContext(`${code}\nsendMessage`, ctx)();
  assert.equal(ctx.sendBtn.disabled, false);
  assert.equal(ctx.clearChatBtn.disabled, false);
});
