import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { fingerprint, recordKey, reviewLabels, useReviews, type ReviewStatus } from '@/lib/review-store'
import type { FuelRecord } from '@/lib/fuel-data'

export function RecordReview({ record }: { record: FuelRecord }) {
  const { reviews, save, error } = useReviews()
  const review = reviews[recordKey(record)]
  const [status, setStatus] = useState<ReviewStatus>(review?.status ?? 'pendente')
  const [note, setNote] = useState(review?.note ?? '')
  const [saved, setSaved] = useState(false)
  const outdated = review && review.fingerprint !== fingerprint(record)
  return <div className="mt-5 space-y-3 border-t pt-4">
    <h4 className="text-sm font-semibold">Revisão do alerta</h4>
    <p className="text-xs text-muted-foreground">A revisão fica neste navegador. Exporte a tabela para guardar ou compartilhar as observações; ela não altera as sinalizações dos modelos.</p>
    {outdated && <p role="status" className="text-xs text-amber-800">Os resultados mudaram desde a última revisão. Confira os indicadores antes de salvar novamente.</p>}
    <label className="grid gap-1 text-xs">Situação da revisão<select aria-label="Situação da revisão" className="h-9 rounded-md border bg-background px-2 text-sm" value={status} onChange={e => { setStatus(e.target.value as ReviewStatus); setSaved(false) }}>{Object.entries(reviewLabels).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>
    <label className="grid gap-1 text-xs">Observações<textarea aria-label="Observações da revisão" className="min-h-20 rounded-md border bg-background p-2 text-sm" value={note} maxLength={1000} onChange={e => { setNote(e.target.value); setSaved(false) }} /></label>
    <Button size="sm" onClick={() => setSaved(save(record, status, note.trim()))}>Salvar revisão</Button>
    {saved && <p role="status" className="text-xs text-teal-700">Revisão salva neste navegador.</p>}
    {error && <p role="alert" className="text-xs text-rose-700">{error}</p>}
    {review && <p className="text-xs text-muted-foreground">Última revisão: {new Date(review.updatedAt).toLocaleString('pt-BR')}</p>}
  </div>
}
