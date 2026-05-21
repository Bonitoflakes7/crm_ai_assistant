import { useSelector, useDispatch } from 'react-redux'
import { updateField } from '../store/formSlice'

const INTERACTION_TYPES = ['Meeting', 'Call', 'Email', 'Conference', 'Other']

export default function InteractionForm() {
  const form = useSelector((s) => s.form)
  const dispatch = useDispatch()

  const set = (field) => (e) => {
    dispatch(updateField({ field, value: e.target.value }))
  }

  const setDirect = (field, value) => {
    dispatch(updateField({ field, value }))
  }

  return (
    <div className="form-panel">
      <div className="form-panel-inner">
        <h2 className="section-title">Interaction Details</h2>

        {/* Row 1: HCP Name + Interaction Type */}
        <div className="form-row">
          <div className="form-group">
            <label className="form-label">HCP Name</label>
            <input
              className="form-input"
              placeholder="Search or select HCP..."
              value={form.hcp_name || ''}
              onChange={set('hcp_name')}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Interaction Type</label>
            <select
              className="form-input form-select"
              value={form.interaction_type || 'Meeting'}
              onChange={set('interaction_type')}
            >
              {INTERACTION_TYPES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Row 2: Date + Time */}
        <div className="form-row">
          <div className="form-group">
            <label className="form-label">Date</label>
            <input
              type="date"
              className="form-input"
              value={form.date || ''}
              onChange={set('date')}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Time</label>
            <input
              type="time"
              className="form-input"
              value={form.time || ''}
              onChange={set('time')}
            />
          </div>
        </div>

        {/* Attendees */}
        <div className="form-group full-width">
          <label className="form-label">Attendees</label>
          <input
            className="form-input"
            placeholder="Enter names or search..."
            value={form.attendees || ''}
            onChange={set('attendees')}
          />
        </div>

        {/* Topics Discussed */}
        <div className="form-group full-width">
          <label className="form-label">Topics Discussed</label>
          <div className="textarea-wrapper">
            <textarea
              className="form-textarea"
              placeholder="Enter key discussion points..."
              value={form.topics_discussed || ''}
              onChange={set('topics_discussed')}
              rows={4}
            />
          </div>
          <button className="voice-btn">
            <span className="voice-icon">✦</span> Summarize from Voice Note (Requires Consent)
          </button>
        </div>

        {/* Materials Shared */}
        <div className="form-group full-width">
          <label className="form-label">Materials Shared / Samples Distributed</label>

          <div className="materials-card">
            <div className="materials-header">
              <span className="materials-label">Materials Shared</span>
              <button className="icon-btn">🔍 Search/Add</button>
            </div>
            {form.materials_shared && form.materials_shared.length > 0 ? (
              <ul className="materials-list">
                {form.materials_shared.map((m, i) => (
                  <li key={i} className="material-tag">
                    <span>📄</span> {m}
                    <button
                      className="remove-btn"
                      onClick={() => setDirect('materials_shared', form.materials_shared.filter((_, idx) => idx !== i))}
                    >×</button>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="empty-label">No materials added.</p>
            )}
          </div>

          <div className="materials-card" style={{ marginTop: '8px' }}>
            <div className="materials-header">
              <span className="materials-label">Samples Distributed</span>
              <button className="icon-btn">⊕ Add Sample</button>
            </div>
            {form.samples_distributed && form.samples_distributed.length > 0 ? (
              <ul className="materials-list">
                {form.samples_distributed.map((s, i) => (
                  <li key={i} className="material-tag">
                    <span>💊</span> {s}
                    <button
                      className="remove-btn"
                      onClick={() => setDirect('samples_distributed', form.samples_distributed.filter((_, idx) => idx !== i))}
                    >×</button>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="empty-label">No samples added.</p>
            )}
          </div>
        </div>

        {/* Sentiment */}
        <div className="form-group full-width">
          <label className="form-label">Observed/Inferred HCP Sentiment</label>
          <div className="sentiment-row">
            {['positive', 'neutral', 'negative'].map((s) => (
              <label key={s} className={`sentiment-option ${form.sentiment === s ? 'active-' + s : ''}`}>
                <input
                  type="radio"
                  name="sentiment"
                  value={s}
                  checked={form.sentiment === s}
                  onChange={() => setDirect('sentiment', s)}
                />
                <span className="sentiment-dot" data-sentiment={s} />
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </label>
            ))}
          </div>
        </div>

        {/* Outcomes */}
        <div className="form-group full-width">
          <label className="form-label">Outcomes</label>
          <textarea
            className="form-textarea"
            placeholder="Key outcomes or agreements..."
            value={form.outcomes || ''}
            onChange={set('outcomes')}
            rows={3}
          />
        </div>

        {/* Follow-up Actions */}
        <div className="form-group full-width">
          <label className="form-label">Follow-up Actions</label>
          <textarea
            className="form-textarea"
            placeholder="Enter next steps or tasks..."
            value={form.follow_up_actions || ''}
            onChange={set('follow_up_actions')}
            rows={3}
          />
        </div>

        {/* AI Suggested Follow-ups */}
        {form.ai_suggested_followups && form.ai_suggested_followups.length > 0 && (
          <div className="form-group full-width">
            <label className="form-label ai-label">✦ AI Suggested Follow-ups:</label>
            <ul className="suggestions-list">
              {form.ai_suggested_followups.map((s, i) => (
                <li
                  key={i}
                  className="suggestion-item"
                  onClick={() => {
                    const current = form.follow_up_actions || ''
                    setDirect('follow_up_actions', current ? current + '\n• ' + s : '• ' + s)
                  }}
                >
                  + {s}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}
