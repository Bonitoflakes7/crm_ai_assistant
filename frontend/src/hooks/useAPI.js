import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 60000,  // 60s — Groq can be slow on first cold call
})

export const chatAPI = {
  sendMessage: async ({ message, formState, chatHistory, sessionId }) => {
    const res = await api.post('/chat', {
      message,
      form_state: formState,
      chat_history: chatHistory,
      session_id: sessionId,
    })
    return res.data
  },

  saveInteraction: async ({ formState, chatHistory, sessionId }) => {
    const res = await api.post('/interactions', {
      form_state: formState,
      chat_history: chatHistory,
      session_id: sessionId,
    })
    return res.data
  },

  getInteractions: async () => {
    const res = await api.get('/interactions')
    return res.data
  },

  searchHCPs: async (query) => {
    const res = await api.get(`/hcps/search?q=${encodeURIComponent(query)}`)
    return res.data
  },

  seedHCPs: async () => {
    const res = await api.post('/hcps/seed')
    return res.data
  },

  health: async () => {
    const res = await api.get('/health')
    return res.data
  },
}

export default api
