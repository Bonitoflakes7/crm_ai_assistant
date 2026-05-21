import { createSlice } from '@reduxjs/toolkit'

const initialFormState = {
  hcp_name: '',
  interaction_type: 'Meeting',
  date: '',
  time: '',
  attendees: '',
  topics_discussed: '',
  materials_shared: [],
  samples_distributed: [],
  sentiment: 'neutral',
  outcomes: '',
  follow_up_actions: '',
  ai_suggested_followups: [],
}

const formSlice = createSlice({
  name: 'form',
  initialState: initialFormState,
  reducers: {
    // Called after log_interaction — applies all non-null fields
    applyAIUpdates: (state, action) => {
      const updates = action.payload
      Object.keys(updates).forEach((key) => {
        if (!(key in state)) return
        const val = updates[key]

        if (val === null || val === undefined) return
        if (typeof val === 'string' && val.trim() === '') return

        // Arrays: only overwrite if incoming array is non-empty
        if (Array.isArray(val)) {
          if (val.length > 0) state[key] = val
          return
        }

        state[key] = val
      })
    },

    // Called after edit_interaction — applies ONLY the specific fields returned
    // Extra guard: never let sentiment change unless it's explicitly in the update
    applyEditUpdates: (state, action) => {
      const { updates, explicitFields } = action.payload
      // explicitFields is the list of keys the edit tool returned
      Object.keys(updates).forEach((key) => {
        if (!(key in state)) return
        const val = updates[key]
        if (val === null || val === undefined) return
        if (typeof val === 'string' && val.trim() === '') return
        if (Array.isArray(val) && val.length === 0) return
        state[key] = val
      })
    },

    updateField: (state, action) => {
      const { field, value } = action.payload
      if (field in state) state[field] = value
    },

    setSuggestions: (state, action) => {
      state.ai_suggested_followups = action.payload
    },

    resetForm: () => initialFormState,
  },
})

export const {
  applyAIUpdates,
  applyEditUpdates,
  updateField,
  setSuggestions,
  resetForm,
} = formSlice.actions
export default formSlice.reducer
