<template>
  <div class="chatbot-container">
    <!-- Header -->
    <div class="chatbot-header">
      <h2>T10 AIRPS Chatbot</h2>
      <div class="status">
        <span :class="['indicator', chatStatus]"></span>
        {{ statusText }}
      </div>
    </div>

    <!-- Messages Display -->
    <div class="chat-messages" ref="messagesContainer">
      <div v-for="msg in messages" :key="msg.id" :class="['message', msg.type]">
        <div v-if="msg.type === 'user'" class="message-content user-msg">
          {{ msg.content }}
        </div>
        <div v-else-if="msg.type === 'assistant'" class="message-content assistant-msg">
          {{ msg.content }}
        </div>
        <div v-else-if="msg.type === 'action'" class="message-content action-msg">
          <strong>System Action:</strong> {{ msg.action }}<br/>
          <small>{{ JSON.stringify(msg.params) }}</small>
        </div>
        <div v-else-if="msg.type === 'error'" class="message-content error-msg">
          ⚠️ {{ msg.content }}
        </div>
      </div>
      <div v-if="isLoading" class="message loading">
        <div class="typing-indicator">
          <span></span><span></span><span></span>
        </div>
      </div>
    </div>

    <!-- Input Area -->
    <div class="chat-input-area">
      <!-- Text Input -->
      <div class="input-row">
        <input
          v-model="userMessage"
          @keyup.enter="sendMessage"
          type="text"
          placeholder="Ask me anything... (Type 'help' for commands)"
          class="text-input"
          :disabled="isLoading || !isConnected"
        />
        <button @click="sendMessage" :disabled="isLoading || !isConnected" class="send-btn">
          Send
        </button>
      </div>

      <!-- Voice Controls -->
      <div class="voice-controls">
        <button
          @click="toggleVoiceInput"
          :disabled="!voiceSupported || isLoading"
          :class="['voice-btn', { listening: isListening }]"
          title="Click to start voice input"
        >
          🎤 {{ isListening ? "Listening..." : "Voice" }}
        </button>

        <button
          @click="toggleVoiceOutput"
          :disabled="!voiceSupported"
          :class="['voice-btn', { enabled: voiceOutputEnabled }]"
          title="Toggle voice responses"
        >
          🔊 {{ voiceOutputEnabled ? "On" : "Off" }}
        </button>

        <button
          @click="showHelp"
          class="help-btn"
          title="Show chatbot help"
        >
          ❓ Help
        </button>
      </div>

      <!-- Quick Commands -->
      <div class="quick-commands">
        <button
          v-for="cmd in quickCommands"
          :key="cmd"
          @click="userMessage = cmd"
          class="cmd-btn"
        >
          {{ cmd }}
        </button>
      </div>
    </div>

    <!-- Help Modal -->
    <div v-if="showHelpModal" class="help-modal" @click.self="showHelpModal = false">
      <div class="help-content">
        <h3>Chatbot Help</h3>
        <p><strong>Cost:</strong> 100% FREE - Runs completely offline using Ollama</p>
        <h4>Example Commands:</h4>
        <ul>
          <li>Create a critical malware incident on database server</li>
          <li>Show me all open incidents</li>
          <li>Close incident 5</li>
          <li>What playbooks for ransomware?</li>
          <li>Give me dashboard summary</li>
          <li>How to respond to data exfiltration</li>
        </ul>
        <h4>Features:</h4>
        <ul>
          <li>Natural language incident management</li>
          <li>Voice input & output support</li>
          <li>Dashboard automation via chat</li>
          <li>Hands-free operation</li>
          <li>Security best practices guidance</li>
        </ul>
        <button @click="showHelpModal = false" class="close-btn">Close</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'

const userMessage = ref('')
const messages = ref([])
const isLoading = ref(false)
const isConnected = ref(false)
const isListening = ref(false)
const voiceSupported = ref(false)
const voiceOutputEnabled = ref(false)
const showHelpModal = ref(false)
const chatStatus = ref('connecting')
const messagesContainer = ref(null)
const ws = ref(null)

const token = localStorage.getItem('token')
const voiceRecognition = ref(null)

const statusText = computed(() => {
  if (!isConnected.value) return 'Offline - Connecting...'
  if (isLoading.value) return 'Chatbot thinking...'
  return 'Ready'
})

const quickCommands = [
  'Show open incidents',
  'Create incident',
  'Close incident',
  'Dashboard summary',
]

// Initialize voice recognition
onMounted(async () => {
  // Check voice support
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  if (SpeechRecognition) {
    voiceSupported.value = true
    voiceRecognition.value = new SpeechRecognition()
    voiceRecognition.value.continuous = false
    voiceRecognition.value.interimResults = false

    voiceRecognition.value.onstart = () => {
      isListening.value = true
    }

    voiceRecognition.value.onend = () => {
      isListening.value = false
    }

    voiceRecognition.value.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((result) => result[0].transcript)
        .join('')
      userMessage.value = transcript
      sendMessage()
    }

    voiceRecognition.value.onerror = (event) => {
      addMessage('error', `Voice error: ${event.error}`)
    }
  }

  // Connect WebSocket
  connectWebSocket()
})

// WebSocket connection
const connectWebSocket = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/api/chatbot/ws/chat`

  ws.value = new WebSocket(wsUrl)

  ws.value.onopen = () => {
    isConnected.value = true
    chatStatus.value = 'connected'
    addMessage('system', 'Connected to T10 AIRPS Chatbot. Type a message or use voice input.')
  }

  ws.value.onmessage = (event) => {
    const data = JSON.parse(event.data)

    if (data.type === 'stream') {
      const lastMsg = messages.value[messages.value.length - 1]
      if (lastMsg && lastMsg.type === 'assistant') {
        lastMsg.content += data.chunk
      } else {
        addMessage('assistant', data.chunk)
      }
      scrollToBottom()
    } else if (data.type === 'action') {
      addMessage('action', data.action, data.params)
    } else if (data.type === 'error') {
      addMessage('error', data.message)
    } else if (data.type === 'done') {
      isLoading.value = false
      if (voiceOutputEnabled.value) {
        speakLastMessage()
      }
    } else if (data.type === 'status') {
      addMessage('system', data.message)
    }
  }

  ws.value.onerror = () => {
    chatStatus.value = 'error'
    isConnected.value = false
    addMessage('error', 'WebSocket error. Check backend connection.')
  }

  ws.value.onclose = () => {
    chatStatus.value = 'disconnected'
    isConnected.value = false
  }
}

// Send message
const sendMessage = () => {
  if (!userMessage.value.trim() || !isConnected.value) return

  addMessage('user', userMessage.value)
  isLoading.value = true

  ws.value.send(
    JSON.stringify({
      message: userMessage.value,
      type: 'text',
      voice_response: voiceOutputEnabled.value,
      token: token,
    })
  )

  userMessage.value = ''
}

// Add message to display
const addMessage = (type, content, params = null) => {
  messages.value.push({
    id: Date.now(),
    type,
    content,
    params,
  })
  scrollToBottom()
}

// Scroll to bottom
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// Voice input
const toggleVoiceInput = () => {
  if (!voiceRecognition.value) return
  if (isListening.value) {
    voiceRecognition.value.abort()
  } else {
    voiceRecognition.value.start()
  }
}

// Voice output
const toggleVoiceOutput = () => {
  voiceOutputEnabled.value = !voiceOutputEnabled.value
}

// Speak last message
const speakLastMessage = () => {
  if (!('speechSynthesis' in window)) return
  const lastMsg = messages.value[messages.value.length - 1]
  if (lastMsg && lastMsg.type === 'assistant') {
    const utterance = new SpeechSynthesisUtterance(lastMsg.content)
    utterance.rate = 1.0
    speechSynthesis.speak(utterance)
  }
}

// Help
const showHelp = async () => {
  showHelpModal.value = true
}
</script>

<style scoped>
.chatbot-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #1a1a2e;
  color: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.chatbot-header {
  background: linear-gradient(135deg, #16213e, #0f3460);
  padding: 16px;
  border-bottom: 2px solid #00d4ff;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chatbot-header h2 {
  margin: 0;
  font-size: 18px;
}

.status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.indicator.connected {
  background: #00ff00;
}

.indicator.connecting {
  background: #ffaa00;
}

.indicator.disconnected,
.indicator.error {
  background: #ff4444;
  animation: none;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message {
  display: flex;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.user {
  justify-content: flex-end;
}

.message-content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 8px;
  word-wrap: break-word;
  line-height: 1.4;
}

.user-msg {
  background: #00d4ff;
  color: #000;
  border-radius: 18px 18px 4px 18px;
}

.assistant-msg {
  background: #16213e;
  border: 1px solid #00d4ff;
  border-radius: 18px 18px 18px 4px;
}

.action-msg {
  background: #2d5a2d;
  border: 1px solid #00ff00;
  border-radius: 8px;
  font-size: 12px;
}

.error-msg {
  background: #5a2d2d;
  border: 1px solid #ff4444;
  border-radius: 8px;
}

.loading {
  justify-content: flex-start;
}

.typing-indicator {
  display: flex;
  gap: 4px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #00d4ff;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    opacity: 0.3;
  }
  30% {
    opacity: 1;
  }
}

.chat-input-area {
  background: #16213e;
  border-top: 1px solid #00d4ff;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.input-row {
  display: flex;
  gap: 8px;
}

.text-input {
  flex: 1;
  padding: 12px;
  background: #0f3460;
  color: #fff;
  border: 1px solid #00d4ff;
  border-radius: 6px;
  font-size: 14px;
}

.text-input:focus {
  outline: none;
  box-shadow: 0 0 8px #00d4ff;
}

.text-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-btn {
  padding: 12px 24px;
  background: #00d4ff;
  color: #000;
  border: none;
  border-radius: 6px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s;
}

.send-btn:hover:not(:disabled) {
  background: #00a8cc;
  transform: translateY(-2px);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.voice-controls {
  display: flex;
  gap: 8px;
}

.voice-btn,
.help-btn {
  flex: 1;
  padding: 10px;
  background: #0f3460;
  color: #00d4ff;
  border: 1px solid #00d4ff;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.3s;
}

.voice-btn:hover:not(:disabled),
.help-btn:hover {
  background: #00d4ff;
  color: #000;
}

.voice-btn.listening {
  background: #ff4444;
  color: #fff;
  border-color: #ff4444;
}

.voice-btn.enabled {
  background: #00ff00;
  color: #000;
  border-color: #00ff00;
}

.voice-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.quick-commands {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.cmd-btn {
  padding: 8px 12px;
  background: #0f3460;
  color: #00d4ff;
  border: 1px solid #00d4ff;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.cmd-btn:hover {
  background: #00d4ff;
  color: #000;
}

.help-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.help-content {
  background: #1a1a2e;
  padding: 24px;
  border-radius: 8px;
  max-width: 500px;
  border: 2px solid #00d4ff;
  max-height: 80vh;
  overflow-y: auto;
}

.help-content h3 {
  margin-top: 0;
  color: #00d4ff;
}

.help-content h4 {
  color: #00ff00;
  margin-top: 16px;
}

.help-content ul {
  padding-left: 20px;
  font-size: 14px;
}

.help-content li {
  margin: 8px 0;
}

.close-btn {
  margin-top: 16px;
  padding: 10px 20px;
  background: #00d4ff;
  color: #000;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
}

.close-btn:hover {
  background: #00a8cc;
}

/* Scrollbar styling */
.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: #0f3460;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: #00d4ff;
  border-radius: 3px;
}
</style>
