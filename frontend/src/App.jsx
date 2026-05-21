import { useState } from 'react'
import InteractionForm from './components/InteractionForm'
import AIAssistant from './components/AIAssistant'

export default function App() {
  const [savedCount, setSavedCount] = useState(0)

  return (
    <div className="app">
      {/* Top bar */}
      <header className="topbar">
        <div className="topbar-inner">
          <div className="brand">
            <span className="brand-icon">⚕</span>
            <span className="brand-name">HCP CRM</span>
          </div>
          <nav className="topbar-nav">
            <span className="nav-item active">Log Interaction</span>
            <span className="nav-item">My HCPs</span>
            <span className="nav-item">Reports</span>
          </nav>
          {savedCount > 0 && (
            <div className="saved-badge">{savedCount} interaction{savedCount > 1 ? 's' : ''} saved</div>
          )}
        </div>
      </header>

      {/* Page title */}
      <div className="page-header">
        <h1 className="page-title">Log HCP Interaction</h1>
        <p className="page-subtitle">Use the AI Assistant on the right to fill this form automatically</p>
      </div>

      {/* Split layout */}
      <div className="split-layout">
        <InteractionForm />
        <AIAssistant onSaved={() => setSavedCount((c) => c + 1)} />
      </div>
    </div>
  )
}
