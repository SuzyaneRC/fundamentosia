# Guia do código

Mapa para entender o projeto. Cada arquivo também explica, no início, o próprio papel; instalação e comandos estão no [README](../README.md).

## Visão geral

```text
planilhas/*.csv (dados da ANP)
   │  criaBaseBruta.py           limpa e recorta Aracaju
   ▼
base_limpa_aracaju.csv
   │  metricasBaseBruta.py       só imprime um resumo
   │  processamento_temporal.py  calcula histórico e mediana municipal
   ▼
dados_aracaju_processados.csv ──► frontend/ (painel)
   │  comparar_metodos.py        acrescenta os 4 métodos à mesma base; gera os relatórios
   │  analise_sensibilidade.py   testa 34 configurações; não altera a base
   ▼
relatorios/
```

`executar_pipeline.py` executa tudo nessa ordem.

## Ordem de leitura sugerida

1. `executar_pipeline.py`: a sequência das etapas.
2. `criaBaseBruta.py`, `validacao_coletas.py` e `processamento_temporal.py`: como os dados são preparados.
3. `baseline_regressao.py`: o método mais simples.
4. `Modelos/algoritmos/`, nesta ordem: `util_dados.py`, `isolation_forest.py`, `kmeans.py`, `modelos_produto.py`, `random_forest.py` e `avaliacao_temporal.py`.
5. `comparar_metodos.py` e `analise_sensibilidade.py`: como os resultados são comparados.
6. `frontend/src/lib/fuel-data.ts`, `App.tsx` e os demais componentes: como o painel usa a base.
7. `tests/test_metodos.py`: exemplos pequenos do comportamento esperado.

## Os quatro métodos

| Método | Pergunta que responde | Quando sinaliza | Avalia dados futuros? |
|---|---|---|---|
| Baseline | O preço está longe da tendência geral do produto? | Resíduo acima de 2 desvios ou 3,5 MAD | Não |
| Isolation Forest | O registro é fácil de separar dos demais? | Entre os 5% mais isoláveis | Não |
| K-Means | O registro está longe de todos os grupos típicos? | Distância no percentil 95 ou acima | Não |
| Random Forest | O preço surpreende quem só conhecia o passado? | Erro maior ou igual ao limite da janela | Sim |

## Termos usados no código

- **Série:** todas as coletas de um posto (CNPJ) para um produto.
- **Registro apto:** tem os dados de que o método precisa e não pertence a uma série curta.
- **Avaliado ou `utilizado_*`:** o método analisou o registro.
- **Sinalizado ou `anomalia_*`:** o método considerou o registro atípico. Indica um caso para conferência, não uma irregularidade.
- **Não avaliado:** é diferente de não sinalizado, e por isso fica fora das taxas.
- **Mediana municipal:** mediana dos outros postos, no mesmo produto e dia.
- **Resíduo:** preço real menos preço estimado.
- **MAD:** desvio absoluto mediano, uma medida de dispersão menos afetada por extremos.
- **Concordância:** parcela de registros com a mesma decisão nos dois métodos.
- **Jaccard:** sinalizados pelos dois divididos pelos sinalizados por pelo menos um.
- **Calibração:** datas não usadas no treino, que definem o limite de erro da janela.
- **Alerta estável:** sinalizado em todas as configurações de um método que avaliaram o registro.

## Painel

| Arquivo | Responsabilidade |
|---|---|
| `src/main.tsx` | Inicia o React |
| `src/App.tsx` | Carregamento, filtros, indicadores, gráficos, tabela e detalhes |
| `src/lib/fuel-data.ts` | Baixa o CSV e converte cada linha em `FuelRecord` |
| `src/lib/review-store.ts` | Tipos e funções das revisões |
| `src/lib/reviews.tsx` | Guarda as revisões em memória e no `localStorage` |
| `src/components/method-comparison.tsx` | Comparação dos métodos no recorte filtrado |
| `src/components/record-review.tsx` | Formulário de revisão |
| `src/components/ui/` | Componentes visuais genéricos (botão, tabela, janela etc.), sem regra do projeto |
| `scripts/visual-check.mjs` | Teste de ponta a ponta no Chrome |

O painel ainda não exibe a análise de sensibilidade; ela está em `relatorios/sensibilidade.md`.

## Como alterar

- **Parâmetro oficial de um método:** altere a constante no arquivo do método e `REFERENCIAS` em `analise_sensibilidade.py`, depois rode o pipeline.
- **Nova coluna no painel:** gere a coluna no Python, depois acrescente-a em `CsvRow`, `FuelRecord` e `parseFuelRecords` em `fuel-data.ts`.
- **Novo período:** coloque o CSV da ANP em `planilhas`, rode o pipeline, atualize `relatorios/revisao_casos.md` (escrito à mão) e ajuste a contagem de 4.816 registros em `tests/test_metodos.py`.
