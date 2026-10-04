import { useState, type ReactNode } from 'react'
import type { FuelRecord } from './fuel-data'
import { ReviewContext, readReviews, STORAGE, recordKey, fingerprint, type ReviewStatus } from './review-store'

export function ReviewProvider({ children }: { children: ReactNode }) {
  const [reviews, setReviews] = useState(readReviews)
  const [error, setError] = useState('')
  function save(record: FuelRecord, status: ReviewStatus, note: string) {
    const next = { ...reviews, [recordKey(record)]: { status, note: note.slice(0, 1000), updatedAt: new Date().toISOString(), fingerprint: fingerprint(record) } }
    try {
      localStorage.setItem(STORAGE, JSON.stringify(next))
      setReviews(next)
      setError('')
      return true
    } catch {
      setError('Não foi possível salvar a revisão neste navegador. Verifique se o armazenamento local está disponível.')
      return false
    }
  }
  return <ReviewContext.Provider value={{ reviews, save, error }}>{children}</ReviewContext.Provider>
}
