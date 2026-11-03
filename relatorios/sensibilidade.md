# Análise de sensibilidade dos parâmetros

Relatório reproduzível gerado por `python analise_sensibilidade.py`. A base consolidada e o painel continuam usando os parâmetros de referência.

Mantidos: parcela dos alertas da referência também sinalizada na configuração. Jaccard e mantidos usam a interseção dos registros avaliados.

| Método | Configuração | Avaliados | Sinalizados | Taxa | Jaccard com a referência | Mantidos | MAE (R$) |
|---|---|---:|---:|---:|---:|---:|---:|
| Baseline | desvios=2, MAD=3 | 4801 | 201 | 4.19% | 100.00% | 100.00% | — |
| Baseline | desvios=2, MAD=3.5 (referência) | 4801 | 201 | 4.19% | 100.00% | 100.00% | — |
| Baseline | desvios=2, MAD=4 | 4801 | 201 | 4.19% | 100.00% | 100.00% | — |
| Baseline | desvios=2.5, MAD=3 | 4801 | 35 | 0.73% | 17.41% | 17.41% | — |
| Baseline | desvios=2.5, MAD=3.5 | 4801 | 35 | 0.73% | 17.41% | 17.41% | — |
| Baseline | desvios=2.5, MAD=4 | 4801 | 35 | 0.73% | 17.41% | 17.41% | — |
| Baseline | desvios=3, MAD=3 | 4801 | 28 | 0.58% | 13.93% | 13.93% | — |
| Baseline | desvios=3, MAD=3.5 | 4801 | 9 | 0.19% | 4.48% | 4.48% | — |
| Baseline | desvios=3, MAD=4 | 4801 | 9 | 0.19% | 4.48% | 4.48% | — |
| Isolation Forest | contaminação=0.01 | 4604 | 47 | 1.02% | 20.26% | 20.26% | — |
| Isolation Forest | contaminação=0.03 | 4604 | 134 | 2.91% | 57.76% | 57.76% | — |
| Isolation Forest | contaminação=0.05 (referência) | 4604 | 232 | 5.04% | 100.00% | 100.00% | — |
| Isolation Forest | contaminação=0.1 | 4604 | 462 | 10.03% | 50.22% | 100.00% | — |
| K-Means | K=2, percentil=0.9 | 4604 | 474 | 10.30% | 48.64% | 98.72% | — |
| K-Means | K=2, percentil=0.95 | 4604 | 233 | 5.06% | 70.80% | 82.55% | — |
| K-Means | K=2, percentil=0.99 | 4604 | 52 | 1.13% | 17.14% | 17.87% | — |
| K-Means | K=3, percentil=0.9 | 4604 | 464 | 10.08% | 50.65% | 100.00% | — |
| K-Means | K=3, percentil=0.95 (referência) | 4604 | 235 | 5.10% | 100.00% | 100.00% | — |
| K-Means | K=3, percentil=0.99 | 4604 | 51 | 1.11% | 21.70% | 21.70% | — |
| K-Means | K=4, percentil=0.9 | 4604 | 464 | 10.08% | 41.21% | 86.81% | — |
| K-Means | K=4, percentil=0.95 | 4604 | 233 | 5.06% | 61.94% | 76.17% | — |
| K-Means | K=4, percentil=0.99 | 4604 | 48 | 1.04% | 20.43% | 20.43% | — |
| K-Means | K=5, percentil=0.9 | 4604 | 467 | 10.14% | 41.53% | 87.66% | — |
| K-Means | K=5, percentil=0.95 | 4604 | 233 | 5.06% | 50.97% | 67.23% | — |
| K-Means | K=5, percentil=0.99 | 4604 | 49 | 1.06% | 19.33% | 19.57% | — |
| Random Forest | árvores=100, percentil=0.9 | 1718 | 626 | 36.44% | 72.11% | 95.32% | 0.2044 |
| Random Forest | árvores=100, percentil=0.95 | 1718 | 473 | 27.53% | 93.57% | 94.91% | 0.2044 |
| Random Forest | árvores=100, percentil=0.99 | 1718 | 332 | 19.32% | 67.62% | 67.62% | 0.2044 |
| Random Forest | árvores=200, percentil=0.9 | 1718 | 663 | 38.59% | 74.06% | 100.00% | 0.2044 |
| Random Forest | árvores=200, percentil=0.95 (referência) | 1718 | 491 | 28.58% | 100.00% | 100.00% | 0.2044 |
| Random Forest | árvores=200, percentil=0.99 | 1718 | 338 | 19.67% | 68.84% | 68.84% | 0.2044 |
| Random Forest | árvores=400, percentil=0.9 | 1718 | 659 | 38.36% | 74.24% | 99.80% | 0.2041 |
| Random Forest | árvores=400, percentil=0.95 | 1718 | 491 | 28.58% | 99.19% | 99.59% | 0.2041 |
| Random Forest | árvores=400, percentil=0.99 | 1718 | 336 | 19.56% | 68.43% | 68.43% | 0.2041 |

## Alertas próximos à mediana dos outros postos

Alertas da referência com preço a até 1% da mediana do mesmo dia. Sugerem acompanhamento do mercado local, sem excluir a necessidade de conferência; alertas sem mediana disponível ficam fora da conta.

| Método | Alertas com mediana | Próximos da mediana | Parcela |
|---|---:|---:|---:|
| Baseline | 196 | 102 | 52.04% |
| Isolation Forest | 232 | 95 | 40.95% |
| K-Means | 235 | 81 | 34.47% |
| Random Forest | 491 | 273 | 55.60% |

## Alertas estáveis

Um alerta é estável em um método quando é sinalizado em todas as configurações que avaliaram o registro. A lista por registro está em `relatorios/estabilidade_alertas.csv`.

| Métodos em que o alerta é estável | Registros |
|---:|---:|
| 4 | 1 |
| 3 | 10 |
| 2 | 19 |
| 1 | 304 |
| 0 | 936 |

## Taxa por produto

| Método | Produto | Referência | Faixa entre configurações |
|---|---|---:|---|
| Baseline | DIESEL | 0.00% | 0.00% a 0.00% |
| Baseline | DIESEL S10 | 3.07% | 0.00% a 3.07% |
| Baseline | ETANOL | 2.58% | 0.00% a 2.58% |
| Baseline | GASOLINA | 5.65% | 0.25% a 5.65% |
| Baseline | GASOLINA ADITIVADA | 5.15% | 0.38% a 5.15% |
| Baseline | GNV | 0.00% | 0.00% a 0.00% |
| Isolation Forest | DIESEL S10 | 5.09% | 1.02% a 10.18% |
| Isolation Forest | ETANOL | 5.06% | 1.01% a 10.03% |
| Isolation Forest | GASOLINA | 5.04% | 1.01% a 10.01% |
| Isolation Forest | GASOLINA ADITIVADA | 5.07% | 1.03% a 10.06% |
| Isolation Forest | GNV | 4.76% | 1.10% a 9.89% |
| K-Means | DIESEL S10 | 5.09% | 1.02% a 11.96% |
| K-Means | ETANOL | 5.06% | 1.01% a 10.21% |
| K-Means | GASOLINA | 5.10% | 1.01% a 10.14% |
| K-Means | GASOLINA ADITIVADA | 5.15% | 1.03% a 10.21% |
| K-Means | GNV | 5.13% | 1.10% a 10.99% |
| Random Forest | DIESEL S10 | 20.86% | 9.82% a 26.99% |
| Random Forest | ETANOL | 21.20% | 14.90% a 44.70% |
| Random Forest | GASOLINA | 30.99% | 20.38% a 35.62% |
| Random Forest | GASOLINA ADITIVADA | 29.19% | 18.22% a 42.03% |
| Random Forest | GNV | 43.88% | 27.34% a 45.32% |

## Taxa por mês

| Método | Mês | Referência | Faixa entre configurações |
|---|---|---:|---|
| Baseline | 2024-07 | 0.00% | 0.00% a 0.00% |
| Baseline | 2024-08 | 0.00% | 0.00% a 0.00% |
| Baseline | 2024-09 | 0.00% | 0.00% a 0.00% |
| Baseline | 2024-10 | 12.33% | 0.00% a 12.33% |
| Baseline | 2024-11 | 19.02% | 0.00% a 19.02% |
| Baseline | 2024-12 | 8.27% | 0.00% a 8.27% |
| Baseline | 2025-01 | 1.52% | 0.00% a 1.52% |
| Baseline | 2025-02 | 0.00% | 0.00% a 0.00% |
| Baseline | 2025-03 | 0.00% | 0.00% a 0.00% |
| Baseline | 2025-04 | 0.00% | 0.00% a 0.00% |
| Baseline | 2025-05 | 0.00% | 0.00% a 0.00% |
| Baseline | 2025-06 | 0.00% | 0.00% a 0.00% |
| Baseline | 2025-07 | 0.00% | 0.00% a 0.00% |
| Baseline | 2025-08 | 0.00% | 0.00% a 0.00% |
| Baseline | 2025-09 | 0.00% | 0.00% a 0.00% |
| Baseline | 2025-10 | 0.00% | 0.00% a 0.00% |
| Baseline | 2025-11 | 0.00% | 0.00% a 0.00% |
| Baseline | 2025-12 | 1.59% | 0.00% a 1.59% |
| Baseline | 2026-01 | 9.09% | 0.00% a 9.09% |
| Baseline | 2026-02 | 19.00% | 0.00% a 19.00% |
| Baseline | 2026-03 | 8.74% | 2.43% a 8.74% |
| Baseline | 2026-04 | 6.81% | 0.00% a 6.81% |
| Baseline | 2026-05 | 25.25% | 2.02% a 25.25% |
| Baseline | 2026-06 | 0.00% | 0.00% a 0.00% |
| Isolation Forest | 2024-07 | 0.00% | 0.00% a 1.25% |
| Isolation Forest | 2024-08 | 0.93% | 0.00% a 1.85% |
| Isolation Forest | 2024-09 | 0.74% | 0.37% a 6.69% |
| Isolation Forest | 2024-10 | 15.46% | 5.80% a 32.85% |
| Isolation Forest | 2024-11 | 12.63% | 0.00% a 33.68% |
| Isolation Forest | 2024-12 | 3.94% | 0.39% a 7.87% |
| Isolation Forest | 2025-01 | 3.57% | 0.00% a 6.63% |
| Isolation Forest | 2025-02 | 2.55% | 0.51% a 6.63% |
| Isolation Forest | 2025-03 | 0.00% | 0.00% a 0.00% |
| Isolation Forest | 2025-04 | 1.55% | 0.00% a 2.59% |
| Isolation Forest | 2025-05 | 1.06% | 0.00% a 2.12% |
| Isolation Forest | 2025-06 | 0.00% | 0.00% a 0.00% |
| Isolation Forest | 2025-07 | 0.00% | 0.00% a 0.00% |
| Isolation Forest | 2025-08 | 1.65% | 0.00% a 1.65% |
| Isolation Forest | 2025-09 | 0.00% | 0.00% a 0.00% |
| Isolation Forest | 2025-10 | 0.00% | 0.00% a 0.00% |
| Isolation Forest | 2025-11 | 0.00% | 0.00% a 0.00% |
| Isolation Forest | 2025-12 | 0.85% | 0.00% a 0.85% |
| Isolation Forest | 2026-01 | 0.00% | 0.00% a 0.00% |
| Isolation Forest | 2026-02 | 6.67% | 0.00% a 7.78% |
| Isolation Forest | 2026-03 | 19.17% | 6.22% a 38.34% |
| Isolation Forest | 2026-04 | 10.23% | 5.11% a 16.48% |
| Isolation Forest | 2026-05 | 37.30% | 5.95% a 59.46% |
| Isolation Forest | 2026-06 | 4.80% | 0.00% a 11.79% |
| K-Means | 2024-07 | 2.50% | 0.62% a 15.62% |
| K-Means | 2024-08 | 0.46% | 0.00% a 3.24% |
| K-Means | 2024-09 | 3.72% | 0.00% a 18.96% |
| K-Means | 2024-10 | 20.77% | 0.00% a 39.13% |
| K-Means | 2024-11 | 16.84% | 1.58% a 37.37% |
| K-Means | 2024-12 | 3.15% | 0.39% a 7.87% |
| K-Means | 2025-01 | 3.57% | 0.51% a 8.67% |
| K-Means | 2025-02 | 5.10% | 0.00% a 15.31% |
| K-Means | 2025-03 | 0.00% | 0.00% a 0.41% |
| K-Means | 2025-04 | 0.52% | 0.00% a 5.70% |
| K-Means | 2025-05 | 1.06% | 0.00% a 4.23% |
| K-Means | 2025-06 | 0.00% | 0.00% a 2.52% |
| K-Means | 2025-07 | 0.00% | 0.00% a 3.80% |
| K-Means | 2025-08 | 1.65% | 0.00% a 1.65% |
| K-Means | 2025-09 | 0.00% | 0.00% a 0.42% |
| K-Means | 2025-10 | 0.00% | 0.00% a 0.54% |
| K-Means | 2025-11 | 0.00% | 0.00% a 2.75% |
| K-Means | 2025-12 | 0.85% | 0.00% a 1.71% |
| K-Means | 2026-01 | 0.00% | 0.00% a 1.10% |
| K-Means | 2026-02 | 3.33% | 2.22% a 10.00% |
| K-Means | 2026-03 | 21.76% | 4.15% a 38.86% |
| K-Means | 2026-04 | 9.09% | 0.00% a 14.77% |
| K-Means | 2026-05 | 25.95% | 1.08% a 45.95% |
| K-Means | 2026-06 | 1.75% | 0.00% a 10.92% |
| Random Forest | 2025-06 | 0.00% | 0.00% a 7.14% |
| Random Forest | 2025-07 | 7.14% | 0.00% a 14.29% |
| Random Forest | 2025-08 | 40.91% | 36.36% a 40.91% |
| Random Forest | 2025-09 | 9.71% | 6.31% a 22.82% |
| Random Forest | 2025-10 | 21.08% | 16.22% a 37.84% |
| Random Forest | 2025-11 | 19.78% | 11.54% a 38.46% |
| Random Forest | 2025-12 | 13.68% | 0.85% a 30.77% |
| Random Forest | 2026-01 | 7.69% | 0.00% a 19.78% |
| Random Forest | 2026-02 | 25.56% | 17.78% a 37.78% |
| Random Forest | 2026-03 | 65.80% | 58.03% a 76.68% |
| Random Forest | 2026-04 | 75.00% | 58.52% a 77.84% |
| Random Forest | 2026-05 | 36.22% | 2.70% a 44.86% |
| Random Forest | 2026-06 | 5.68% | 0.00% a 10.04% |

## Limitações

- Nos métodos não supervisionados, a taxa acompanha o parâmetro por construção; a estabilidade dos registros sinalizados é o indicador mais informativo.
- A grade não escolhe parâmetros melhores: sem rótulos confirmados não é possível calcular precisão e recall.
- Sinalização estável indica robustez à configuração, não irregularidade.
