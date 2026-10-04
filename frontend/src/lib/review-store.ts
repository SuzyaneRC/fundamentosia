import { createContext, useContext } from 'react'
import type { FuelRecord } from './fuel-data'

export const reviewLabels = { pendente: 'Pendente', revisado: 'Revisado', erro: 'Possível erro de dado', justificavel: 'Variação justificável' }
export type ReviewStatus = keyof typeof reviewLabels
export type Review = { status: ReviewStatus; note: string; updatedAt: string; fingerprint: string }
export const STORAGE = 'radar-precos-revisoes-v1'
export const recordKey = (record: FuelRecord) => JSON.stringify([record.cnpj, record.product, record.dateLabel])
export const fingerprint = (record: FuelRecord) => JSON.stringify([record.price, record.methods, record.forestThreshold])

export function readReviews(): Record<string, Review> {
  try {
    const raw: unknown = JSON.parse(localStorage.getItem(STORAGE) ?? '{}')
    if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return {}
    return Object.fromEntries(Object.entries(raw).filter(([, r]) => r && typeof r === 'object' && Object.hasOwn(reviewLabels, r.status) && typeof r.note === 'string' && r.note.length <= 1000 && typeof r.updatedAt === 'string' && typeof r.fingerprint === 'string'))
  } catch { return {} }
}

type ReviewContextValue = {
  reviews: Record<string, Review>
  error: string
  save: (record: FuelRecord, status: ReviewStatus, note: string) => boolean
}
export const ReviewContext = createContext<ReviewContextValue | null>(null)


export function useReviews() {
  const context = useContext(ReviewContext)
  if (!context) throw new Error('Revisões indisponíveis fora do painel.')
  return context
}
