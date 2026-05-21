import { configureStore } from '@reduxjs/toolkit'
import formReducer from './formSlice'
import chatReducer from './chatSlice'

export const store = configureStore({
  reducer: {
    form: formReducer,
    chat: chatReducer,
  },
})
