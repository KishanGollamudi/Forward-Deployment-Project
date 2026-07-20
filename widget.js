(function () {
  const style = document.createElement('style');
  style.textContent = `
    #ai-fab { position:fixed; bottom:24px; right:24px; z-index:9999; width:52px; height:52px;
      border-radius:50%; background:#3f51b5; color:#fff; border:none; cursor:pointer;
      font-size:24px; box-shadow:0 4px 12px rgba(0,0,0,0.3); display:flex; align-items:center; justify-content:center; }
    #ai-panel { position:fixed; bottom:88px; right:24px; z-index:9999; width:320px;
      background:#1e1e2e; border-radius:12px; box-shadow:0 8px 24px rgba(0,0,0,0.4);
      display:none; flex-direction:column; overflow:hidden; font-family:sans-serif; }
    #ai-panel.open { display:flex; }
    #ai-header { background:#3f51b5; color:#fff; padding:10px 14px; display:flex; align-items:center; gap:8px; font-weight:600; }
    #ai-header button { margin-left:auto; background:none; border:none; color:#fff; cursor:pointer; font-size:18px; line-height:1; }
    #ai-messages { flex:1; overflow-y:auto; padding:10px; display:flex; flex-direction:column; gap:8px; min-height:260px; max-height:300px; }
    .ai-msg { max-width:85%; padding:8px 12px; border-radius:12px; font-size:13px; line-height:1.4; word-break:break-word; }
    .ai-msg.user { align-self:flex-end; background:#3f51b5; color:#fff; border-bottom-right-radius:3px; }
    .ai-msg.bot  { align-self:flex-start; background:#2e2e42; color:#e0e0e0; border-bottom-left-radius:3px; }
    #ai-input-row { display:flex; padding:8px; gap:6px; background:#1e1e2e; }
    #ai-input { flex:1; background:#2e2e42; border:none; border-radius:8px; padding:8px 10px; color:#e0e0e0; font-size:13px; outline:none; }
    #ai-send { background:#3f51b5; border:none; border-radius:8px; color:#fff; padding:8px 12px; cursor:pointer; font-size:16px; }
    #ai-send:disabled { opacity:0.5; cursor:default; }
  `;
  document.head.appendChild(style);

  document.body.insertAdjacentHTML('beforeend', `
    <button id="ai-fab" title="AI Assistant">🤖</button>
    <div id="ai-panel">
      <div id="ai-header">
        <span>🤖</span><span>AI Assistant</span>
        <button onclick="document.getElementById('ai-panel').classList.remove('open')">✕</button>
      </div>
      <div id="ai-messages">
        <div class="ai-msg bot">Hi! Ask me anything about our products or pricing.</div>
      </div>
      <div id="ai-input-row">
        <input id="ai-input" placeholder="Ask about products or pricing…" />
        <button id="ai-send">➤</button>
      </div>
    </div>
  `);

  document.getElementById('ai-fab').onclick = () =>
    document.getElementById('ai-panel').classList.toggle('open');

  async function send() {
    const input = document.getElementById('ai-input');
    const text = input.value.trim();
    if (!text) return;
    const messages = document.getElementById('ai-messages');
    const sendBtn = document.getElementById('ai-send');

    messages.insertAdjacentHTML('beforeend', `<div class="ai-msg user">${text}</div>`);
    input.value = '';
    sendBtn.disabled = true;

    const typing = document.createElement('div');
    typing.className = 'ai-msg bot';
    typing.textContent = '...';
    messages.appendChild(typing);
    messages.scrollTop = messages.scrollHeight;

    try {
      const res = await fetch('/api/assistant/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });
      const data = await res.json();
      typing.textContent = data.reply || 'No response.';
    } catch {
      typing.textContent = 'Sorry, could not reach the assistant.';
    }

    sendBtn.disabled = false;
    messages.scrollTop = messages.scrollHeight;
  }

  document.getElementById('ai-send').onclick = send;
  document.getElementById('ai-input').onkeydown = e => { if (e.key === 'Enter') send(); };
})();
