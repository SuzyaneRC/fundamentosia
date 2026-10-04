# Resultados e comparação dos métodos

Relatório reproduzível gerado por `python comparar_metodos.py`.

| Método | Avaliados | Sinalizados | Taxa |
|---|---:|---:|---:|
| Baseline | 4801 | 201 | 4.19% |
| Isolation Forest | 4604 | 232 | 5.04% |
| K-Means | 4604 | 235 | 5.10% |
| Random Forest | 1718 | 491 | 28.58% |

## Concordância na interseção dos registros avaliados

| Par | Em comum | Ambos sinalizam | Concordância total | Jaccard das sinalizações |
|---|---:|---:|---:|---:|
| Baseline × Isolation Forest | 4604 | 71 | 93.92% | 20.23% |
| Baseline × K-Means | 4604 | 36 | 92.33% | 9.25% |
| Baseline × Random Forest | 1718 | 68 | 73.22% | 12.88% |
| Isolation Forest × K-Means | 4604 | 147 | 96.24% | 45.94% |
| Isolation Forest × Random Forest | 1718 | 113 | 76.14% | 21.61% |
| K-Means × Random Forest | 1718 | 78 | 73.69% | 14.72% |

## Random Forest: avaliação temporal

30 janelas por produto; 1718 previsões de teste distintas. Primeiro teste desde 2025-06-24.
MAE: R$ 0.2044; RMSE: R$ 0.3258; R²: 0.8743.
Cada janela calibra seu próprio limite no percentil 95 dos erros anteriores ao teste. Não há previsão de treino na pontuação.

## Casos para conferência

Amostra por consenso e distância municipal. A sinalização não comprova irregularidade.

| CNPJ | Produto | Data | Preço | Mediana dos outros postos | Diferença % | Métodos sinalizando / avaliados |
|---|---|---|---:|---:|---:|---:|
| 32864795001063 | GASOLINA ADITIVADA | 20/03/2026 | 7.89 | 7.14 | 10.50 | 4 / 4 |
| 32864795001063 | GASOLINA | 20/03/2026 | 7.69 | 7.14 | 7.70 | 4 / 4 |
| 13113477000478 | GASOLINA | 20/03/2026 | 7.68 | 7.14 | 7.56 | 4 / 4 |
| 04979182000145 | GASOLINA | 20/03/2026 | 7.62 | 7.14 | 6.72 | 4 / 4 |
| 04979182000145 | GASOLINA ADITIVADA | 20/03/2026 | 7.62 | 7.14 | 6.72 | 4 / 4 |
| 15591357000169 | GASOLINA | 20/03/2026 | 7.62 | 7.14 | 6.72 | 4 / 4 |
| 15083140000148 | GASOLINA ADITIVADA | 04/05/2026 | 7.73 | 7.29 | 6.04 | 4 / 4 |
| 13007828001004 | GASOLINA ADITIVADA | 12/05/2026 | 7.93 | 7.54 | 5.10 | 4 / 4 |
| 15083140000148 | GASOLINA | 04/05/2026 | 7.55 | 7.22 | 4.57 | 4 / 4 |
| 11433769000110 | GASOLINA ADITIVADA | 07/05/2026 | 7.88 | 7.59 | 3.82 | 4 / 4 |

## Parâmetros e limitações

- Baseline: regressão linear por produto, tempo em dias; resíduos acima de 2 desvios padrão ou 3,5 MAD normalizado. Limites por produto; séries com menos de 3 registros excluídas.
- Isolation Forest: 100 árvores, seed 42, contaminação inicial 5%; testes de 1%, 3%, 5% e 10%.
- K-Means: 3 grupos, n_init=10, seed 42; distância ao centroide, limite no percentil 95.
- IA não supervisionada: modelos e StandardScaler independentes por produto, sobre preço, variação percentual, diferença histórica e diferença municipal percentual. Ajuste descritivo na base inteira; não mede generalização futura. Grupos com menos de 10 registros aptos ficam fora; K-Means também exige 3 vetores distintos.
- Random Forest: 200 árvores, seed 42; treino inicial com 40% das datas distintas, calibração e testes em blocos de aproximadamente 10%. Treino crescente e testes sem sobreposição, por produto. Exige 20 registros de treino, 5 de calibração e 10 datas distintas. Somente teste recebe pontuação. O total final da série foi removido das entradas para evitar informação futura.
- A mediana municipal usa outros postos no mesmo dia: é uma referência contemporânea, que exige coletas daquele dia; não é previsão antecipada.
- Baseline é descritivo e ajustado na base analisada. Não deve ser interpretado como previsão fora do treino.
- Pontuações têm escalas diferentes. Compare sinalizações e rankings, não os valores brutos entre métodos.
- Concordância total pode ser alta pela predominância de registros não sinalizados; Jaccard compara apenas a união das sinalizações.
- Não há rótulos de anomalias confirmadas: concordância e coerência não substituem precisão/recall nem validação humana.
- Próximos testes: K=2/3/4/5, percentis 90/95/99, RF 100/200/400 árvores e limites baseline 2/2,5/3 desvios e 3/3,5/4 MAD. Comparar por produto e em janelas temporais.

## Diagnóstico por produto e mês — Random Forest

| Produto | Mês | Avaliados | Sinalizados | Taxa | MAE |
|---|---|---:|---:|---:|---:|
| DIESEL S10 | 2025-06 | 8 | 0 | 0.00% | 0.0761 |
| DIESEL S10 | 2025-07 | 16 | 0 | 0.00% | 0.0751 |
| DIESEL S10 | 2025-08 | 13 | 0 | 0.00% | 0.0736 |
| DIESEL S10 | 2025-09 | 18 | 7 | 38.89% | 0.0224 |
| DIESEL S10 | 2025-10 | 14 | 6 | 42.86% | 0.0165 |
| DIESEL S10 | 2025-11 | 11 | 1 | 9.09% | 0.0109 |
| DIESEL S10 | 2025-12 | 14 | 2 | 14.29% | 0.0438 |
| DIESEL S10 | 2026-01 | 12 | 1 | 8.33% | 0.0113 |
| DIESEL S10 | 2026-02 | 7 | 3 | 42.86% | 0.0190 |
| DIESEL S10 | 2026-03 | 16 | 10 | 62.50% | 0.4107 |
| DIESEL S10 | 2026-04 | 10 | 3 | 30.00% | 0.7384 |
| DIESEL S10 | 2026-05 | 10 | 1 | 10.00% | 0.5134 |
| DIESEL S10 | 2026-06 | 14 | 0 | 0.00% | 0.3436 |
| ETANOL | 2025-09 | 49 | 0 | 0.00% | 0.0123 |
| ETANOL | 2025-10 | 38 | 5 | 13.16% | 0.0228 |
| ETANOL | 2025-11 | 35 | 6 | 17.14% | 0.0292 |
| ETANOL | 2025-12 | 19 | 0 | 0.00% | 0.0115 |
| ETANOL | 2026-01 | 17 | 0 | 0.00% | 0.0272 |
| ETANOL | 2026-02 | 22 | 4 | 18.18% | 0.0699 |
| ETANOL | 2026-03 | 43 | 7 | 16.28% | 0.1100 |
| ETANOL | 2026-04 | 39 | 34 | 87.18% | 0.5513 |
| ETANOL | 2026-05 | 40 | 10 | 25.00% | 0.6763 |
| ETANOL | 2026-06 | 47 | 8 | 17.02% | 0.4088 |
| GASOLINA | 2025-09 | 68 | 9 | 13.24% | 0.0072 |
| GASOLINA | 2025-10 | 67 | 17 | 25.37% | 0.0162 |
| GASOLINA | 2025-11 | 68 | 11 | 16.18% | 0.0323 |
| GASOLINA | 2025-12 | 40 | 0 | 0.00% | 0.0316 |
| GASOLINA | 2026-01 | 31 | 3 | 9.68% | 0.0108 |
| GASOLINA | 2026-02 | 33 | 3 | 9.09% | 0.0082 |
| GASOLINA | 2026-03 | 71 | 58 | 81.69% | 0.3696 |
| GASOLINA | 2026-04 | 63 | 44 | 69.84% | 0.5610 |
| GASOLINA | 2026-05 | 64 | 35 | 54.69% | 0.6800 |
| GASOLINA | 2026-06 | 79 | 1 | 1.27% | 0.4820 |
| GASOLINA ADITIVADA | 2025-09 | 56 | 4 | 7.14% | 0.0262 |
| GASOLINA ADITIVADA | 2025-10 | 55 | 11 | 20.00% | 0.0527 |
| GASOLINA ADITIVADA | 2025-11 | 56 | 6 | 10.71% | 0.0612 |
| GASOLINA ADITIVADA | 2025-12 | 35 | 5 | 14.29% | 0.0634 |
| GASOLINA ADITIVADA | 2026-01 | 27 | 1 | 3.70% | 0.0309 |
| GASOLINA ADITIVADA | 2026-02 | 22 | 7 | 31.82% | 0.0599 |
| GASOLINA ADITIVADA | 2026-03 | 55 | 44 | 80.00% | 0.2935 |
| GASOLINA ADITIVADA | 2026-04 | 52 | 39 | 75.00% | 0.3598 |
| GASOLINA ADITIVADA | 2026-05 | 55 | 20 | 36.36% | 0.4980 |
| GASOLINA ADITIVADA | 2026-06 | 70 | 4 | 5.71% | 0.1888 |
| GNV | 2025-06 | 6 | 0 | 0.00% | 0.0392 |
| GNV | 2025-07 | 12 | 2 | 16.67% | 0.0643 |
| GNV | 2025-08 | 9 | 9 | 100.00% | 0.1723 |
| GNV | 2025-09 | 15 | 0 | 0.00% | 0.1184 |
| GNV | 2025-10 | 11 | 0 | 0.00% | 0.1202 |
| GNV | 2025-11 | 12 | 12 | 100.00% | 0.0006 |
| GNV | 2025-12 | 9 | 9 | 100.00% | 0.0006 |
| GNV | 2026-01 | 4 | 2 | 50.00% | 0.0003 |
| GNV | 2026-02 | 6 | 6 | 100.00% | 0.0800 |
| GNV | 2026-03 | 8 | 8 | 100.00% | 0.0800 |
| GNV | 2026-04 | 12 | 12 | 100.00% | 0.0800 |
| GNV | 2026-05 | 16 | 1 | 6.25% | 0.0475 |
| GNV | 2026-06 | 19 | 0 | 0.00% | 0.0348 |

## Auditoria das janelas temporais

| Produto | Janela | Fim treino | Calibração | Teste | N treino / cal / teste | Limite |
|---|---:|---|---|---|---|---:|
| DIESEL S10 | 1 | 2025-04-08 | 2025-04-15 a 2025-06-16 | 2025-06-24 a 2025-08-27 | 193 / 37 / 37 | 0.3242 |
| DIESEL S10 | 2 | 2025-06-16 | 2025-06-24 a 2025-08-27 | 2025-09-02 a 2025-11-04 | 230 / 37 / 35 | 0.0134 |
| DIESEL S10 | 3 | 2025-08-27 | 2025-09-02 a 2025-11-04 | 2025-11-11 a 2025-12-29 | 267 / 35 / 22 | 0.0509 |
| DIESEL S10 | 4 | 2025-11-04 | 2025-11-11 a 2025-12-29 | 2026-01-05 a 2026-03-20 | 302 / 22 / 31 | 0.0353 |
| DIESEL S10 | 5 | 2025-12-29 | 2026-01-05 a 2026-03-20 | 2026-03-25 a 2026-05-26 | 324 / 31 / 24 | 0.7493 |
| DIESEL S10 | 6 | 2026-03-20 | 2026-03-25 a 2026-05-26 | 2026-06-03 a 2026-06-30 | 355 / 24 / 14 | 0.9010 |
| ETANOL | 1 | 2025-06-03 | 2025-06-09 a 2025-08-27 | 2025-09-02 a 2025-11-04 | 610 / 128 / 92 | 0.0492 |
| ETANOL | 2 | 2025-08-27 | 2025-09-02 a 2025-11-04 | 2025-11-05 a 2025-12-29 | 738 / 92 / 49 | 0.0821 |
| ETANOL | 3 | 2025-11-04 | 2025-11-05 a 2025-12-29 | 2026-01-06 a 2026-03-09 | 830 / 49 / 57 | 0.1526 |
| ETANOL | 4 | 2025-12-29 | 2026-01-06 a 2026-03-09 | 2026-03-20 a 2026-04-29 | 879 / 57 / 64 | 0.1703 |
| ETANOL | 5 | 2026-03-09 | 2026-03-20 a 2026-04-29 | 2026-05-04 a 2026-06-16 | 936 / 64 / 69 | 0.7611 |
| ETANOL | 6 | 2026-04-29 | 2026-05-04 a 2026-06-16 | 2026-06-23 a 2026-06-30 | 1000 / 69 / 18 | 0.0912 |
| GASOLINA | 1 | 2025-06-09 | 2025-06-16 a 2025-09-02 | 2025-09-09 a 2025-11-05 | 804 / 200 / 152 | 0.0168 |
| GASOLINA | 2 | 2025-09-02 | 2025-09-09 a 2025-11-05 | 2025-11-11 a 2025-12-30 | 1004 / 152 / 91 | 0.0659 |
| GASOLINA | 3 | 2025-11-05 | 2025-11-11 a 2025-12-30 | 2026-01-05 a 2026-02-24 | 1156 / 91 / 64 | 0.0318 |
| GASOLINA | 4 | 2025-12-30 | 2026-01-05 a 2026-02-24 | 2026-03-04 a 2026-04-23 | 1247 / 64 / 104 | 0.0116 |
| GASOLINA | 5 | 2026-02-24 | 2026-03-04 a 2026-04-23 | 2026-04-24 a 2026-06-03 | 1311 / 104 / 111 | 0.6000 |
| GASOLINA | 6 | 2026-04-23 | 2026-04-24 a 2026-06-03 | 2026-06-08 a 2026-06-30 | 1415 / 111 / 62 | 0.6292 |
| GASOLINA ADITIVADA | 1 | 2025-06-09 | 2025-06-16 a 2025-09-02 | 2025-09-09 a 2025-11-05 | 627 / 153 / 125 | 0.1123 |
| GASOLINA ADITIVADA | 2 | 2025-09-02 | 2025-09-09 a 2025-11-05 | 2025-11-11 a 2025-12-30 | 780 / 125 / 77 | 0.1156 |
| GASOLINA ADITIVADA | 3 | 2025-11-05 | 2025-11-11 a 2025-12-30 | 2026-01-05 a 2026-03-04 | 905 / 77 / 59 | 0.0605 |
| GASOLINA ADITIVADA | 4 | 2025-12-30 | 2026-01-05 a 2026-03-04 | 2026-03-09 a 2026-04-24 | 982 / 59 / 83 | 0.1363 |
| GASOLINA ADITIVADA | 5 | 2026-03-04 | 2026-03-09 a 2026-04-24 | 2026-04-27 a 2026-06-08 | 1041 / 83 / 89 | 0.5757 |
| GASOLINA ADITIVADA | 6 | 2026-04-24 | 2026-04-27 a 2026-06-08 | 2026-06-09 a 2026-06-30 | 1124 / 89 / 50 | 0.3190 |
| GNV | 1 | 2025-04-15 | 2025-04-22 a 2025-06-16 | 2025-06-24 a 2025-08-19 | 108 / 26 / 27 | 0.1051 |
| GNV | 2 | 2025-06-16 | 2025-06-24 a 2025-08-19 | 2025-09-02 a 2025-10-28 | 134 / 27 / 26 | 0.2932 |
| GNV | 3 | 2025-08-19 | 2025-09-02 a 2025-10-28 | 2025-11-04 a 2026-01-05 | 161 / 26 / 23 | 0.0006 |
| GNV | 4 | 2025-10-28 | 2025-11-04 a 2026-01-05 | 2026-01-20 a 2026-04-24 | 187 / 23 / 24 | 0.0000 |
| GNV | 5 | 2026-01-05 | 2026-01-20 a 2026-04-24 | 2026-04-29 a 2026-06-09 | 210 / 24 / 28 | 0.0800 |
| GNV | 6 | 2026-04-24 | 2026-04-29 a 2026-06-09 | 2026-06-16 a 2026-06-30 | 234 / 28 / 11 | 0.0532 |
