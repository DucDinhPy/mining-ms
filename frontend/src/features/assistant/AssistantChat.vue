<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { sendAssistantMessage } from '../../services/assistantApi'

const STORAGE_KEY = 'mineops-assistant-session'
const MAX_MESSAGE_LENGTH = 4000

const suggestedPrompts = [
  'Which cameras are currently connected?',
  'Summarise the latest PPE detections.',
  'What can you help me with in MineOps?',
]

const isOpen = ref(false)
const hasUnreadResponse = ref(false)
const draft = ref('')
const interactionId = ref(null)
const isSending = ref(false)
const elapsedSeconds = ref(0)
const errorMessage = ref('')
const messageList = ref(null)
const messageInput = ref(null)

let abortController = null
let elapsedTimer = null

const messages = ref([
  createMessage(
    'assistant',
    'Hello. I am your MineOps Assistant. Ask me about active cameras, runtime status, or the latest PPE detections.',
  ),
])

const canSend = computed(() => (
  draft.value.trim().length > 0
  && draft.value.length <= MAX_MESSAGE_LENGTH
  && !isSending.value
))

const userMessageCount = computed(
  () => messages.value.filter((message) => message.role === 'user').length,
)

function createMessage(role, content) {
  return {
    id: globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random()}`,
    role,
    content,
    createdAt: new Date().toISOString(),
  }
}

function loadSession() {
  try {
    const stored = sessionStorage.getItem(STORAGE_KEY)
    if (!stored) return

    const parsed = JSON.parse(stored)

    if (Array.isArray(parsed.messages) && parsed.messages.length) {
      messages.value = parsed.messages.filter(
        (message) => ['assistant', 'user'].includes(message.role) && message.content,
      )
    }

    interactionId.value = typeof parsed.interactionId === 'string'
      ? parsed.interactionId
      : null
  } catch {
    sessionStorage.removeItem(STORAGE_KEY)
  }
}

function saveSession() {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify({
    messages: messages.value,
    interactionId: interactionId.value,
  }))
}

function openAssistant() {
  isOpen.value = true
  hasUnreadResponse.value = false

  nextTick(async () => {
    await scrollToLatest()
    messageInput.value?.focus()
  })
}

function closeAssistant() {
  isOpen.value = false
}

async function submitMessage(message = draft.value) {
  const content = message.trim()

  if (!content || isSending.value) return

  if (content.length > MAX_MESSAGE_LENGTH) {
    errorMessage.value = `Message must be ${MAX_MESSAGE_LENGTH.toLocaleString()} characters or fewer.`
    return
  }

  messages.value.push(createMessage('user', content))
  draft.value = ''
  errorMessage.value = ''
  isSending.value = true
  elapsedSeconds.value = 0
  abortController = new AbortController()
  startElapsedTimer()
  await scrollToLatest()

  try {
    const response = await sendAssistantMessage(
      {
        message: content,
        previous_interaction_id: interactionId.value,
      },
      { signal: abortController.signal },
    )

    if (!response?.message) {
      throw new Error('The assistant returned an empty response.')
    }

    messages.value.push(createMessage('assistant', response.message))
    interactionId.value = response.interaction_id ?? interactionId.value

    if (!isOpen.value) hasUnreadResponse.value = true
  } catch (error) {
    if (error.name === 'AbortError') {
      errorMessage.value = 'Response stopped.'
    } else {
      errorMessage.value = error.message || 'MineOps Assistant is unavailable.'
      if (!isOpen.value) hasUnreadResponse.value = true
    }
  } finally {
    isSending.value = false
    abortController = null
    stopElapsedTimer()
    await scrollToLatest()
    messageInput.value?.focus()
  }
}

function useSuggestedPrompt(prompt) {
  draft.value = prompt
  submitMessage(prompt)
}

function stopResponse() {
  abortController?.abort()
}

function startNewConversation() {
  stopResponse()
  interactionId.value = null
  errorMessage.value = ''
  messages.value = [
    createMessage(
      'assistant',
      'New conversation started. What would you like to know about MineOps?',
    ),
  ]
  sessionStorage.removeItem(STORAGE_KEY)
  nextTick(() => messageInput.value?.focus())
}

function startElapsedTimer() {
  stopElapsedTimer()
  elapsedTimer = window.setInterval(() => {
    elapsedSeconds.value += 1
  }, 1000)
}

function stopElapsedTimer() {
  if (elapsedTimer) window.clearInterval(elapsedTimer)
  elapsedTimer = null
}

function handleKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    submitMessage()
  }
}

function handleWindowKeydown(event) {
  if (event.key === 'Escape' && isOpen.value) closeAssistant()
}

async function scrollToLatest() {
  await nextTick()
  const element = messageList.value
  if (element) element.scrollTop = element.scrollHeight
}

function formatTime(value) {
  return new Intl.DateTimeFormat('en-AU', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(new Date(value))
}

watch([messages, interactionId], saveSession, { deep: true })

onMounted(() => {
  loadSession()
  window.addEventListener('keydown', handleWindowKeydown)
})

onBeforeUnmount(() => {
  abortController?.abort()
  stopElapsedTimer()
  window.removeEventListener('keydown', handleWindowKeydown)
})
</script>

<template>
  <div class="assistant-widget">
    <button
      v-if="!isOpen"
      class="assistant-launcher"
      type="button"
      aria-label="Open MineOps Assistant"
      @click="openAssistant"
    >
      <span class="launcher-icon">
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M12 3 5 6.5v5c0 4.5 2.8 8.1 7 9.5 4.2-1.4 7-5 7-9.5v-5L12 3Z" />
          <path d="M8.5 12h7M10 9.5v5M14 9.5v5" />
        </svg>
        <i v-if="hasUnreadResponse"></i>
      </span>
      <span class="launcher-copy">
        <strong>MineOps Assistant</strong>
        <small>{{ isSending ? `Working · ${elapsedSeconds}s` : 'Ask about your operation' }}</small>
      </span>
    </button>

    <Transition name="assistant-popup">
      <section
        v-if="isOpen"
        class="assistant-popup-panel"
        role="dialog"
        aria-label="MineOps Assistant"
      >
        <header class="assistant-popup-header">
          <div class="assistant-popup-identity">
            <span class="assistant-avatar" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none">
                <path d="M12 3 5 6.5v5c0 4.5 2.8 8.1 7 9.5 4.2-1.4 7-5 7-9.5v-5L12 3Z" />
                <path d="M8.5 12h7M10 9.5v5M14 9.5v5" />
              </svg>
            </span>
            <div>
              <div class="assistant-title-row">
                <h2>MineOps Assistant</h2>
                <span class="assistant-online"><i></i> Online</span>
              </div>
              <p>Camera and PPE operations</p>
            </div>
          </div>

          <div class="assistant-header-actions">
            <button
              type="button"
              title="Start new conversation"
              aria-label="Start new conversation"
              @click="startNewConversation"
            >
              <svg viewBox="0 0 20 20" fill="none"><path d="M10 3v14M3 10h14" /></svg>
            </button>
            <button
              type="button"
              title="Close assistant"
              aria-label="Close assistant"
              @click="closeAssistant"
            >
              <svg viewBox="0 0 20 20" fill="none"><path d="m5 5 10 10M15 5 5 15" /></svg>
            </button>
          </div>
        </header>

        <div class="assistant-tool-strip">
          <span><i></i> Live camera status</span>
          <span><i></i> Latest PPE data</span>
          <strong>Read only</strong>
        </div>

        <div ref="messageList" class="assistant-messages assistant-popup-messages" aria-live="polite">
          <article
            v-for="message in messages"
            :key="message.id"
            class="chat-message"
            :class="message.role"
          >
            <span class="message-avatar" aria-hidden="true">
              <svg v-if="message.role === 'assistant'" viewBox="0 0 24 24" fill="none">
                <path d="M12 3 5 6.5v5c0 4.5 2.8 8.1 7 9.5 4.2-1.4 7-5 7-9.5v-5L12 3Z" />
                <path d="M9 12h6M10 9.5v5M14 9.5v5" />
              </svg>
              <span v-else>DA</span>
            </span>

            <div class="message-content">
              <div class="message-meta">
                <strong>{{ message.role === 'assistant' ? 'MineOps AI' : 'You' }}</strong>
                <time :datetime="message.createdAt">{{ formatTime(message.createdAt) }}</time>
              </div>
              <p>{{ message.content }}</p>
            </div>
          </article>

          <div v-if="userMessageCount === 0 && !isSending" class="assistant-popup-prompts">
            <span>Try asking</span>
            <button
              v-for="prompt in suggestedPrompts"
              :key="prompt"
              type="button"
              @click="useSuggestedPrompt(prompt)"
            >
              {{ prompt }}
              <svg viewBox="0 0 20 20" fill="none"><path d="m7 4 6 6-6 6" /></svg>
            </button>
          </div>

          <article v-if="isSending" class="chat-message assistant pending">
            <span class="message-avatar" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none">
                <path d="M12 3 5 6.5v5c0 4.5 2.8 8.1 7 9.5 4.2-1.4 7-5 7-9.5v-5L12 3Z" />
                <path d="M9 12h6M10 9.5v5M14 9.5v5" />
              </svg>
            </span>
            <div class="message-content">
              <div class="message-meta">
                <strong>MineOps AI</strong>
                <span>{{ elapsedSeconds }}s</span>
              </div>
              <div class="assistant-thinking">
                <span></span><span></span><span></span>
                <b>Checking MineOps data...</b>
              </div>
            </div>
          </article>
        </div>

        <div v-if="errorMessage" class="assistant-error" role="alert">
          <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <circle cx="10" cy="10" r="7" />
            <path d="M10 6.5v4.5M10 14h.01" />
          </svg>
          <span>{{ errorMessage }}</span>
          <button type="button" @click="errorMessage = ''">Dismiss</button>
        </div>

        <footer class="assistant-composer assistant-popup-composer">
          <div class="composer-field" :class="{ busy: isSending }">
            <textarea
              ref="messageInput"
              v-model="draft"
              rows="1"
              :maxlength="MAX_MESSAGE_LENGTH"
              :disabled="isSending"
              placeholder="Ask MineOps Assistant..."
              aria-label="Message MineOps Assistant"
              @keydown="handleKeydown"
            ></textarea>

            <div class="composer-actions">
              <button
                v-if="isSending"
                class="stop-response"
                type="button"
                @click="stopResponse"
              >
                Stop
              </button>
              <button
                v-else
                class="send-message"
                type="button"
                :disabled="!canSend"
                aria-label="Send message"
                @click="submitMessage()"
              >
                <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
                  <path d="m3 3 14 7-14 7 2-7-2-7Z" />
                  <path d="M5 10h12" />
                </svg>
              </button>
            </div>
          </div>
          <p>Confirm safety-critical decisions with qualified personnel.</p>
        </footer>
      </section>
    </Transition>
  </div>
</template>
