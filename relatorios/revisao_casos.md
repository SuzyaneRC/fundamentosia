# Conferência dos casos e diagnóstico dos alertas

Revisão documental dos indicadores da base consolidada com modelos separados por produto e avaliação temporal em 30 janelas. Foram comparados preço atual, coleta anterior, mediana municipal, previsão e limite da janela do Random Forest. A conferência avalia coerência estatística; não consulta documentos comerciais nem confirma irregularidades.

| CNPJ | Produto / coleta | Evidências | Interpretação |
|---|---|---|---|
| 32864795001063 | Gasolina aditivada, 20/03/2026 | R$ 7,89 contra R$ 7,09 antes; mediana municipal R$ 7,14 (+10,50%); previsão RF R$ 7,007 e limite R$ 0,1363; quatro métodos sinalizam | Há aumento temporal e distância municipal simultâneos. Priorizar conferência da coleta e comparação com postos semelhantes. |
| 32864795001063 | Gasolina, 20/03/2026 | R$ 7,69 contra R$ 6,89 antes; mediana municipal R$ 7,14 (+7,70%); previsão RF R$ 6,69; quatro métodos sinalizam | Aumento de R$ 0,80 e nível acima dos outros postos sustentam a seleção para revisão. O limite RF desta janela é baixo (R$ 0,0116), refletindo calibração com preços estáveis. |
| 04979182000145 | Gasolina, 12/05/2026 | R$ 7,52 contra R$ 7,22 antes; mediana municipal R$ 7,52; previsão RF R$ 6,69, erro R$ 0,83 e limite R$ 0,60; quatro métodos sinalizam | O preço coincide com a mediana municipal. Mesmo o consenso não prova comportamento exclusivo do posto; há dificuldade dos modelos históricos em acompanhar o nível de mercado. |
| 13008610000183 | Diesel S10, 09/04/2026 | R$ 7,30 contra R$ 6,28 antes (+16,24%); mediana municipal R$ 7,30; previsão RF R$ 6,3878, erro R$ 0,9122 e limite R$ 0,7493; quatro métodos sinalizam | Forte mudança temporal com preço municipal compatível. Investigar mudança geral de mercado e o intervalo entre coletas. |

## Diagnóstico por produto e mês

O Random Forest sinalizou 491 de 1.718 registros de teste (28,58%). Os testes não impõem uma taxa fixa de 5%: cada limite é o percentil 95 dos erros da calibração anterior. Uma mudança na distribuição dos preços pode elevar a taxa nas janelas seguintes.

- Gasolina: 181 de 584 registros sinalizados. Em abril/2026, 44 de 63 (69,84%), com MAE de R$ 0,561; em maio, 35 de 64 (54,69%), com MAE de R$ 0,680. Os erros concentram-se em períodos de níveis de preço diferentes do histórico de treino.
- Etanol: em abril/2026, 34 de 39 registros sinalizados (87,18%), com MAE de R$ 0,551; em maio, 10 de 40 (25%), com MAE de R$ 0,676. A taxa isolada não determina o tamanho do erro: os limites de calibração mudam entre janelas.
- Diesel S10: abril/2026 tem MAE de R$ 0,738, com somente dez registros avaliados. A amostra pequena exige cautela na interpretação.
- GNV: 61 de 139 registros sinalizados (43,88%). A calibração pode ter dispersão quase nula; pequenas mudanças reais passam a superar limites muito baixos. Não se deve interpretar a taxa como percentual de irregularidades.
- DIESEL: sem população apta suficiente para IA por produto. O painel mostra explicitamente zero avaliados, em vez de considerar os registros normais.

A avaliação em janelas amplia a cobertura para 1.718 previsões de teste distintas, sem repetir testes ou usar preços futuros no treino. Isso não elimina a dificuldade do Random Forest em extrapolar novos níveis de preço. As métricas da avaliação antiga e da atual usam populações diferentes, portanto não permitem afirmar melhora de precisão apenas pela mudança do MAE.

Isolation Forest e K-Means têm Jaccard de 45,94%, enquanto a concordância total é 96,24%. A concordância total é influenciada pela maioria de registros não sinalizados; os métodos ainda divergem sobre parte importante dos alertas.

## Sensibilidade dos alertas aos parâmetros

Interpretação de `relatorios/sensibilidade.md`, com 34 configurações.

- Random Forest: a taxa elevada não decorre do número de árvores nem só do percentil. Com 100, 200 ou 400 árvores no percentil 95, ficou entre 27,53% e 28,58%; mesmo no percentil 99, ficou entre 19,32% e 19,67%, muito acima do 1% que uma distribuição estável sugeriria. Março a maio de 2026 concentram 326 dos 491 alertas (66,40%) em 554 dos 1.718 registros de teste; nos demais meses, a taxa é de 14,18%. O padrão é compatível com a mudança de nível de preços já descrita acima, mas não a demonstra como causa.
- Baseline: é o método mais sensível ao limite. Passar de 2 para 2,5 desvios reduz os alertas de 201 para 35; 3 desvios e 3,5 MAD deixam 9. Com 2 desvios, o limite MAD não altera os alertas. A escolha de 2 desvios define, portanto, boa parte do resultado.
- Isolation Forest e K-Means: a taxa acompanha o parâmetro por construção. Com K-Means no percentil 95, mudar K de 3 para 5 mantém 67,23% dos alertas da referência e chega a Jaccard de 50,97%: a contagem quase não muda, mas os registros mudam.
- Proximidade do mercado: 55,60% dos alertas do Random Forest e 52,04% dos do baseline têm preço a até 1% da mediana dos outros postos no mesmo dia. Esses casos dizem menos sobre um posto específico. O limite de 1% é descritivo.
- Alertas estáveis: 1.270 registros são sinalizados em alguma configuração, mas só 30 são estáveis em dois ou mais métodos, 11 em três ou mais e 1 nos quatro (32864795001063, gasolina aditivada, 20/03/2026, R$ 7,89, +10,50% sobre a mediana). Essa lista é um ponto de partida mais robusto para a conferência do que uma única configuração.

A grade mede estabilidade, não acerto: sem rótulos confirmados, não indica quais parâmetros são melhores, e por isso a referência foi mantida.

## Uso das revisões no painel

O grupo pode registrar situação e observações em cada coleta e exportá-las em CSV. A revisão fica no navegador e não altera as previsões. Os resultados associados à revisão são identificados; uma revisão fica desatualizada quando seus preços ou resultados mudam. Essa coleta inicial de avaliações humanas poderá apoiar uma validação futura, mas ainda não constitui uma base compartilhada de rótulos confirmados.

Se a base ou os parâmetros mudarem, esta análise deve ser refeita. `resultados.md` e `comparacao.json` são regenerados pelo pipeline; esta revisão permanece separada.
