import { chromium } from 'playwright-core'
import path from 'node:path'

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

  await page.goto('http://127.0.0.1:5173/', { waitUntil: 'networkidle' })
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
  const tableScrollAvailable = await page.locator('table').evaluate((table) => {
    const container = table.parentElement
    return Boolean(container && container.scrollWidth > container.clientWidth)
  })
  await page.getByRole('button', { name: /Ver detalhes de/ }).first().click()
  const temporalDetailsVisible = await page.getByText('Comparação temporal', { exact: true }).isVisible()
  const municipalDetailsVisible = await page.getByText('Comparação municipal', { exact: true }).isVisible()
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
    interactions: { ...(interactions ?? {}), tableScrollAvailable, temporalDetailsVisible, municipalDetailsVisible, dialogFits },
    chartGeometry: await page.evaluate(() => ({
      bars: [...document.querySelectorAll('.recharts-bar-rectangle path')].map((element) => Math.round(element.getBoundingClientRect().width)),
      lines: [...document.querySelectorAll('.recharts-line-curve')].map((element) => Math.round(element.getBoundingClientRect().width)),
    })),
    errors,
  })
  await page.close()
}

await browser.close()
console.log(JSON.stringify(results, null, 2))
