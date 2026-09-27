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
python -m pip install pandas
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

Os comandos devem ser executados na raiz do repositório, onde estão os arquivos Python.

## Resultado esperado

Ao executar `criaBaseBruta.py`, será criado ou atualizado o arquivo `base_bruta_aracaju.csv`. O terminal mostrará a quantidade de registros antes e depois da limpeza, os valores ausentes e os registros inválidos ou repetidos encontrados.

O arquivo final contém os dados de revenda, CNPJ, bairro, produto, data da coleta, valor de venda e bandeira.