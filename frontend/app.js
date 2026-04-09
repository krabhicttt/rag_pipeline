// ===== Configuration =====
const CONFIG = {
  API_BASE: 'http://localhost:8000',
  ENDPOINTS: {
    CHAT:   '/api/chat',
    HEALTH: '/api/health',
    INGEST: '/api/ingest',
  },
  MAX_RETRIES: 2,
};

// ===== State =====
const state = {
  conversations: [],          // [{ id, title, messages: [] }]
  activeConversationId: null,
  isLoading: false,
  selectedModel: 'llama3.2',
};

// ===== DOM refs =====
const $ = id => document.getElementById(id);
const dom = {
  messages:           $('messages'),
  chatInput:          $('chatInput'),
  sendBtn:            $('sendBtn'),
  charCount:          $('charCount'),
  modelSelect:        $('modelSelect'),
  statusDot:          $('statusDot'),
  statusText:         $('statusText'),
  topbarTitle:        $('topbarTitle'),
  conversationList:   $('conversationList'),
  newChatBtn:         $('newChatBtn'),
  clearChatBtn:       $('clearChatBtn'),
  sidebarToggle:      $('sidebarToggle'),
  welcomeScreen:      $('welcomeScreen'),
  modalOverlay:       $('modalOverlay'),
  modalBody:          $('modalBody'),
  modalClose:         $('modalClose'),
};

// ===== Helpers =====
const genId   = () => `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
const now     = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
const escHtml = s => s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

/** Very small Markdown → HTML renderer (bold, italic, code, pre, lists, blockquote, headings) */
function renderMarkdown(text) {
  let html = escHtml(text);

  // Fenced code blocks
  html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) =>
    `<pre><code class="language-${lang}">${code.trim()}</code></pre>`);

  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Headings
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm,  '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm,   '<h1>$1</h1>');

  // Blockquote
  html = html.replace(/^&gt; (.+)$/gm, '<blockquote>$1</blockquote>');

  // Bold & italic
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
  html = html.replace(/\*\*(.+?)\*\*/g,     '<strong>$1</strong>');
  html = html.replace(/\*(.+?)\*/g,         '<em>$1</em>');

  // Unordered lists
  html = html.replace(/((?:^- .+\n?)+)/gm, match => {
    const items = match.trim().split('\n').map(l => `<li>${l.replace(/^- /, '')}</li>`).join('');
    return `<ul>${items}</ul>`;
  });

  // Ordered lists
  html = html.replace(/((?:^\d+\. .+\n?)+)/gm, match => {
    const items = match.trim().split('\n').map(l => `<li>${l.replace(/^\d+\. /, '')}</li>`).join('');
    return `<ol>${items}</ol>`;
  });

  // Paragraphs (double newlines)
  html = html
    .split(/\n{2,}/)
    .map(block => block.trim())
    .filter(Boolean)
    .map(block => {
      if (/^<(h[1-3]|ul|ol|pre|blockquote)/.test(block)) return block;
      return `<p>${block.replace(/\n/g, '<br>')}</p>`;
    })
    .join('');

  return html;
}

// ===== Conversations =====
function createConversation() {
  const conv = { id: genId(), title: 'New Chat', messages: [] };
  state.conversations.unshift(conv);
  state.activeConversationId = conv.id;
  saveToStorage();
  renderSidebar();
  renderMessages();
  dom.topbarTitle.textContent = conv.title;
  return conv;
}

function getActiveConversation() {
  return state.conversations.find(c => c.id === state.activeConversationId);
}

function switchConversation(id) {
  state.activeConversationId = id;
  const conv = getActiveConversation();
  dom.topbarTitle.textContent = conv?.title ?? 'Chat';
  renderMessages();
  renderSidebar();
}

function autoTitle(text) {
  return text.length > 40 ? text.slice(0, 40).trim() + '…' : text.trim();
}

// ===== Sidebar =====
function renderSidebar() {
  dom.conversationList.innerHTML = state.conversations.map(conv => `
    <li class="conversation-item ${conv.id === state.activeConversationId ? 'active' : ''}"
        data-id="${conv.id}">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"
          stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <span>${escHtml(conv.title)}</span>
    </li>
  `).join('');

  dom.conversationList.querySelectorAll('.conversation-item').forEach(el => {
    el.addEventListener('click', () => switchConversation(el.dataset.id));
  });
}

// ===== Messages =====
function renderMessages() {
  const conv = getActiveConversation();
  if (!conv || conv.messages.length === 0) {
    dom.messages.innerHTML = `<div class="welcome" id="welcomeScreen">
      <div class="welcome-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"
            stroke="#4fc3f7" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
      <h2>How can I help you today?</h2>
      <p>Ask anything about your documents. I'll search the knowledge base and provide grounded answers.</p>
      <div class="suggestions">
        <button class="suggestion-chip" data-text="What documents are available in the knowledge base?">What documents are available?</button>
        <button class="suggestion-chip" data-text="Summarize the key topics covered in the documents.">Summarize key topics</button>
        <button class="suggestion-chip" data-text="What are the main concepts I should know?">Main concepts overview</button>
      </div>
    </div>`;
    attachSuggestionListeners();
    return;
  }

  dom.messages.innerHTML = conv.messages.map(msg => buildMessageHTML(msg)).join('');
  scrollToBottom();
}

function buildMessageHTML(msg) {
  const isUser = msg.role === 'user';
  const avatarContent = isUser
    ? '<span>U</span>'
    : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none">
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"
          stroke="#4fc3f7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
       </svg>`;

  const sourcesBtn = (!isUser && msg.sources?.length)
    ? `<button class="btn-sources" data-sources='${JSON.stringify(msg.sources)}'>
        ${msg.sources.length} source${msg.sources.length > 1 ? 's' : ''}
       </button>`
    : '';

  const bubbleContent = isUser
    ? `<p>${escHtml(msg.content).replace(/\n/g, '<br>')}</p>`
    : renderMarkdown(msg.content);

  return `
    <div class="message-group">
      <div class="message-row ${isUser ? 'user' : 'assistant'}">
        <div class="avatar ${isUser ? 'user' : 'assistant'}">${avatarContent}</div>
        <div class="bubble-wrap">
          <div class="bubble ${msg.error ? 'error' : ''}">${bubbleContent}</div>
          <div class="message-meta">
            <span class="message-time">${msg.time ?? ''}</span>
            ${sourcesBtn}
          </div>
        </div>
      </div>
    </div>`;
}

function appendMessage(msg) {
  // Remove welcome screen if present
  const welcome = dom.messages.querySelector('.welcome');
  if (welcome) welcome.remove();

  const el = document.createElement('div');
  el.innerHTML = buildMessageHTML(msg);
  el.firstElementChild.dataset.msgId = msg.id;
  dom.messages.appendChild(el.firstElementChild);
  scrollToBottom();
  attachSourceListeners();
}

function appendTypingIndicator() {
  const el = document.createElement('div');
  el.id = 'typingIndicator';
  el.className = 'typing-indicator';
  el.innerHTML = `
    <div class="avatar assistant">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"
          stroke="#4fc3f7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </div>
    <div class="typing-dots">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    </div>`;
  dom.messages.appendChild(el);
  scrollToBottom();
}

function removeTypingIndicator() {
  $('typingIndicator')?.remove();
}

function scrollToBottom() {
  const wrapper = dom.messages.closest('.messages-wrapper');
  if (wrapper) wrapper.scrollTop = wrapper.scrollHeight;
}

// ===== Sources Modal =====
function attachSourceListeners() {
  dom.messages.querySelectorAll('.btn-sources').forEach(btn => {
    btn.onclick = () => showSources(JSON.parse(btn.dataset.sources));
  });
}

function showSources(sources) {
  dom.modalBody.innerHTML = sources.map((s, i) => `
    <div class="source-card">
      <div class="source-card-header">
        <span class="source-doc">${escHtml(s.document ?? `Source ${i+1}`)}</span>
        ${s.score != null ? `<span class="source-score">${(s.score * 100).toFixed(0)}% match</span>` : ''}
      </div>
      <div class="source-meta">
        ${s.page    ? `Page ${s.page} · ` : ''}
        ${s.section ? `${escHtml(s.section)} · ` : ''}
        ${s.metadata ? escHtml(JSON.stringify(s.metadata)) : ''}
      </div>
      <div class="source-text">${escHtml(s.text ?? s.content ?? '').slice(0, 400)}${(s.text ?? '').length > 400 ? '…' : ''}</div>
    </div>
  `).join('');
  dom.modalOverlay.style.display = 'flex';
}

dom.modalClose.onclick   = () => dom.modalOverlay.style.display = 'none';
dom.modalOverlay.onclick = e => { if (e.target === dom.modalOverlay) dom.modalOverlay.style.display = 'none'; };

// ===== Suggestion chips =====
function attachSuggestionListeners() {
  document.querySelectorAll('.suggestion-chip').forEach(btn => {
    btn.onclick = () => {
      dom.chatInput.value = btn.dataset.text;
      handleInputChange();
      sendMessage();
    };
  });
}

// ===== API Calls =====
async function callChatAPI(message, conversationHistory) {
  const response = await fetch(`${CONFIG.API_BASE}${CONFIG.ENDPOINTS.CHAT}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      model:   state.selectedModel,
      history: conversationHistory.slice(-10),  // last 10 messages for context
    }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail ?? `Server error ${response.status}`);
  }

  return response.json();
}

async function checkHealth() {
  dom.statusDot.className  = 'dot checking';
  dom.statusText.textContent = 'Checking…';
  try {
    const res = await fetch(`${CONFIG.API_BASE}${CONFIG.ENDPOINTS.HEALTH}`, { signal: AbortSignal.timeout(4000) });
    if (res.ok) {
      dom.statusDot.className  = 'dot online';
      dom.statusText.textContent = 'Backend online';
    } else {
      throw new Error('not ok');
    }
  } catch {
    dom.statusDot.className  = 'dot offline';
    dom.statusText.textContent = 'Backend offline';
  }
}

// ===== Send Message =====
async function sendMessage() {
  const text = dom.chatInput.value.trim();
  if (!text || state.isLoading) return;

  let conv = getActiveConversation();
  if (!conv) conv = createConversation();

  // Auto-title from first message
  if (conv.messages.length === 0) {
    conv.title = autoTitle(text);
    dom.topbarTitle.textContent = conv.title;
    renderSidebar();
  }

  // Add user message
  const userMsg = { id: genId(), role: 'user', content: text, time: now() };
  conv.messages.push(userMsg);
  appendMessage(userMsg);

  // Reset input
  dom.chatInput.value = '';
  handleInputChange();
  setLoading(true);

  appendTypingIndicator();

  try {
    const data = await callChatAPI(text, conv.messages.slice(0, -1));

    removeTypingIndicator();

    const assistantMsg = {
      id:      genId(),
      role:    'assistant',
      content: data.response ?? data.answer ?? '(empty response)',
      sources: data.sources ?? [],
      model:   data.model ?? state.selectedModel,
      time:    now(),
    };

    conv.messages.push(assistantMsg);
    appendMessage(assistantMsg);
    saveToStorage();

  } catch (err) {
    removeTypingIndicator();

    const errorMsg = {
      id:      genId(),
      role:    'assistant',
      content: `**Error:** ${err.message}\n\nMake sure the Python backend is running on \`${CONFIG.API_BASE}\`.`,
      error:   true,
      time:    now(),
    };

    conv.messages.push(errorMsg);
    appendMessage(errorMsg);
    saveToStorage();
  } finally {
    setLoading(false);
  }
}

function setLoading(isLoading) {
  state.isLoading = isLoading;
  dom.sendBtn.disabled = isLoading || !dom.chatInput.value.trim();
  dom.chatInput.disabled = isLoading;
}

// ===== Input Handling =====
function handleInputChange() {
  const val = dom.chatInput.value;
  dom.charCount.textContent = `${val.length} / 4000`;
  dom.sendBtn.disabled = !val.trim() || state.isLoading;

  // Auto-resize textarea
  dom.chatInput.style.height = 'auto';
  dom.chatInput.style.height = Math.min(dom.chatInput.scrollHeight, 200) + 'px';
}

dom.chatInput.addEventListener('input', handleInputChange);

dom.chatInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

dom.sendBtn.addEventListener('click', sendMessage);

// ===== Toolbar Actions =====
dom.newChatBtn.addEventListener('click', () => {
  createConversation();
  dom.chatInput.focus();
});

dom.clearChatBtn.addEventListener('click', () => {
  const conv = getActiveConversation();
  if (conv) {
    conv.messages = [];
    saveToStorage();
    renderMessages();
  }
});

dom.sidebarToggle.addEventListener('click', () => {
  document.querySelector('.sidebar').classList.toggle('collapsed');
});

dom.modelSelect.addEventListener('change', e => {
  state.selectedModel = e.target.value;
});

// ===== LocalStorage =====
function saveToStorage() {
  try {
    localStorage.setItem('rag_chat_state', JSON.stringify({
      conversations:         state.conversations,
      activeConversationId:  state.activeConversationId,
    }));
  } catch { /* storage full – ignore */ }
}

function loadFromStorage() {
  try {
    const saved = JSON.parse(localStorage.getItem('rag_chat_state') ?? '{}');
    if (saved.conversations?.length) {
      state.conversations        = saved.conversations;
      state.activeConversationId = saved.activeConversationId ?? saved.conversations[0].id;
    }
  } catch { /* ignore corrupt data */ }
}

// ===== Init =====
function init() {
  loadFromStorage();

  if (state.conversations.length === 0) {
    createConversation();
  } else {
    renderSidebar();
    renderMessages();
    attachSourceListeners();
    dom.topbarTitle.textContent = getActiveConversation()?.title ?? 'Chat';
  }

  checkHealth();
  setInterval(checkHealth, 30_000);   // re-check every 30 s

  dom.chatInput.focus();
}

init();
