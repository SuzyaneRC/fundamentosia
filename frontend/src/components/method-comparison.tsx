import { useState } from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { methodKeys, methodLabels, type FuelRecord } from '@/lib/fuel-data'

export function MethodComparison({ records }: { records: FuelRecord[] }) {
  const [commonOnly, setCommonOnly] = useState(false)
  const common = records.filter(r => methodKeys.every(k => r.methods[k].evaluated))
  const selected = commonOnly ? common : records
  const summary = methodKeys.map(key => {
    const evaluated = selected.filter(r => r.methods[key].evaluated)
    const flagged = evaluated.filter(r => r.methods[key].anomaly).length
    return { key, name: methodLabels[key], evaluated: evaluated.length, flagged, rate: evaluated.length ? 100 * flagged / evaluated.length : null }
  })
  const pairs = methodKeys.flatMap((a, i) => methodKeys.slice(i + 1).map(b => {
    const shared = selected.filter(r => r.methods[a].evaluated && r.methods[b].evaluated)
    const both = shared.filter(r => r.methods[a].anomaly && r.methods[b].anomaly).length
    const union = shared.filter(r => r.methods[a].anomaly || r.methods[b].anomaly).length
    const same = shared.filter(r => r.methods[a].anomaly === r.methods[b].anomaly).length
    return { a, b, count: shared.length, both, agreement: shared.length ? 100 * same / shared.length : null, jaccard: union ? 100 * both / union : null }
  }))
  const percent = (n: number | null) => n === null ? 'N/D' : `${n.toLocaleString('pt-BR', { maximumFractionDigits: 1 })}%`
  const forestRecords = selected.filter(r => r.methods.random_forest.evaluated)
  const forestGroups = new Map<string, FuelRecord[]>()
  for (const r of forestRecords) {
    const month = `${r.date.getFullYear()}-${String(r.date.getMonth() + 1).padStart(2, '0')}`
    const key = `${r.product} / ${month}`
    forestGroups.set(key, [...(forestGroups.get(key) ?? []), r])
  }
  const diagnosis = [...forestGroups.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([key, rows]) => ({
    key, count: rows.length, flagged: rows.filter(r => r.methods.random_forest.anomaly).length,
    mae: rows.reduce((sum, r) => sum + (r.methods.random_forest.score ?? 0), 0) / rows.length,
  }))
  const products = [...new Set(selected.map(r => r.product))].sort()
  return <Card>
    <CardHeader>
      <CardTitle>Comparação entre métodos</CardTitle>
      <CardDescription>Os filtros de produto, posto e período também se aplicam a esta comparação.</CardDescription>
    </CardHeader>
    <CardContent className="space-y-5">
      <label className="flex items-start gap-2 text-sm"><input type="checkbox" checked={commonOnly} onChange={e => setCommonOnly(e.target.checked)} className="mt-1" />Comparar somente os {common.length.toLocaleString('pt-BR')} registros avaliados pelos quatro métodos</label>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{summary.map(m => <div key={m.key} className="rounded-md border bg-muted/40 p-4">
        <p className="text-sm font-medium">{m.name}</p><p className="mt-2 text-2xl font-semibold">{m.flagged.toLocaleString('pt-BR')}</p>
        <p className="text-xs text-muted-foreground">sinalizados em {m.evaluated.toLocaleString('pt-BR')} avaliados · {percent(m.rate)}</p>
        <p className="mt-1 text-xs text-muted-foreground">Cobertura do recorte: {percent(selected.length ? 100 * m.evaluated / selected.length : null)}</p>
      </div>)}</div>
      <div className="h-56" aria-label="Gráfico de registros sinalizados por método"><ResponsiveContainer width="100%" height="100%"><BarChart data={summary} layout="vertical" margin={{ left: 15, right: 20 }}>
        <CartesianGrid horizontal={false} /><XAxis type="number" allowDecimals={false} /><YAxis dataKey="name" type="category" width={115} tick={{ fontSize: 11 }} /><Tooltip /><Bar dataKey="flagged" name="Sinalizados" fill="#087f6f" radius={[0, 4, 4, 0]} isAnimationActive={false} />
      </BarChart></ResponsiveContainer></div>
      <div><h3 className="mb-2 text-sm font-semibold">Concordância entre pares</h3><Table>
        <TableHeader><TableRow><TableHead>Métodos</TableHead><TableHead>Em comum</TableHead><TableHead>Ambos sinalizam</TableHead><TableHead>Concordância</TableHead><TableHead>Jaccard</TableHead></TableRow></TableHeader>
        <TableBody>{pairs.map(p => <TableRow key={`${p.a}-${p.b}`}><TableCell className="whitespace-nowrap">{methodLabels[p.a]} × {methodLabels[p.b]}</TableCell><TableCell>{p.count}</TableCell><TableCell>{p.both}</TableCell><TableCell>{percent(p.agreement)}</TableCell><TableCell>{percent(p.jaccard)}</TableCell></TableRow>)}</TableBody>
      </Table></div>
      <div><h3 className="mb-2 text-sm font-semibold">Sinalizações por combustível</h3><Table><TableHeader><TableRow><TableHead>Produto</TableHead>{methodKeys.map(k => <TableHead key={k}>{methodLabels[k]}</TableHead>)}</TableRow></TableHeader><TableBody>{products.map(product => <TableRow key={product}><TableCell className="whitespace-nowrap">{product}</TableCell>{methodKeys.map(k => {
        const evaluated = selected.filter(r => r.product === product && r.methods[k].evaluated)
        const flagged = evaluated.filter(r => r.methods[k].anomaly).length
        return <TableCell key={k} className="whitespace-nowrap">{flagged} / {evaluated.length} · {percent(evaluated.length ? 100 * flagged / evaluated.length : null)}</TableCell>
      })}</TableRow>)}</TableBody></Table><p className="mt-2 text-xs text-muted-foreground">Sinalizados / avaliados e taxa por produto. Modelos e padronização independentes para cada combustível.</p></div>
      <details className="rounded-md border p-3"><summary className="cursor-pointer text-sm font-semibold">Diagnóstico temporal do Random Forest</summary>
        <p className="my-3 text-xs text-muted-foreground">{new Set(forestRecords.map(r => r.forestWindow)).size} janelas com previsões no recorte. Os primeiros períodos ficam como histórico para treino e calibração. O limite de cada janela é calculado em datas anteriores ao teste.</p>
        {diagnosis.length ? <div className="max-h-80 overflow-y-auto"><Table><TableHeader><TableRow><TableHead>Produto / mês</TableHead><TableHead>Avaliados</TableHead><TableHead>Sinalizados</TableHead><TableHead>Taxa</TableHead><TableHead>Erro médio</TableHead></TableRow></TableHeader><TableBody>{diagnosis.map(r => <TableRow key={r.key}><TableCell className="whitespace-nowrap">{r.key}</TableCell><TableCell>{r.count}</TableCell><TableCell>{r.flagged}</TableCell><TableCell>{percent(100 * r.flagged / r.count)}</TableCell><TableCell className="whitespace-nowrap">R$ {r.mae.toLocaleString('pt-BR', { minimumFractionDigits: 3, maximumFractionDigits: 3 })}</TableCell></TableRow>)}</TableBody></Table></div> : <p className="text-xs text-muted-foreground">Sem registros de teste neste recorte.</p>}
      </details>
      <p className="text-xs leading-5 text-muted-foreground">Concordância inclui resultados normais e atípicos. Jaccard mede a interseção das sinalizações sobre sua união; N/D indica ausência de sinalizações ou dados. Cada par usa apenas registros avaliados pelos dois métodos. Random Forest avalia janelas de teste posteriores ao treino e à calibração, separadas por combustível. Os demais métodos descrevem a base analisada. Pontuações usam escalas diferentes; sinalizações são indícios para revisão.</p>
    </CardContent>
  </Card>
}
