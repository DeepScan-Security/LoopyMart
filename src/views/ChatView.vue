<script setup>
import { ref, onMounted, nextTick } from 'vue'
import client from '@/api/client'

const messages = ref([])
const newMessage = ref('')
const loading = ref(true)
const sending = ref(false)
const chatContainer = ref(null)

onMounted(async () => {
  try {
    const res = await client.get('/chat/history')
    messages.value = res.data.messages
    await nextTick()
    scrollToBottom()
  } catch (e) {
    console.error('Failed to load chat history', e)
  } finally {
    loading.value = false
  }
})

function scrollToBottom() {
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

async function sendMessage() {
  if (!newMessage.value.trim() || sending.value) return
  
  const userMsg = newMessage.value.trim()
  newMessage.value = ''
  sending.value = true
  
  try {
    const res = await client.post('/chat', { message: userMsg })
    
    // Add user message
    messages.value.push({
      id: `${res.data.id}_user`,
      message: userMsg,
      is_user: true,
      created_at: new Date().toISOString(),
    })
    
    // Add AI response
    messages.value.push({
      id: `${res.data.id}_ai`,
      message: res.data.response,
      is_user: false,
      created_at: new Date().toISOString(),
    })
    
    await nextTick()
    scrollToBottom()
  } catch (e) {
    console.error('Failed to send message', e)
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <div class="chat-page">
    <div class="chat-header">
      <h1>Support Chat</h1>
      <p>Ask us anything! Our AI assistant is here to help.</p>
    </div>
    
    <div v-if="loading" class="loading">Loading chat...</div>
    
    <div v-else class="chat-container">
      <div class="messages" ref="chatContainer">
        <div v-if="messages.length === 0" class="welcome-message">
          <h3>👋 Welcome to LoopyMart!</h3>
          <p>How can we help you today?</p>
        </div>
        
        <div 
          v-for="msg in messages" 
          :key="msg.id" 
          :class="['message', msg.is_user ? 'message-user' : 'message-ai']">
          <div class="message-avatar">
            {{ msg.is_user ? '👤' : '🤖' }}
          </div>
          <div class="message-content">
            <div class="message-text">{{ msg.message }}</div>
            <div class="message-time">
              {{ new Date(msg.created_at).toLocaleTimeString() }}
            </div>
          </div>
        </div>
      </div>
      
      <form @submit.prevent="sendMessage" class="message-input">
        <input 
          v-model="newMessage" 
          type="text" 
          placeholder="Type your message..."
          :disabled="sending"
        />
        <button type="submit" :disabled="sending || !newMessage.trim()">
          {{ sending ? '⏳' : '📤' }}
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.chat-page {
  height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
}

.chat-header {
  padding: 1rem;
  background: white;
  border-bottom: 1px solid #e5e7eb;
}

.chat-header h1 {
  margin: 0 0 0.5rem;
  font-size: 1.5rem;
}

.chat-header p {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
}

.loading {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f9fafb;
  overflow: hidden;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.welcome-message {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.welcome-message h3 {
  margin: 0 0 0.5rem;
  font-size: 1.2rem;
}

.message {
  display: flex;
  gap: 0.75rem;
  max-width: 70%;
  animation: slideIn 0.3s ease;
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

.message-user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-ai {
  align-self: flex-start;
}

.message-avatar {
  font-size: 2rem;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.message-text {
  padding: 0.75rem 1rem;
  border-radius: 12px;
  font-size: 0.95rem;
  line-height: 1.5;
}

.message-user .message-text {
  background: #2874f0;
  color: white;
  border-bottom-right-radius: 4px;
}

.message-ai .message-text {
  background: white;
  border: 1px solid #e5e7eb;
  border-bottom-left-radius: 4px;
}

.message-time {
  font-size: 0.75rem;
  color: #999;
  padding: 0 0.5rem;
}

.message-user .message-time {
  text-align: right;
}

.message-input {
  display: flex;
  gap: 0.75rem;
  padding: 1rem;
  background: white;
  border-top: 1px solid #e5e7eb;
}

.message-input input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 24px;
  font-size: 0.95rem;
  font-family: inherit;
}

.message-input input:focus {
  outline: none;
  border-color: #2874f0;
}

.message-input button {
  width: 48px;
  height: 48px;
  border: none;
  background: #2874f0;
  color: white;
  border-radius: 50%;
  font-size: 1.2rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.message-input button:hover:not(:disabled) {
  background: #1e5bc6;
  transform: scale(1.05);
}

.message-input button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
