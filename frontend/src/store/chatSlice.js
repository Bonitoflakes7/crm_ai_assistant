import { createSlice } from '@reduxjs/toolkit'

const chatSlice = createSlice({
  name: 'chat',
  initialState: {
    messages: [],       // { role: 'user'|'assistant', content: string, type: 'normal'|'success'|'error' }
    isLoading: false,
    sessionId: null,
    error: null,
  },
  reducers: {
    addMessage: (state, action) => {
      state.messages.push(action.payload)
    },
    setLoading: (state, action) => {
      state.isLoading = action.payload
    },
    setSessionId: (state, action) => {
      state.sessionId = action.payload
    },
    setError: (state, action) => {
      state.error = action.payload
    },
    clearChat: (state) => {
      state.messages = []
      state.sessionId = null
      state.error = null
    },
  },
})

export const { addMessage, setLoading, setSessionId, setError, clearChat } = chatSlice.actions
export default chatSlice.reducer
