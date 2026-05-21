export default function ChatMessage({ message }) {
  const isUser = message.role === 'user'
  const isSuccess = message.type === 'success'
  const isError = message.type === 'error'

  return (
    <div className={`chat-message ${isUser ? 'user-message' : 'assistant-message'}`}>
      {!isUser && (
        <div className="assistant-avatar">A</div>
      )}
      <div
        className={`message-bubble ${
          isUser ? 'user-bubble' :
          isSuccess ? 'success-bubble' :
          isError ? 'error-bubble' :
          'assistant-bubble'
        }`}
      >
        {message.content}
      </div>
    </div>
  )
}
