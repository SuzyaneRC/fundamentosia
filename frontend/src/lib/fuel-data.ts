import Papa from 'papaparse'
import csvText from '../../../dados_aracaju_processados.csv?raw'

type CsvRow = {
  [key: string]: string | undefined
  Revenda: string
  'CNPJ da Revenda': string
  Bairro: string
  Produto: string
  'Data da Coleta': string
  'Valor de Venda': string
  Bandeira: string
  preco_anterior?: string
  variacao_absoluta?: string
  variacao_percentual?: string
  media_historica_posto?: string
  mediana_historica_posto?: string
  diff_media_historica_posto?: string
  diff_mediana_historica_posto?: string
  mediana_municipal?: string
  diff_mediana_municipal?: string
  diff_mediana_municipal_percentual?: string
  total_registros_serie?: string
  poucos_registros?: string
}

// Representa um registro já convertido para os tipos utilizados pela interface.
export type FuelRecord = {
  forestPrediction: number | null
  forestThreshold: number | null
  forestWindow: string
  baselinePrediction: number | null
  methods: Record<MethodKey, { evaluated: boolean; anomaly: boolean; score: number | null }>
  id: number
  station: string
  cnpj: string
  neighborhood: string
  product: string
  date: Date
  dateLabel: string
  price: number
  brand: string
  previousPrice: number | null
  absoluteVariation: number | null
  percentageVariation: number | null
  historicalAverage: number | null
  historicalMedian: number | null
  historicalMeanDifference: number | null
  historicalMedianDifference: number | null
  municipalMedian: number | null
  municipalDifference: number | null
  municipalDifferencePercentage: number | null
  seriesRecordCount: number
  hasFewRecords: boolean
}

export const methodLabels = { regressao: 'Baseline', isolation_forest: 'Isolation Forest', kmeans: 'K-Means', random_forest: 'Random Forest' }
export type MethodKey = keyof typeof methodLabels
export const methodKeys = Object.keys(methodLabels) as MethodKey[]
const scoreColumns = { regressao: 'pontuacao_anomalia', isolation_forest: 'score_isolation_forest', kmeans: 'score_kmeans', random_forest: 'erro_abs_random_forest' }

// Converte a data brasileira sem aplicar deslocamento de fuso horário.
function parseDate(value: string) {
  const [day, month, year] = value.split('/').map(Number)
  return new Date(year, month - 1, day)
}

// Converte colunas calculadas que podem estar vazias na primeira coleta da série.
function parseOptionalNumber(value?: string) {
  if (!value) return null
  const number = Number(value.replace(',', '.'))
  return Number.isFinite(number) ? number : null
}

// Lê a base limpa gerada pelo script Python e preserva o CNPJ como texto.
export function parseFuelRecords(csvText: string): FuelRecord[] {
const parsed = Papa.parse<CsvRow>(csvText, {
  delimiter: ';',
  header: true,
  skipEmptyLines: true,
  transformHeader: (header) => header.replace(/^\uFEFF/, '').trim(),
})

// Normaliza os nomes das propriedades e descarta linhas sem preço válido.
const required = ['Revenda', 'CNPJ da Revenda', 'Produto', 'Data da Coleta', 'Valor de Venda', ...methodKeys.map(key => `utilizado_${key}`)]
if (parsed.errors.length || required.some(key => !parsed.meta.fields?.includes(key))) {
  throw new Error('A base de preços está incompleta ou possui formato inválido. Gere novamente o pipeline.')
}
return parsed.data
  .map((row, index) => ({
    methods: Object.fromEntries(methodKeys.map((key) => [key, {
      evaluated: row[`utilizado_${key}`]?.toLowerCase() === 'true',
      anomaly: row[`anomalia_${key}`]?.toLowerCase() === 'true',
      score: parseOptionalNumber(row[scoreColumns[key]]),
    }])) as FuelRecord['methods'],
    id: index,
    forestPrediction: parseOptionalNumber(row.previsao_random_forest),
    forestThreshold: parseOptionalNumber(row.limite_erro_random_forest),
    forestWindow: row.janela_random_forest ?? '',
    baselinePrediction: parseOptionalNumber(row.preco_estimado),
    station: row.Revenda?.trim(),
    cnpj: row['CNPJ da Revenda']?.trim(),
    neighborhood: row.Bairro?.trim(),
    product: row.Produto?.trim(),
    date: parseDate(row['Data da Coleta']),
    dateLabel: row['Data da Coleta'],
    price: Number(row['Valor de Venda']?.replace(',', '.')),
    brand: row.Bandeira?.trim(),
    previousPrice: parseOptionalNumber(row.preco_anterior),
    absoluteVariation: parseOptionalNumber(row.variacao_absoluta),
    percentageVariation: parseOptionalNumber(row.variacao_percentual),
    historicalAverage: parseOptionalNumber(row.media_historica_posto),
    historicalMedian: parseOptionalNumber(row.mediana_historica_posto),
    historicalMeanDifference: parseOptionalNumber(row.diff_media_historica_posto),
    historicalMedianDifference: parseOptionalNumber(row.diff_mediana_historica_posto),
    municipalMedian: parseOptionalNumber(row.mediana_municipal),
    municipalDifference: parseOptionalNumber(row.diff_mediana_municipal),
    municipalDifferencePercentage: parseOptionalNumber(row.diff_mediana_municipal_percentual),
    seriesRecordCount: Number(row.total_registros_serie ?? 0),
    hasFewRecords: row.poucos_registros?.toLowerCase() === 'true',
  }))
  .filter((record) => record.station && record.cnpj && record.product && Number.isFinite(record.price) && record.price > 0 && Number.isFinite(record.date.getTime()))
}

export const fuelRecords = parseFuelRecords(csvText)
