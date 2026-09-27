import Papa from 'papaparse'
import csvText from '../../../dados_aracaju_processados.csv?raw'

type CsvRow = {
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
  diff_historico_posto?: string
  mediana_municipal?: string
  diff_mediana_municipal?: string
  diff_mediana_municipal_percentual?: string
  total_registros_serie?: string
  poucos_registros?: string
}

// Representa um registro já convertido para os tipos utilizados pela interface.
export type FuelRecord = {
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
  historicalDifference: number | null
  municipalMedian: number | null
  municipalDifference: number | null
  municipalDifferencePercentage: number | null
  seriesRecordCount: number
  hasFewRecords: boolean
}

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
const parsed = Papa.parse<CsvRow>(csvText, {
  delimiter: ';',
  header: true,
  skipEmptyLines: true,
  transformHeader: (header) => header.replace(/^\uFEFF/, '').trim(),
})

// Normaliza os nomes das propriedades e descarta linhas sem preço válido.
export const fuelRecords: FuelRecord[] = parsed.data
  .map((row, index) => ({
    id: index,
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
    historicalDifference: parseOptionalNumber(row.diff_historico_posto),
    municipalMedian: parseOptionalNumber(row.mediana_municipal),
    municipalDifference: parseOptionalNumber(row.diff_mediana_municipal),
    municipalDifferencePercentage: parseOptionalNumber(row.diff_mediana_municipal_percentual),
    seriesRecordCount: Number(row.total_registros_serie ?? 0),
    hasFewRecords: row.poucos_registros?.toLowerCase() === 'true',
  }))
  .filter((record) => record.station && record.product && Number.isFinite(record.price))
