# Detecção de anomalias em preços de combustíveis

Projeto da disciplina de Fundamentos de Inteligência Artificial para identificar comportamentos atípicos nos preços de combustíveis publicados pela Agência Nacional do Petróleo, Gás Natural e Biocombustíveis (ANP).

O estudo utiliza somente dados de Aracaju (SE) e compara os preços de cada produto em cada posto ao longo do tempo. O objetivo é sinalizar registros que mereçam análise humana, sem afirmar que um preço é abusivo ou que existe alguma irregularidade.

## Escopo

O projeto prevê:

- importar, limpar e padronizar as planilhas públicas da ANP;
- analisar o histórico de preços por posto e produto;
- calcular diferenças e variações ao longo do tempo;
- testar K-Means, Random Forest e Isolation Forest;
- comparar os modelos com um método estatístico baseado em regressão;
- atribuir uma pontuação de anomalia aos registros;
- explicar os fatores que contribuíram para cada sinalização;
- apresentar os resultados em uma tela com filtros.

## Requisitos

- Python 3.9 ou superior
- pandas
- Node.js 20 ou superior
- npm
- numpy
- scikit-learn

## Como executar

Clone o repositório e entre na pasta do projeto:

```powershell
git clone https://github.com/SuzyaneRC/fundamentosia.git
cd fundamentosia
```

Crie e ative um ambiente virtual no Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

No Linux ou macOS, ative com:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instale a dependência atual:

```powershell
python -m pip install pandas numpy scikit-learn
```

Coloque as planilhas CSV da ANP na pasta `planilhas`. Os arquivos devem utilizar codificação UTF-8, separador `;` e manter os nomes das colunas da fonte.

Gere a base limpa:

```powershell
python criaBaseBruta.py
```

Consulte as métricas básicas da base gerada:

```powershell
python metricasBaseBruta.py
```

Baseline de regressão:

Após o processamento temporal da base, o projeto utiliza um modelo de regressão linear como método baseline para estimar o preço esperado de cada produto ao longo do tempo.

```powershell
python baseline_regressao.py
```

O método:

- realiza a regressão separadamente para cada produto;

- utiliza o tempo como variável explicativa;

- calcula o preço estimado;

- calcula o resíduo entre o preço observado e o preço estimado;

- utiliza o desvio padrão e o MAD (Median Absolute Deviation) para identificar resíduos atípicos;

- gera uma pontuação de anomalia baseada no tamanho do resíduo;

- cria a coluna anomalia_regressao para sinalizar os registros identificados.

Como resultado, é gerado o arquivo dados_aracaju_baseline.csv, que contém os dados processados juntamente com as informações produzidas pelo baseline de regressão.

Os comandos devem ser executados na raiz do repositório, onde estão os arquivos Python.

### Executar o painel

Depois de gerar `base_bruta_aracaju.csv`, instale as dependências do frontend:

```powershell
cd frontend
npm install
```

Inicie o servidor de desenvolvimento:

```powershell
npm run dev
```

Abra o endereço exibido no terminal. O painel oferece filtros por produto, posto, bairro, bandeira e período, além de indicadores, gráficos, tabela e exportação dos registros filtrados.

## Resultado esperado

Ao executar `criaBaseBruta.py`, será criado ou atualizado o arquivo `base_bruta_aracaju.csv`. O terminal mostrará a quantidade de registros antes e depois da limpeza, os valores ausentes e os registros inválidos ou repetidos encontrados.

Após o processamento temporal, será gerado o arquivo `dados_aracaju_processados.csv`, contendo as variáveis históricas e temporais utilizadas nas etapas de análise.

Ao executar `baseline_regressao.py`, será gerado o arquivo `dados_aracaju_baseline.csv`, contendo os preços estimados pela regressão, os resíduos, a pontuação de anomalia e a sinalização dos registros considerados atípicos pelo baseline.