import { createContext, useContext } from 'react'
import type { FuelRecord } from './fuel-data'

// Tipos e funções das revisões humanas, guardadas apenas no localStorage do navegador.
export const reviewLabels = { pendente: 'Pendente', revisado: 'Revisado', erro: 'Possível erro de dado', justificavel: 'Variação justificável' }
export type ReviewStatus = keyof typeof reviewLabels
export type Review = { status: ReviewStatus; note: string; updatedAt: string; fingerprint: string }
export const STORAGE = 'radar-precos-revisoes-v1'
// Identifica a coleta. Não usa record.id porque ele é só a posição da linha no CSV e pode mudar.
export const recordKey = (record: FuelRecord) => JSON.stringify([record.cnpj, record.product, record.dateLabel])
// "Impressão digital" dos resultados revisados. Se qualquer valor mudar, mesmo uma pontuação em
// casas decimais distantes, a revisão aparece como desatualizada e pede nova conferência.
export const fingerprint = (record: FuelRecord) => JSON.stringify([record.price, record.methods, record.forestThreshold])

// Lê as revisões salvas e descarta entradas inválidas, pois o localStorage pode ser editado.
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


// Dá a qualquer componente dentro de <ReviewProvider> acesso às revisões e à função de salvar.
export function useReviews() {
  const context = useContext(ReviewContext)
  if (!context) throw new Error('Revisões indisponíveis fora do painel.')
  return context
}
