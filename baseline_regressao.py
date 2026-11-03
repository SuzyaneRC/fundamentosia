"""Método 1, baseline: compara cada preço com a tendência geral do produto no tempo.

É a referência simples com que os modelos de IA são comparados. Para cada produto:
    1. Ajusta uma reta (regressão linear): preço em função dos dias desde a 1ª coleta.
    2. Calcula o resíduo de cada registro: preço real - preço estimado pela reta.
    3. Sinaliza resíduos atípicos por dois critérios, e basta um deles:
       - Desvio padrão: |resíduo| / desvio padrão > limite_desvios.
       - MAD (desvio absoluto mediano): distância até a mediana dos resíduos, dividida
         por 1,4826 x MAD. A constante deixa o MAD na escala do desvio padrão em dados
         normais. Por usar medianas, sofre menos influência de valores extremos.

É descritivo: a reta usa todos os dados, inclusive datas posteriores ao registro.
Portanto, não mede capacidade de previsão.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def aplicar_baseline(df, limite_desvios=2, limite_mad=3.5):
    """Devolve uma cópia de `df` com o resultado do baseline em novas colunas.

    Principais colunas: `preco_estimado`, `residuo_regressao`, `pontuacao_anomalia`
    (resíduo em desvios padrão), `score_mad`, `utilizado_regressao` (foi avaliado) e
    `anomalia_regressao` (foi sinalizado).
    """
    df = df.copy()
    datas = pd.to_datetime(df['Data da Coleta'], dayfirst=True, errors='coerce')
    df['tempo'] = (datas - datas.min()).dt.days
    df['utilizado_regressao'] = False
    for coluna in ['preco_estimado', 'residuo_regressao', 'score_mad', 'pontuacao_anomalia', 'limite_desvio_produto', 'mad_produto']:
        df[coluna] = np.nan
    for coluna in ['anomalia_desvio_padrao', 'anomalia_mad', 'anomalia_regressao']:
        df[coluna] = False
    # Ficam fora as séries curtas e os registros sem data ou com preço inválido.
    aptos = (~df['poucos_registros'].astype(str).str.lower().eq('true') & df['tempo'].notna() & df['Valor de Venda'].gt(0))
    for produto, grupo in df.loc[aptos].groupby('Produto'):
        if len(grupo) < 3 or grupo['tempo'].nunique() < 2:
            continue
        modelo = LinearRegression().fit(grupo[['tempo']], grupo['Valor de Venda'])
        estimado = modelo.predict(grupo[['tempo']])
        residuo = grupo['Valor de Venda'] - estimado
        desvio = residuo.std()
        # Com dispersão zero não há como dividir: qualquer resíduo diferente de zero
        # recebe pontuação infinita (é sinalizado) e resíduo zero recebe pontuação 0.
        centro = residuo.median()
        mad = (residuo - centro).abs().median()
        score = residuo.abs() / desvio if desvio > 1e-12 else np.where(residuo.abs() > 1e-12, np.inf, 0)
        score_mad = (residuo - centro).abs() / (1.4826 * mad) if mad > 1e-12 else np.where((residuo - centro).abs() > 1e-12, np.inf, 0)
        indices = grupo.index
        df.loc[indices, 'utilizado_regressao'] = True
        for coluna, valores in [('preco_estimado', estimado), ('residuo_regressao', residuo), ('pontuacao_anomalia', score), ('score_mad', score_mad), ('limite_desvio_produto', limite_desvios * desvio), ('mad_produto', mad)]:
            df.loc[indices, coluna] = valores
        df.loc[indices, 'anomalia_desvio_padrao'] = np.asarray(score) > limite_desvios
        df.loc[indices, 'anomalia_mad'] = np.asarray(score_mad) > limite_mad
        df.loc[indices, 'anomalia_regressao'] = (np.asarray(score) > limite_desvios) | (np.asarray(score_mad) > limite_mad)
    return df


if __name__ == '__main__':
    from Modelos.algoritmos.util_dados import carregar_dados
    dados = aplicar_baseline(carregar_dados())
    dados.to_csv('dados_aracaju_baseline.csv', sep=';', decimal=',', encoding='utf-8-sig', index=False)
    print(dados.groupby('Produto')['anomalia_regressao'].sum().to_string())
