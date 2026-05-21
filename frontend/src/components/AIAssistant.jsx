import { useState, useRef, useEffect } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { addMessage, setLoading, setSessionId, setError } from '../store/chatSlice'
import { applyAIUpdates, applyEditUpdates, setSuggestions, resetForm } from '../store/formSlice'
import { chatAPI } from '../hooks/useAPI'
import ChatMessage from './ChatMessage'

export default function AIAssistant({ onSaved }) {
  const [input, setInput] = useState('')
  const [saveStatus, setSaveStatus] = useState(null)
  const dispatch = useDispatch()
  const { messages, isLoading, sessionId } = useSelector((s) => s.chat)
  const form = useSelector((s) => s.form)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async () => {
    const text = input.trim()
    if (!text || isLoading) return

    setInput('')
    dispatch(addMessage({ role: 'user', content: text }))
    dispatch(setLoading(true))
    dispatch(setError(null))

    try {
      const history = messages.slice(-10).map((m) => ({
        role: m.role,
        content: m.content,
      }))

      const formState = {
        hcp_name: form.hcp_name || null,
        interaction_type: form.interaction_type || 'Meeting',
        date: form.date || null,
        time: form.time || null,
        attendees: form.attendees || null,
        topics_discussed: form.topics_discussed || null,
        materials_shared: form.materials_shared || [],
        samples_distributed: form.samples_distributed || [],
        sentiment: form.sentiment || 'neutral',
        outcomes: form.outcomes || null,
        follow_up_actions: form.follow_up_actions || null,
        ai_suggested_followups: form.ai_suggested_followups || [],
      }

      const response = await chatAPI.sendMessage({
        message: text,
        formState,
        chatHistory: history,
        sessionId,
      })

      if (response.session_id) dispatch(setSessionId(response.session_id))
      if (response.form_updates && Object.keys(response.form_updates).length > 0) {
        if (response.action_type === 'edit') {
          // edit: only touch the exact fields returned, nothing else
          dispatch(applyEditUpdates({
            updates: response.form_updates,
            explicitFields: Object.keys(response.form_updates),
          }))
        } else {
          // log/summarize/search: apply all non-null fields
          dispatch(applyAIUpdates(response.form_updates))
        }
      }
      if (response.suggestions && response.suggestions.length > 0) {
        dispatch(setSuggestions(response.suggestions))
      }

      const hasUpdates = response.form_updates && Object.keys(response.form_updates).length > 0
      dispatch(addMessage({
        role: 'assistant',
        content: response.assistant_message,
        type: hasUpdates ? 'success' : 'normal',
      }))

    } catch (err) {
      let errMsg = err.response?.data?.detail || err.message || 'Something went wrong.'
      if (errMsg.includes('timeout') || errMsg.includes('ECONNABORTED')) {
        errMsg = 'The AI took too long to respond. Please try again.'
      }
      dispatch(addMessage({ role: 'assistant', content: `❌ ${errMsg}`, type: 'error' }))
      dispatch(setError(errMsg))
    } finally {
      dispatch(setLoading(false))
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const handleSave = async () => {
    setSaveStatus('saving')
    try {
      // Build clean formState — convert empty strings to null for backend
      const cleanForm = {
        hcp_name: form.hcp_name?.trim() || null,
        interaction_type: form.interaction_type || 'Meeting',
        date: form.date?.trim() || null,
        time: form.time?.trim() || null,
        attendees: form.attendees?.trim() || null,
        topics_discussed: form.topics_discussed?.trim() || null,
        materials_shared: Array.isArray(form.materials_shared) ? form.materials_shared : [],
        samples_distributed: Array.isArray(form.samples_distributed) ? form.samples_distributed : [],
        sentiment: form.sentiment || 'neutral',
        outcomes: form.outcomes?.trim() || null,
        follow_up_actions: form.follow_up_actions?.trim() || null,
        ai_suggested_followups: Array.isArray(form.ai_suggested_followups) ? form.ai_suggested_followups : [],
      }

      const history = messages.map((m) => ({ role: m.role, content: m.content }))

      await chatAPI.saveInteraction({
        formState: cleanForm,
        chatHistory: history,
        sessionId,
      })

      setSaveStatus('saved')
      if (onSaved) onSaved()
      setTimeout(() => setSaveStatus(null), 3000)
    } catch (err) {
      console.error('Save error:', err.response?.data || err.message)
      setSaveStatus('error')
      setTimeout(() => setSaveStatus(null), 3000)
    }
  }

  const handleReset = () => {
    dispatch(resetForm())
    dispatch({ type: 'chat/clearChat' })
    setSaveStatus(null)
  }

  return (
    <div className="chat-panel">
      {/* Header */}
      <div className="chat-header">
        <div className="chat-header-left">
          <div className="ai-avatar">🤖</div>
          <div>
            <div className="chat-title">AI Assistant</div>
            <div className="chat-subtitle">Log interaction details via chat</div>
          </div>
        </div>
        <button className="reset-btn" onClick={handleReset} title="Reset form and chat">↺</button>
      </div>

      {/* Messages */}
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-placeholder">
            Log interaction details here (e.g., "Met Dr. Smith, discussed Product X efficacy, positive sentiment, shared brochure") or ask for help.
          </div>
        )}
        {messages.map((msg, i) => (
          <ChatMessage key={i} message={msg} />
        ))}
        {isLoading && (
          <div className="chat-message assistant-message">
            <div className="assistant-avatar">A</div>
            <div className="message-bubble assistant-bubble loading-bubble">
              <span className="dot" /><span className="dot" /><span className="dot" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="chat-input-area">
        <textarea
          className="chat-input"
          placeholder="Describe interaction..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={2}
          disabled={isLoading}
        />
        <button
          className={`log-btn ${isLoading ? 'disabled' : ''}`}
          onClick={sendMessage}
          disabled={isLoading || !input.trim()}
        >
          <span>⚡</span> Log
        </button>
      </div>

      {/* Save */}
      <div className="save-area">
        <button
          className={`save-btn ${saveStatus === 'saved' ? 'saved' : ''} ${saveStatus === 'error' ? 'save-error' : ''}`}
          onClick={handleSave}
          disabled={saveStatus === 'saving'}
        >
          {saveStatus === 'saving' ? '⏳ Saving...' :
           saveStatus === 'saved'  ? '✅ Saved to CRM!' :
           saveStatus === 'error'  ? '❌ Save Failed — check console' :
           '💾 Save Interaction'}
        </button>
      </div>
    </div>
  )
}
