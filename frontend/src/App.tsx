import { useMemo, useState, type ReactNode } from 'react'
import {
  ArrowDownToLine,
  Building2,
  CalendarDays,
  ChartNoAxesCombined,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  Droplets,
  Eye,
  FilterX,
  Fuel,
  MapPin,
  RefreshCw,
  SearchCheck,
  TrendingDown,
  TriangleAlert,
} from 'lucide-react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip as ChartTooltip,
  XAxis,
  YAxis,
} from 'recharts'
import Papa from 'papaparse'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { fuelRecords, type FuelRecord } from '@/lib/fuel-data'

const ALL = '__all__'

// Formatadores compartilhados mantêm moeda, números e meses no padrão brasileiro.
const currency = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })
const integer = new Intl.NumberFormat('pt-BR')
const monthFormatter = new Intl.DateTimeFormat('pt-BR', { month: 'short', year: '2-digit' })

function unique(values: string[]) {
  return [...new Set(values)].sort((a, b) => a.localeCompare(b, 'pt-BR'))
}

function toInputDate(date: Date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function median(values: number[]) {
  const sorted = [...values].sort((a, b) => a - b)
  const middle = Math.floor(sorted.length / 2)
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2
}

function shortName(name: string) {
  return name.length > 22 ? `${name.slice(0, 21)}…` : name
}

function formatCnpj(value: string) {
  const digits = value.replace(/\D/g, '').padStart(14, '0')
  return digits.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5')
}

const productColors: Record<string, string> = {
  ETANOL: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  GASOLINA: 'border-sky-200 bg-sky-50 text-sky-700',
  'GASOLINA ADITIVADA': 'border-amber-200 bg-amber-50 text-amber-800',
  DIESEL: 'border-slate-300 bg-slate-100 text-slate-700',
  'DIESEL S10': 'border-violet-200 bg-violet-50 text-violet-700',
  GNV: 'border-cyan-200 bg-cyan-50 text-cyan-800',
}

function productColor(product: string) {
  return productColors[product] ?? 'border-neutral-200 bg-neutral-50 text-neutral-700'
}

function optionalCurrency(value: number | null) {
  return value === null ? 'Não disponível' : currency.format(value)
}

function optionalPercentage(value: number | null) {
  if (value === null) return 'Não disponível'
  const signal = value > 0 ? '+' : ''
  return `${signal}${value.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%`
}

function variationColor(value: number | null) {
  if (value === null || value === 0) return 'text-muted-foreground'
  return value > 0 ? 'text-rose-700' : 'text-teal-700'
}

type FilterSelectProps = {
  label: string
  value: string
  options: string[]
  placeholder: string
  onChange: (value: string) => void
}

function FilterSelect({ label, value, options, placeholder, onChange }: FilterSelectProps) {
  return (
    <label className="grid min-w-0 gap-1.5 text-xs font-medium text-muted-foreground">
      {label}
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger aria-label={label}><SelectValue placeholder={placeholder} /></SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL}>{placeholder}</SelectItem>
          {options.map((option) => <SelectItem key={option} value={option}>{option}</SelectItem>)}
        </SelectContent>
      </Select>
    </label>
  )
}

type StatCardProps = {
  label: string
  value: string
  detail: string
  icon: ReactNode
  accent?: 'teal' | 'amber' | 'red' | 'blue'
}

const accents = {
  teal: 'bg-teal-50 text-teal-700',
  amber: 'bg-amber-50 text-amber-700',
  red: 'bg-rose-50 text-rose-700',
  blue: 'bg-sky-50 text-sky-700',
}

function StatCard({ label, value, detail, icon, accent = 'teal' }: StatCardProps) {
  return (
    <Card className="min-w-0">
      <CardContent className="flex items-start justify-between gap-3 p-4 sm:p-5">
        <div className="min-w-0">
          <p className="text-xs font-medium text-muted-foreground">{label}</p>
          <p className="mt-2 truncate text-2xl font-semibold text-foreground">{value}</p>
          <p className="mt-1 min-h-8 text-[11px] leading-4 text-muted-foreground">{detail}</p>
        </div>
        <span className={`flex size-9 shrink-0 items-center justify-center rounded-md ${accents[accent]}`}>{icon}</span>
      </CardContent>
    </Card>
  )
}

function App() {
  // Opções disponíveis nos filtros, extraídas diretamente da base carregada.
  const products = useMemo(() => unique(fuelRecords.map((item) => item.product)), [])
  const stations = useMemo(() => unique(fuelRecords.map((item) => item.station)), [])
  const neighborhoods = useMemo(() => unique(fuelRecords.map((item) => item.neighborhood)), [])
  const brands = useMemo(() => unique(fuelRecords.map((item) => item.brand)), [])
  const totalStations = useMemo(() => new Set(fuelRecords.map((item) => item.cnpj)).size, [])
  const minDataDate = useMemo(() => new Date(Math.min(...fuelRecords.map((item) => item.date.getTime()))), [])
  const maxDataDate = useMemo(() => new Date(Math.max(...fuelRecords.map((item) => item.date.getTime()))), [])

  const [product, setProduct] = useState(ALL)
  const [station, setStation] = useState(ALL)
  const [neighborhood, setNeighborhood] = useState(ALL)
  const [brand, setBrand] = useState(ALL)
  const [startDate, setStartDate] = useState(toInputDate(minDataDate))
  const [endDate, setEndDate] = useState(toInputDate(maxDataDate))
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)

  // O botão de limpeza só aparece quando o usuário altera o recorte inicial.
  const hasActiveFilters =
    product !== ALL ||
    station !== ALL ||
    neighborhood !== ALL ||
    brand !== ALL ||
    startDate !== toInputDate(minDataDate) ||
    endDate !== toInputDate(maxDataDate)

  // Aplica todos os filtros antes de calcular indicadores, gráficos e tabela.
  const filtered = useMemo(() => {
    const start = new Date(`${startDate}T00:00:00`)
    const end = new Date(`${endDate}T23:59:59`)
    return fuelRecords.filter((item) =>
      (product === ALL || item.product === product) &&
      (station === ALL || item.station === station) &&
      (neighborhood === ALL || item.neighborhood === neighborhood) &&
      (brand === ALL || item.brand === brand) &&
      item.date >= start && item.date <= end,
    )
  }, [brand, endDate, neighborhood, product, startDate, station])

  // Calcula os indicadores resumidos apresentados no topo do painel.
  const stats = useMemo(() => {
    if (!filtered.length) return { average: 0, minimum: 0, maximum: 0, stations: 0 }
    const prices = filtered.map((item) => item.price)
    return {
      average: prices.reduce((sum, price) => sum + price, 0) / prices.length,
      minimum: Math.min(...prices),
      maximum: Math.max(...prices),
      stations: new Set(filtered.map((item) => item.cnpj)).size,
    }
  }, [filtered])

  // Agrupa os preços por mês para comparar média e mediana ao longo do tempo.
  const timeline = useMemo(() => {
    const groups = new Map<string, { date: Date; prices: number[] }>()
    filtered.forEach((item) => {
      const key = `${item.date.getFullYear()}-${String(item.date.getMonth() + 1).padStart(2, '0')}`
      const current = groups.get(key) ?? { date: new Date(item.date.getFullYear(), item.date.getMonth(), 1), prices: [] }
      current.prices.push(item.price)
      groups.set(key, current)
    })
    return [...groups.entries()]
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([, group]) => ({
        month: monthFormatter.format(group.date).replace('.', ''),
        media: Number((group.prices.reduce((sum, price) => sum + price, 0) / group.prices.length).toFixed(2)),
        mediana: Number(median(group.prices).toFixed(2)),
      }))
  }, [filtered])

  // Agrupa por CNPJ para não misturar postos diferentes com o mesmo nome de revenda.
  const stationComparison = useMemo(() => {
    const groups = new Map<string, FuelRecord[]>()
    filtered.forEach((item) => groups.set(item.cnpj, [...(groups.get(item.cnpj) ?? []), item]))
    return [...groups.entries()]
      .map(([cnpj, records]) => ({
        name: shortName(records[0].station),
        fullName: records[0].station,
        cnpj: formatCnpj(cnpj),
        brand: unique(records.map((item) => item.brand)).join(', '),
        average: Number((records.reduce((sum, item) => sum + item.price, 0) / records.length).toFixed(2)),
      }))
      .sort((a, b) => a.average - b.average)
      .slice(0, 8)
  }, [filtered])

  // Calcula o preço médio de cada bairro no recorte selecionado.
  const neighborhoodComparison = useMemo(() => {
    const groups = new Map<string, number[]>()
    filtered.forEach((item) => groups.set(item.neighborhood, [...(groups.get(item.neighborhood) ?? []), item.price]))
    return [...groups.entries()]
      .map(([name, prices]) => ({
        name: shortName(name),
        fullName: name,
        average: Number((prices.reduce((sum, price) => sum + price, 0) / prices.length).toFixed(2)),
      }))
      .sort((a, b) => a.average - b.average)
  }, [filtered])

  // Ordena as coletas mais recentes primeiro e separa apenas a página atual.
  const sortedRecords = useMemo(() => [...filtered].sort((a, b) => b.date.getTime() - a.date.getTime()), [filtered])
  const pageCount = Math.max(1, Math.ceil(sortedRecords.length / pageSize))
  const currentPage = Math.min(page, pageCount)
  const paginatedRecords = useMemo(
    () => sortedRecords.slice((currentPage - 1) * pageSize, currentPage * pageSize),
    [currentPage, pageSize, sortedRecords],
  )

  function resetFilters() {
    setProduct(ALL)
    setStation(ALL)
    setNeighborhood(ALL)
    setBrand(ALL)
    setStartDate(toInputDate(minDataDate))
    setEndDate(toInputDate(maxDataDate))
    setPage(1)
  }

  // Exporta somente os registros do recorte atual no mesmo padrão CSV da base.
  function downloadFiltered() {
    const rows = filtered.map((item) => ({
      Revenda: item.station,
      'CNPJ da Revenda': item.cnpj,
      Bairro: item.neighborhood,
      Produto: item.product,
      'Data da Coleta': item.dateLabel,
      'Valor de Venda': item.price.toFixed(2).replace('.', ','),
      Bandeira: item.brand,
    }))
    const csv = Papa.unparse(rows, { delimiter: ';' })
    const url = URL.createObjectURL(new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8' }))
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = 'precos_aracaju_filtrados.csv'
    anchor.click()
    URL.revokeObjectURL(url)
  }

  return (
    <TooltipProvider>
      <div className="min-h-screen bg-background text-foreground">
        {/* Identificação do painel e ação de exportação rápida. */}
        <header className="border-b bg-card">
          <div className="mx-auto flex min-h-16 max-w-[1600px] items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
            <div className="flex min-w-0 items-center gap-3">
              <span className="flex size-9 shrink-0 items-center justify-center rounded-md bg-primary text-primary-foreground"><Fuel className="size-5" /></span>
              <div className="min-w-0">
                <h1 className="truncate text-base font-semibold">Radar de Preços</h1>
                <p className="truncate text-xs text-muted-foreground">Combustíveis em Aracaju</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge className="hidden sm:inline-flex"><span className="mr-1.5 size-1.5 rounded-full bg-teal-600" />Base atualizada</Badge>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="outline" size="icon" onClick={downloadFiltered} aria-label="Baixar dados filtrados"><ArrowDownToLine /></Button>
                </TooltipTrigger>
                <TooltipContent>Baixar dados filtrados</TooltipContent>
              </Tooltip>
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-[1600px] px-4 py-5 sm:px-6 lg:px-8 lg:py-7">
          <div className="mb-5 flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
            <div>
              <div className="mb-1 flex items-center gap-2 text-xs font-medium text-primary"><MapPin className="size-3.5" />ARACAJU, SERGIPE</div>
              <h2 className="text-xl font-semibold sm:text-2xl">Visão geral dos preços</h2>
              <p className="mt-1 text-sm text-muted-foreground">Acompanhe o comportamento dos combustíveis por posto e período.</p>
            </div>
            <p className="flex items-center gap-1.5 text-xs text-muted-foreground"><CalendarDays className="size-3.5" />Dados até {maxDataDate.toLocaleDateString('pt-BR')}</p>
          </div>

          <div className="grid items-start gap-5 lg:grid-cols-[272px_minmax(0,1fr)]">
            {/* Os filtros controlam todos os indicadores e visualizações da página. */}
            <Card className="lg:sticky lg:top-5">
              <CardHeader className="flex-row items-center justify-between space-y-0">
                <div>
                  <CardTitle>Filtros</CardTitle>
                  <CardDescription className="mt-1">Refine toda a análise</CardDescription>
                </div>
                {hasActiveFilters && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button className="text-rose-600 hover:bg-rose-50 hover:text-rose-700" variant="ghost" size="icon" onClick={resetFilters} aria-label="Limpar filtros"><FilterX /></Button>
                    </TooltipTrigger>
                    <TooltipContent>Limpar filtros</TooltipContent>
                  </Tooltip>
                )}
              </CardHeader>
              <CardContent className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
                <FilterSelect label="Produto" value={product} options={products} placeholder="Todos os produtos" onChange={(value) => { setProduct(value); setPage(1) }} />
                <FilterSelect label="Posto" value={station} options={stations} placeholder="Todos os postos" onChange={(value) => { setStation(value); setPage(1) }} />
                <FilterSelect label="Bairro" value={neighborhood} options={neighborhoods} placeholder="Todos os bairros" onChange={(value) => { setNeighborhood(value); setPage(1) }} />
                <FilterSelect label="Bandeira" value={brand} options={brands} placeholder="Todas as bandeiras" onChange={(value) => { setBrand(value); setPage(1) }} />
                <label className="grid gap-1.5 text-xs font-medium text-muted-foreground">
                  Data inicial
                  <input className="h-9 min-w-0 rounded-md border border-input bg-background px-3 text-sm text-foreground outline-none focus:ring-2 focus:ring-primary/25" type="date" min={toInputDate(minDataDate)} max={endDate} value={startDate} onChange={(event) => { setStartDate(event.target.value); setPage(1) }} />
                </label>
                <label className="grid gap-1.5 text-xs font-medium text-muted-foreground">
                  Data final
                  <input className="h-9 min-w-0 rounded-md border border-input bg-background px-3 text-sm text-foreground outline-none focus:ring-2 focus:ring-primary/25" type="date" min={startDate} max={toInputDate(maxDataDate)} value={endDate} onChange={(event) => { setEndDate(event.target.value); setPage(1) }} />
                </label>
                <div className="flex items-center justify-between border-t pt-4 text-xs text-muted-foreground sm:col-span-2 lg:col-span-1">
                  <span>Registros encontrados</span>
                  <strong className="text-foreground">{integer.format(filtered.length)}</strong>
                </div>
              </CardContent>
            </Card>

            <section className="min-w-0 space-y-5">
              {/* Indicadores principais do recorte selecionado. */}
              <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
                <StatCard label="Preço médio" value={currency.format(stats.average)} detail={`Máximo ${currency.format(stats.maximum)}`} icon={<ChartNoAxesCombined className="size-5" />} accent="teal" />
                <StatCard label="Menor preço" value={currency.format(stats.minimum)} detail="No recorte selecionado" icon={<TrendingDown className="size-5" />} accent="amber" />
                <StatCard label="Postos analisados" value={integer.format(stats.stations)} detail={`${integer.format(totalStations)} na base completa`} icon={<Building2 className="size-5" />} accent="blue" />
                <StatCard label="Registros" value={integer.format(filtered.length)} detail={`${products.length} tipos de combustível`} icon={<SearchCheck className="size-5" />} accent="red" />
              </div>

              {/* Comparações temporais, por posto e por bairro. */}
              <div className="grid gap-5 xl:grid-cols-2">
                <Card>
                  <CardHeader>
                    <CardTitle>Evolução dos preços</CardTitle>
                    <CardDescription>Média e mediana mensal no período selecionado</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="h-[300px] w-full">
                      {timeline.length ? (
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={timeline} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
                            <CartesianGrid vertical={false} stroke="#e7e9e8" />
                            <XAxis dataKey="month" tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: '#66706d' }} minTickGap={28} />
                            <YAxis tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: '#66706d' }} tickFormatter={(value) => `R$ ${Number(value).toFixed(1)}`} domain={['dataMin - 0.3', 'dataMax + 0.3']} />
                            <ChartTooltip formatter={(value) => currency.format(Number(value))} contentStyle={{ borderRadius: 6, borderColor: '#dfe3e1', fontSize: 12 }} />
                            <Line type="monotone" dataKey="media" name="Média" stroke="#087f6f" strokeWidth={2.5} dot={false} activeDot={{ r: 4 }} isAnimationActive={false} />
                            <Line type="monotone" dataKey="mediana" name="Mediana" stroke="#d48a19" strokeWidth={2} strokeDasharray="5 5" dot={false} isAnimationActive={false} />
                          </LineChart>
                        </ResponsiveContainer>
                      ) : <EmptyState />}
                    </div>
                    <div className="mt-3 flex items-center gap-5 text-xs text-muted-foreground">
                      <span className="flex items-center gap-2"><i className="h-0.5 w-5 bg-primary" />Média</span>
                      <span className="flex items-center gap-2"><i className="h-0.5 w-5 bg-amber-600" />Mediana</span>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Postos com menor média</CardTitle>
                    <CardDescription>Comparação no recorte selecionado</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="h-[332px] w-full">
                      {stationComparison.length ? (
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={stationComparison} layout="vertical" margin={{ top: 0, right: 16, left: 5, bottom: 0 }}>
                            <CartesianGrid horizontal={false} stroke="#e7e9e8" />
                            <XAxis type="number" hide domain={[0, 'dataMax + 1']} />
                            <YAxis dataKey="name" type="category" width={132} tickLine={false} axisLine={false} tick={{ fontSize: 10, fill: '#4e5955' }} />
                            <ChartTooltip
                              cursor={{ fill: '#f1f4f3' }}
                              content={({ active, payload }) => {
                                const item = payload?.[0]?.payload as (typeof stationComparison)[number] | undefined
                                if (!active || !item) return null
                                return (
                                  <div className="max-w-72 rounded-md border bg-popover p-3 text-xs text-popover-foreground shadow-md">
                                    <p className="font-semibold leading-4">{item.fullName}</p>
                                    <dl className="mt-2 grid grid-cols-[64px_1fr] gap-x-2 gap-y-1 text-muted-foreground">
                                      <dt>Bandeira</dt><dd className="font-medium text-foreground">{item.brand}</dd>
                                      <dt>CNPJ</dt><dd className="font-medium text-foreground">{item.cnpj}</dd>
                                      <dt>Média</dt><dd className="font-semibold text-primary">{currency.format(item.average)}</dd>
                                    </dl>
                                  </div>
                                )
                              }}
                            />
                            <Bar dataKey="average" name="Preço médio" fill="#087f6f" radius={[0, 4, 4, 0]} maxBarSize={20} isAnimationActive={false} />
                          </BarChart>
                        </ResponsiveContainer>
                      ) : <EmptyState />}
                    </div>
                  </CardContent>
                </Card>

                <Card className="xl:col-span-2">
                  <CardHeader className="flex-row items-start justify-between gap-4 space-y-0">
                    <div>
                      <CardTitle>Preço médio por bairro</CardTitle>
                      <CardDescription className="mt-1">Comparação em ordem crescente no recorte selecionado</CardDescription>
                    </div>
                    <Badge variant="outline" className="whitespace-nowrap">{neighborhoodComparison.length} bairros</Badge>
                  </CardHeader>
                  <CardContent>
                    <div className="max-h-[520px] min-h-[320px] w-full overflow-y-auto pr-1">
                      {neighborhoodComparison.length ? (
                        <div style={{ height: Math.max(320, neighborhoodComparison.length * 34) }}>
                          <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={neighborhoodComparison} layout="vertical" margin={{ top: 0, right: 18, left: 5, bottom: 0 }}>
                              <CartesianGrid horizontal={false} stroke="#e7e9e8" />
                              <XAxis type="number" tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: '#66706d' }} tickFormatter={(value) => `R$ ${Number(value).toFixed(1)}`} domain={[0, 'dataMax + 1']} />
                              <YAxis dataKey="name" type="category" width={112} tickLine={false} axisLine={false} tick={{ fontSize: 10, fill: '#4e5955' }} />
                              <ChartTooltip formatter={(value) => currency.format(Number(value))} labelFormatter={(_, payload) => payload?.[0]?.payload?.fullName ?? ''} contentStyle={{ borderRadius: 6, borderColor: '#dfe3e1', fontSize: 12 }} />
                              <Bar dataKey="average" name="Preço médio" fill="#d48a19" radius={[0, 4, 4, 0]} maxBarSize={18} isAnimationActive={false} />
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                      ) : <EmptyState />}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Tabela completa com paginação e exportação dos dados filtrados. */}
              <Card>
                <CardHeader className="flex-row items-start justify-between gap-4 space-y-0">
                  <div>
                    <CardTitle>Registros mais recentes</CardTitle>
                    <CardDescription className="mt-1">Últimas coletas disponíveis no recorte atual</CardDescription>
                  </div>
                  <Button variant="outline" size="sm" onClick={downloadFiltered}><ArrowDownToLine />Exportar</Button>
                </CardHeader>
                <CardContent className="px-0 pb-0">
                  {paginatedRecords.length ? (
                    <>
                      <RecordsTable records={paginatedRecords} />
                      <Pagination
                        page={currentPage}
                        pageCount={pageCount}
                        pageSize={pageSize}
                        total={sortedRecords.length}
                        onPageChange={setPage}
                        onPageSizeChange={(size) => { setPageSize(size); setPage(1) }}
                      />
                    </>
                  ) : <div className="px-5 pb-5"><EmptyState /></div>}
                </CardContent>
              </Card>
            </section>
          </div>
        </main>
      </div>
    </TooltipProvider>
  )
}

function EmptyState() {
  return (
    <div className="flex h-full min-h-40 flex-col items-center justify-center gap-2 text-center text-muted-foreground">
      <RefreshCw className="size-5" />
      <p className="text-sm">Nenhum registro para este filtro.</p>
    </div>
  )
}

function RecordsTable({ records }: { records: FuelRecord[] }) {
  return (
    <Table className="table-fixed sm:table-auto">
      <TableHeader>
        <TableRow>
          <TableHead className="w-[34%] sm:w-auto">Posto</TableHead>
          <TableHead className="w-[32%] sm:w-auto">Produto</TableHead>
          <TableHead className="hidden md:table-cell">Bairro</TableHead>
          <TableHead className="hidden lg:table-cell">Variação</TableHead>
          <TableHead className="hidden xl:table-cell">Mediana municipal</TableHead>
          <TableHead className="hidden sm:table-cell">Data</TableHead>
          <TableHead className="w-[23%] text-right sm:w-auto">Preço</TableHead>
          <TableHead className="w-[11%] sm:w-12"><span className="sr-only">Detalhes</span></TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {records.map((item) => (
          <TableRow key={item.id}>
            <TableCell className="w-[42%] max-w-48 font-medium"><span className="block truncate">{item.station}</span></TableCell>
            <TableCell>
              <Badge variant="outline" className={`h-auto min-h-6 max-w-full whitespace-normal py-1 text-[10px] leading-3 ${productColor(item.product)}`}>
                <Droplets className="mr-1 size-3 shrink-0" />{item.product}
              </Badge>
            </TableCell>
            <TableCell className="hidden md:table-cell">{item.neighborhood}</TableCell>
            <TableCell className={`hidden whitespace-nowrap font-medium lg:table-cell ${variationColor(item.percentageVariation)}`}>{optionalPercentage(item.percentageVariation)}</TableCell>
            <TableCell className="hidden whitespace-nowrap text-muted-foreground xl:table-cell">{optionalCurrency(item.municipalMedian)}</TableCell>
            <TableCell className="hidden whitespace-nowrap text-muted-foreground sm:table-cell">{item.dateLabel}</TableCell>
            <TableCell className="whitespace-nowrap text-right font-semibold">{currency.format(item.price)}</TableCell>
            <TableCell><RecordDetails record={item} /></TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

// Apresenta as variáveis temporais e municipais calculadas para uma coleta.
function RecordDetails({ record }: { record: FuelRecord }) {
  return (
    <Dialog>
      <Tooltip>
        <TooltipTrigger asChild>
          <DialogTrigger asChild>
            <Button variant="ghost" size="icon" className="size-8" aria-label={`Ver detalhes de ${record.station}`}><Eye /></Button>
          </DialogTrigger>
        </TooltipTrigger>
        <TooltipContent>Ver análise do registro</TooltipContent>
      </Tooltip>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Detalhes da coleta</DialogTitle>
          <DialogDescription>{record.product} em {record.dateLabel}</DialogDescription>
        </DialogHeader>

        <div className="mt-5 border-y py-4">
          <p className="font-semibold leading-5">{record.station}</p>
          <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
            <span>CNPJ: {formatCnpj(record.cnpj)}</span>
            <span>Bandeira: {record.brand}</span>
            <span>Bairro: {record.neighborhood}</span>
          </div>
        </div>

        <div className="mt-5">
          <h4 className="text-sm font-semibold">Comparação temporal</h4>
          <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3">
            <DetailMetric label="Preço atual" value={currency.format(record.price)} />
            <DetailMetric label="Preço anterior" value={optionalCurrency(record.previousPrice)} />
            <DetailMetric label="Variação" value={optionalPercentage(record.percentageVariation)} tone={variationColor(record.percentageVariation)} />
            <DetailMetric label="Média histórica" value={optionalCurrency(record.historicalAverage)} />
            <DetailMetric label="Mediana histórica" value={optionalCurrency(record.historicalMedian)} />
            <DetailMetric label="Diferença histórica" value={optionalCurrency(record.historicalDifference)} tone={variationColor(record.historicalDifference)} />
          </div>
        </div>

        <div className="mt-5">
          <h4 className="text-sm font-semibold">Comparação municipal</h4>
          <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3">
            <DetailMetric label="Preço do posto" value={currency.format(record.price)} />
            <DetailMetric label="Mediana municipal" value={optionalCurrency(record.municipalMedian)} />
            <DetailMetric label="Diferença" value={optionalPercentage(record.municipalDifferencePercentage)} tone={variationColor(record.municipalDifferencePercentage)} />
          </div>
        </div>

        <div className={`mt-5 flex items-start gap-2 rounded-md border p-3 text-xs ${record.hasFewRecords ? 'border-amber-200 bg-amber-50 text-amber-800' : 'border-teal-200 bg-teal-50 text-teal-800'}`}>
          {record.hasFewRecords && <TriangleAlert className="mt-0.5 size-4 shrink-0" />}
          <p><strong>{record.seriesRecordCount} registros</strong> na série deste posto e produto. {record.hasFewRecords ? 'A série possui poucos dados para uma comparação histórica confiável.' : 'A série possui histórico suficiente para as comparações iniciais.'}</p>
        </div>
      </DialogContent>
    </Dialog>
  )
}

function DetailMetric({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div className="min-w-0 rounded-md bg-muted p-3">
      <p className="text-[11px] text-muted-foreground">{label}</p>
      <p className={`mt-1 break-words text-sm font-semibold ${tone ?? 'text-foreground'}`}>{value}</p>
    </div>
  )
}

type PaginationProps = {
  page: number
  pageCount: number
  pageSize: number
  total: number
  onPageChange: (page: number) => void
  onPageSizeChange: (size: number) => void
}

function Pagination({ page, pageCount, pageSize, total, onPageChange, onPageSizeChange }: PaginationProps) {
  // Limites usados no texto "Exibindo X–Y de Z".
  const firstRecord = total ? (page - 1) * pageSize + 1 : 0
  const lastRecord = Math.min(page * pageSize, total)

  return (
    <div className="flex flex-col gap-3 border-t px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
      <p className="text-xs text-muted-foreground">
        Exibindo <strong className="font-medium text-foreground">{integer.format(firstRecord)}–{integer.format(lastRecord)}</strong> de <strong className="font-medium text-foreground">{integer.format(total)}</strong>
      </p>
      <div className="flex flex-wrap items-center justify-between gap-3 sm:justify-end">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>Por página</span>
          <Select value={String(pageSize)} onValueChange={(value) => onPageSizeChange(Number(value))}>
            <SelectTrigger className="w-[68px]" aria-label="Registros por página"><SelectValue /></SelectTrigger>
            <SelectContent>
              {[10, 25, 50].map((size) => <SelectItem key={size} value={String(size)}>{size}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <span className="min-w-20 text-center text-xs font-medium">{page} de {pageCount}</span>
        <div className="flex items-center gap-1">
          <Tooltip>
            <TooltipTrigger asChild><Button variant="outline" size="icon" className="size-8" disabled={page === 1} onClick={() => onPageChange(1)} aria-label="Primeira página"><ChevronsLeft /></Button></TooltipTrigger>
            <TooltipContent>Primeira página</TooltipContent>
          </Tooltip>
          <Tooltip>
            <TooltipTrigger asChild><Button variant="outline" size="icon" className="size-8" disabled={page === 1} onClick={() => onPageChange(page - 1)} aria-label="Página anterior"><ChevronLeft /></Button></TooltipTrigger>
            <TooltipContent>Página anterior</TooltipContent>
          </Tooltip>
          <Tooltip>
            <TooltipTrigger asChild><Button variant="outline" size="icon" className="size-8" disabled={page === pageCount} onClick={() => onPageChange(page + 1)} aria-label="Próxima página"><ChevronRight /></Button></TooltipTrigger>
            <TooltipContent>Próxima página</TooltipContent>
          </Tooltip>
          <Tooltip>
            <TooltipTrigger asChild><Button variant="outline" size="icon" className="size-8" disabled={page === pageCount} onClick={() => onPageChange(pageCount)} aria-label="Última página"><ChevronsRight /></Button></TooltipTrigger>
            <TooltipContent>Última página</TooltipContent>
          </Tooltip>
        </div>
      </div>
    </div>
  )
}

export default App
