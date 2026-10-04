import { chromium } from 'playwright-core'
import path from 'node:path'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const browser = await chromium.launch({
  executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  headless: true,
})

const results = []

for (const config of [
  { name: 'desktop', width: 1440, height: 1000 },
  { name: 'mobile', width: 390, height: 844 },
]) {
  const page = await browser.newPage({ viewport: { width: config.width, height: config.height } })
  const errors = []
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text())
  })
  page.on('pageerror', (error) => errors.push(error.message))

  await page.goto(process.env.PREVIEW_URL ?? 'http://127.0.0.1:5173/', { waitUntil: 'domcontentloaded', timeout: 60000 })
  await page.getByText('Comparação entre métodos', { exact: true }).waitFor()
  const commonPopulation = page.getByRole('checkbox', { name: /Comparar somente/ })
  const commonCount = (await commonPopulation.locator('..').textContent()).match(/somente os ([\d.]+)/)[1]
  await commonPopulation.check()
  assert.equal(await page.getByText(`avaliados ·`, { exact: false }).filter({ hasText: `sinalizados em ${commonCount} avaliados` }).count(), 4)
  await commonPopulation.uncheck()
  await page.getByRole('combobox', { name: 'Sinalizações na tabela' }).click()
  await page.getByRole('option', { name: 'Pelo menos um método', exact: true }).click()
  const dataRows = page.locator('table').last().locator('tbody tr')
  assert.ok(await dataRows.count() > 0)
  for (const text of await dataRows.allTextContents()) assert.match(text, /[1-4] sinalizam/)
  const downloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Exportar', exact: true }).click()
  const download = await downloadPromise
  assert.equal(download.suggestedFilename(), 'precos_aracaju_filtrados.csv')
  const csv = await readFile(await download.path(), 'utf8')
  assert.ok(csv.includes('utilizado_random_forest'))
  assert.ok(csv.includes('observacoes_revisao'))
  await page.getByRole('combobox', { name: 'Sinalizações na tabela' }).click()
  await page.getByRole('option', { name: 'Todos os registros', exact: true }).click()
  await page.getByRole('button', { name: /Ver detalhes de/ }).first().click()
  await page.getByLabel('Situação da revisão', { exact: true }).selectOption('revisado')
  await page.getByLabel('Observações da revisão').fill('Conferência inicial dos indicadores do posto.')
  await page.getByRole('button', { name: 'Salvar revisão' }).click()
  assert.ok(await page.getByText('Revisão salva neste navegador.', { exact: true }).isVisible())
  await page.getByRole('button', { name: 'Fechar' }).click()
  await page.reload({ waitUntil: 'domcontentloaded' })
  await page.getByText('Comparação entre métodos', { exact: true }).waitFor()
  await page.getByRole('button', { name: /Ver detalhes de/ }).first().click()
  assert.equal(await page.getByLabel('Situação da revisão', { exact: true }).inputValue(), 'revisado')
  assert.equal(await page.getByLabel('Observações da revisão').inputValue(), 'Conferência inicial dos indicadores do posto.')
  await page.getByRole('button', { name: 'Fechar' }).click()
  let interactions = null
  if (config.name === 'desktop') {
    const clearButton = page.getByRole('button', { name: 'Limpar filtros' })
    const clearInitiallyHidden = await clearButton.count() === 0
    const stationSelect = page.getByRole('combobox', { name: 'Posto' })
    await stationSelect.click()
    await page.getByRole('option', { name: 'ALPHA COMERCIAL DE COMBUSTIVEIS LTDA', exact: true }).click()
    const clearVisible = await clearButton.isVisible()
    const clearColor = await clearButton.evaluate((element) => getComputedStyle(element).color)
    const selectFits = await stationSelect.evaluate((element) => {
      const field = element.getBoundingClientRect()
      const panel = element.closest('[class*="rounded-lg"]')?.getBoundingClientRect()
      return Boolean(panel && field.right <= panel.right && field.left >= panel.left)
    })
    await stationSelect.click()
    await page.getByRole('option', { name: 'Todos os postos', exact: true }).click()
    await page.getByRole('button', { name: 'Próxima página' }).click()
    const paginationAdvanced = await page.getByText(/2 de \d+/).isVisible()
    await page.getByRole('button', { name: 'Primeira página' }).click()
    await page.getByRole('combobox', { name: 'Produto' }).click()
    await page.getByRole('option', { name: 'GASOLINA', exact: true }).click()
    await page.waitForTimeout(300)
    await page.locator('.recharts-bar-rectangle path').first().hover()
    const stationDetailsVisible = await page.getByText('CNPJ', { exact: true }).isVisible()
    interactions = { clearInitiallyHidden, clearVisible, clearColor, selectFits, paginationAdvanced, stationDetailsVisible }
  }

  const screenshot = path.join(process.env.TEMP, `radar-precos-${config.name}.png`)
  await page.screenshot({ path: screenshot, fullPage: true })
  const tableScrollAvailable = await page.locator('table').last().evaluate((table) => {
    const container = table.parentElement
    return Boolean(container && container.scrollWidth > container.clientWidth)
  })
  await page.getByRole('button', { name: /Ver detalhes de/ }).first().click()
  const temporalDetailsVisible = await page.getByText('Comparação temporal', { exact: true }).isVisible()
  const municipalDetailsVisible = await page.getByText('Comparação municipal', { exact: true }).isVisible()
  const modelDetailsVisible = await page.getByText('Resultados dos métodos', { exact: true }).isVisible()
  const dialogFits = await page.getByRole('dialog').evaluate((element) => element.scrollWidth <= element.clientWidth)
  const detailScreenshot = path.join(process.env.TEMP, `radar-precos-${config.name}-details.png`)
  await page.screenshot({ path: detailScreenshot })
  await page.getByRole('button', { name: 'Fechar' }).click()
  results.push({
    viewport: config.name,
    title: await page.title(),
    heading: await page.getByRole('heading', { name: 'Visão geral dos preços' }).textContent(),
    screenshot,
    detailScreenshot,
    horizontalOverflow: await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth),
    interactions: { ...(interactions ?? {}), tableScrollAvailable, temporalDetailsVisible, municipalDetailsVisible, modelDetailsVisible, dialogFits },
    chartGeometry: await page.evaluate(() => ({
      bars: [...document.querySelectorAll('.recharts-bar-rectangle path')].map((element) => Math.round(element.getBoundingClientRect().width)),
      lines: [...document.querySelectorAll('.recharts-line-curve')].map((element) => Math.round(element.getBoundingClientRect().width)),
    })),
    errors,
  })
  assert.equal(errors.length, 0)
  assert.ok(temporalDetailsVisible && municipalDetailsVisible && modelDetailsVisible && dialogFits)
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth), false)
  await page.close()
}

const recovery = await browser.newPage()
await recovery.route(/\.csv(?:\?.*)?$/, route => route.fulfill({ status: 503, body: '' }))
await recovery.goto(process.env.PREVIEW_URL ?? 'http://127.0.0.1:5173/', { waitUntil: 'domcontentloaded' })
await recovery.getByRole('alert').waitFor()
assert.match(await recovery.getByRole('alert').textContent(), /carregar a base/)
await recovery.unroute(/\.csv(?:\?.*)?$/)
await recovery.getByRole('button', { name: 'Tentar novamente' }).click()
await recovery.getByText('Comparação entre métodos', { exact: true }).waitFor()
await recovery.close()
await browser.close()
console.log(JSON.stringify(results, null, 2))
