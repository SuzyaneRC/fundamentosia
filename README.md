# Detecção de anomalias em preços de combustíveis

Análise exploratória dos preços da ANP em Aracaju (SE). Sinalizações indicam casos para conferência, sem comprovar irregularidade.

## Dados e escopo

As fontes em `planilhas` cobrem o segundo semestre de 2024, os dois semestres de 2025 e o primeiro semestre de 2026. O histórico adicional amplia as referências temporais: o recorte final vai de 09/07/2024 a 30/06/2026. São mantidos apenas SE, ARACAJU e combustíveis automotivos (gasolina, gasolina aditivada, etanol, diesel, diesel S10 e GNV). O dicionário original está em `dicionario_colunas.csv`.

A obtenção dos CSVs da ANP é manual. A leitura usa UTF-8, separador `;` e conversão do decimal brasileiro. CNPJ é preservado como texto. Revenda e CNPJ são mantidos em colunas distintas para permitir identificação e agrupamento.

## Preparação do ambiente

Requisitos: Python 3.10+, pandas, numpy, scikit-learn; Node.js 20.19+ ou 22.12+ para o painel.

Clone o projeto e crie um ambiente virtual na raiz do repositório:

```powershell
git clone https://github.com/SuzyaneRC/fundamentosia.git
cd fundamentosia
python -m venv .venv
```

No Windows, os comandos abaixo usam diretamente o Python do ambiente virtual, sem depender da ativação pelo PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install pandas numpy scikit-learn
.\.venv\Scripts\python.exe executar_pipeline.py
```

No Linux ou macOS:

```bash
source .venv/bin/activate
python -m pip install pandas numpy scikit-learn
python executar_pipeline.py
```

## Executar o pipeline

Com o ambiente ativado e as fontes CSV em `planilhas`, execute:

```powershell
python executar_pipeline.py
```

Execute na raiz do repositório. O pipeline limpa os dados, calcula variáveis temporais e executa os quatro métodos. A base consolidada `dados_aracaju_processados.csv` contém os preços, variáveis derivadas, pontuações e sinalizações; é a única base consumida pelo painel. Arquivos intermediários e saídas individuais existentes ficam disponíveis por compatibilidade, sem exigir montagem manual de planilhas por etapa.

Os resumos são guardados em `relatorios/limpeza.txt`, `base.txt` e `temporal.txt`. Resultados, parâmetros, comparação e limitações estão em `relatorios/resultados.md`; os mesmos indicadores estão em `relatorios/comparacao.json`. A conferência de casos está em `relatorios/revisao_casos.md`.

| Etapa | Script | Resultado principal |
|---|---|---|
| Recorte e limpeza | `criaBaseBruta.py` | Seleção dos combustíveis automotivos, padronização, verificação de ausentes e remoção de preços inválidos e duplicados |
| Métricas da base | `metricasBaseBruta.py` | Quantidade de registros e CNPJs, produtos e período |
| Variáveis temporais | `processamento_temporal.py` | Preço anterior, variações, referências históricas e municipais e séries curtas |
| Modelagem e comparação | `comparar_metodos.py` | Base consolidada com os quatro métodos e relatórios de comparação |

Ao executar novamente o pipeline, a base consolidada e os relatórios automáticos são sobrescritos. A revisão dos casos em `relatorios/revisao_casos.md` é preservada e precisa ser atualizada quando a base ou os parâmetros mudarem.

Para recalcular apenas os métodos sobre a base processada:

```powershell
python comparar_metodos.py
```

Scripts individuais também podem ser executados:

```powershell
python baseline_regressao.py
python Modelos/algoritmos/isolation_forest.py
python Modelos/algoritmos/kmeans.py
python Modelos/algoritmos/random_forest.py
```

Após alterações nos scripts individuais, execute `comparar_metodos.py` para atualizar a base consolidada e a comparação do painel.

## Métodos e comparação

- Baseline: regressão linear separada por produto, tempo em dias. Limites e pontuações dos resíduos também são por produto (2 desvios padrão ou 3,5 MAD normalizado).
- Isolation Forest: modelos e `StandardScaler` separados por produto; 100 árvores, contaminação inicial 5%, seed 42. O pipeline também testa 1%, 3% e 10% por combustível.
- K-Means: modelos e `StandardScaler` separados por produto; 3 grupos, pontuação pela distância ao centroide e sinalização acima ou no percentil 95. Distâncias nulas não geram alertas.
- Random Forest: regressor de preço por produto com 200 árvores, avaliado em janelas temporais crescentes. O histórico inicial usa aproximadamente 40% das datas distintas; blocos de aproximadamente 10% são usados para calibração e teste. A cada janela, o treino incorpora somente datas já passadas. O limite é o percentil 95 dos erros da calibração daquela janela; somente previsões de teste são usadas na pontuação. As datas de treino, calibração e teste são separadas dentro de cada janela, e os testes não se sobrepõem.

Séries de posto/produto com menos de 3 registros ficam fora dos quatro métodos. Registros sem as variáveis necessárias também ficam fora do respectivo modelo; não avaliados são diferenciados de não sinalizados. Primeiras coletas normalmente não têm histórico anterior.

Os modelos não supervisionados exigem pelo menos 10 registros aptos por produto; K-Means também exige três vetores distintos. Random Forest exige pelo menos 10 datas distintas, 20 registros de treino e 5 de calibração por janela. O período inicial serve de histórico e fica sem previsão de teste. O produto DIESEL, na base atual, não possui registros aptos suficientes para esses modelos; continua disponível para consulta e para o baseline.

A comparação apresenta contagens, taxas sobre registros avaliados e pares calculados na interseção de suas populações. Concordância total inclui os registros não sinalizados; Jaccard mede a sobreposição das sinalizações. O painel permite limitar todos os métodos à população avaliada pelos quatro. As pontuações brutas não têm a mesma escala e não devem ser comparadas diretamente.

Os métodos não supervisionados e o baseline são descritivos, ajustados na base analisada. A avaliação temporal do Random Forest usa dados posteriores ao treino; a mediana municipal continua sendo uma informação contemporânea de outros postos. Não há rótulos confirmados para calcular precisão e recall. Conferência de coerência estatística não confirma abuso de preço.

## Resultados da execução atual

A base contém **4.816 registros, 32 CNPJs e 6 produtos**, distribuídos em 117 séries de posto/produto. Dez séries têm menos de três observações.

| Método | Registros avaliados | Registros sinalizados | Taxa |
|---|---:|---:|---:|
| Baseline | 4.801 | 201 | 4,19% |
| Isolation Forest | 4.604 | 232 | 5,04% |
| K-Means | 4.604 | 235 | 5,10% |
| Random Forest | 1.718 | 491 | 28,58% |

O Random Forest cobre **30 janelas e 1.718 registros de teste distintos**, com o primeiro teste em 24/06/2025. MAE = R$ 0,2044, RMSE = R$ 0,3258 e R² = 0,8743. Cada janela tem seu próprio limite, calculado na calibração anterior ao teste. A proporção sinalizada pode exceder 5%, pois o teste não define o limite. As métricas agregadas cobrem produtos com diferentes níveis de preço; consulte também o diagnóstico por produto e mês e a auditoria das datas em `relatorios/resultados.md`.

Esses números correspondem à base e aos parâmetros atuais. Consulte os [resultados completos](relatorios/resultados.md), os [indicadores em JSON](relatorios/comparacao.json) e a [revisão dos casos](relatorios/revisao_casos.md) após novas execuções.

## Painel

```powershell
cd frontend
npm install
npm run dev
```

O painel apresenta filtros por produto, posto, bairro, bandeira e período, gráficos de preços, comparação dos quatro métodos, concordância/Jaccard, sinalizações por registro e pontuações nos detalhes. A tabela pode ser refinada por método sinalizando, pelo menos um método ou dois ou mais métodos, sem alterar a população da comparação. Sua exportação inclui os resultados dos métodos e os indicadores de avaliação.

A comparação inclui cobertura do recorte, resultados por combustível e um diagnóstico expansível do Random Forest por produto e mês, com taxa de alertas e erro médio. Nos detalhes da coleta, os indicadores mostram variação temporal, distância municipal, diferença histórica e previsão/limite da janela do Random Forest. Esses indicadores ajudam a conferir o caso, sem atribuir uma causa à sinalização.

### Revisão de alertas

Nos detalhes de uma coleta, escolha **Pendente**, **Revisado**, **Possível erro de dado** ou **Variação justificável**, registre uma observação e clique em **Salvar revisão**. As revisões são guardadas no armazenamento local do navegador e sobrevivem ao recarregamento da página. A exportação CSV inclui situação, observações, data da revisão e indicação de revisão desatualizada.

As revisões são identificadas por CNPJ, produto e data. Se preços, resultados ou limite temporal mudarem, o painel identifica a revisão como desatualizada e pede nova conferência. A revisão não modifica os resultados dos métodos nem constitui um rótulo validado automaticamente. Não há sincronização entre usuários ou dispositivos; exporte as observações para guardar e compartilhar com o grupo. Limpar os dados do navegador também remove as revisões locais.

### Carregamento dos dados

A base CSV é carregada separadamente do JavaScript. O painel informa o carregamento e oferece **Tentar novamente** em caso de falha. O build gera o CSV como recurso estático; após alterar a base, gere novamente o build para atualizar uma versão publicada.

Abra o endereço exibido pelo Vite. O botão de exportação do cabeçalho baixa todo o recorte dos filtros gerais; o botão da tabela também respeita o filtro de sinalizações. Nos detalhes, registros não avaliados são identificados explicitamente.

Para visualizar a versão compilada:

```powershell
npm run build
npm run preview -- --host 127.0.0.1 --port 5174
```

No PowerShell, se a política de execução impedir `npm`, use `npm.cmd` nos mesmos comandos.

## Verificação

```powershell
python -m unittest discover -s tests
cd frontend
npm run build
npm run lint
node scripts/visual-check.mjs
```

Os testes Python verificam limites por produto, exclusão de séries curtas, comparação apenas de registros avaliados, padronização por produto, separação temporal e ausência de previsões repetidas ou feitas sobre dados de treino.

O teste visual requer Chrome no caminho configurado em `frontend/scripts/visual-check.mjs` e o servidor local na porta 5173. Ele verifica desktop e celular, comparação na população comum, filtros de sinalização, exportação, persistência das revisões após recarga, paginação, detalhes e ausência de erros de interface. Também simula falha no CSV e verifica a recuperação pelo botão de nova tentativa.

Para testar a versão compilada em outro endereço, mantenha o servidor de preview aberto em um terminal e execute em outro, na pasta `frontend`:

```powershell
$env:PREVIEW_URL = 'http://127.0.0.1:5174/'
node scripts/visual-check.mjs
```
