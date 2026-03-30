document.addEventListener('DOMContentLoaded', () => {
  const chatLog = document.getElementById('chat-log');
  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('chat-input');
  const sendButton = document.getElementById('chat-send');
  const closeButton = document.getElementById('analyze-exit-button');
  const conversationHistory = [];
  const maxHistoryMessages = 20;

  const appendMessage = (role, text) => {
    if (!chatLog) return;

    const wrapper = document.createElement('div');
    wrapper.className = role === 'user' ? 'chat-message user' : 'chat-message assistant';

    const roleTag = document.createElement('div');
    roleTag.className = 'chat-role';
    roleTag.textContent = role === 'user' ? 'You' : 'Ollama';

    const body = document.createElement('div');
    body.className = 'chat-body';
    body.textContent = text;

    wrapper.appendChild(roleTag);
    wrapper.appendChild(body);
    chatLog.appendChild(wrapper);
    chatLog.scrollTop = chatLog.scrollHeight;
  };

  const setBusy = (busy) => {
    if (sendButton) {
      sendButton.disabled = busy;
      sendButton.setAttribute('aria-disabled', String(busy));
    }
    if (chatInput) {
      chatInput.disabled = busy;
      chatInput.setAttribute('aria-disabled', String(busy));
    }
  };

  if (closeButton) {
    closeButton.addEventListener('click', () => {
      if (window.electronAPI && typeof window.electronAPI.quit === 'function') {
        window.close();
      } else {
        window.close();
      }
    });
  }

  appendMessage(
    'assistant',
    'Ready. Ask a question about the off-loaded JSON library and I will query local Ollama for analysis.'
  );

  if (chatForm) {
    chatForm.addEventListener('submit', async (event) => {
      event.preventDefault();

      if (!chatInput) return;

      const question = chatInput.value.trim();
      if (!question) return;

      appendMessage('user', question);
      chatInput.value = '';
      setBusy(true);

      try {
        if (!window.electronAPI || typeof window.electronAPI.analyzeLibraryData !== 'function') {
          throw new Error('Analyze API is unavailable. Check preload bridge configuration.');
        }

        const response = await window.electronAPI.analyzeLibraryData(question, {
          model: 'qwen2.5:3b',
          history: conversationHistory
        });

        const modelUsed = response && response.model ? response.model : 'unknown';
        const totalEntries = response && Number.isFinite(response.totalEntries) ? response.totalEntries : 0;

        appendMessage('assistant', `Model: ${modelUsed} | Entries: ${totalEntries}\n\n${response.answer}`);

        conversationHistory.push({ role: 'user', content: question });
        conversationHistory.push({ role: 'assistant', content: response.answer });

        if (conversationHistory.length > maxHistoryMessages) {
          conversationHistory.splice(0, conversationHistory.length - maxHistoryMessages);
        }
      } catch (error) {
        appendMessage('assistant', `Analysis failed: ${error.message}`);
      } finally {
        setBusy(false);
        chatInput.focus();
      }
    });
  }
});
