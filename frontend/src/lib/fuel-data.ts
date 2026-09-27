import Papa from 'papaparse'
import csvText from '../../../base_bruta_aracaju.csv?raw'

type CsvRow = {
  Revenda: string
  'CNPJ da Revenda': string
  Bairro: string
  Produto: string
  'Data da Coleta': string
  'Valor de Venda': string
  Bandeira: string
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
}

// Converte a data brasileira sem aplicar deslocamento de fuso horário.
function parseDate(value: string) {
  const [day, month, year] = value.split('/').map(Number)
  return new Date(year, month - 1, day)
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
  }))
  .filter((record) => record.station && record.product && Number.isFinite(record.price))
