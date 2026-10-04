"""Baseline descritivo com regressão e limites por produto."""
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def aplicar_baseline(df):
    df = df.copy()
    datas = pd.to_datetime(df['Data da Coleta'], dayfirst=True, errors='coerce')
    df['tempo'] = (datas - datas.min()).dt.days
    df['utilizado_regressao'] = False
    for coluna in ['preco_estimado', 'residuo_regressao', 'score_mad', 'pontuacao_anomalia', 'limite_desvio_produto', 'mad_produto']:
        df[coluna] = np.nan
    for coluna in ['anomalia_desvio_padrao', 'anomalia_mad', 'anomalia_regressao']:
        df[coluna] = False
    aptos = (~df['poucos_registros'].astype(str).str.lower().eq('true') & df['tempo'].notna() & df['Valor de Venda'].gt(0))
    for produto, grupo in df.loc[aptos].groupby('Produto'):
        if len(grupo) < 3 or grupo['tempo'].nunique() < 2:
            continue
        modelo = LinearRegression().fit(grupo[['tempo']], grupo['Valor de Venda'])
        estimado = modelo.predict(grupo[['tempo']])
        residuo = grupo['Valor de Venda'] - estimado
        desvio = residuo.std()
        centro = residuo.median()
        mad = (residuo - centro).abs().median()
        score = residuo.abs() / desvio if desvio > 1e-12 else np.where(residuo.abs() > 1e-12, np.inf, 0)
        score_mad = (residuo - centro).abs() / (1.4826 * mad) if mad > 1e-12 else np.where((residuo - centro).abs() > 1e-12, np.inf, 0)
        indices = grupo.index
        df.loc[indices, 'utilizado_regressao'] = True
        for coluna, valores in [('preco_estimado', estimado), ('residuo_regressao', residuo), ('pontuacao_anomalia', score), ('score_mad', score_mad), ('limite_desvio_produto', 2 * desvio), ('mad_produto', mad)]:
            df.loc[indices, coluna] = valores
        df.loc[indices, 'anomalia_desvio_padrao'] = np.asarray(score) > 2
        df.loc[indices, 'anomalia_mad'] = np.asarray(score_mad) > 3.5
        df.loc[indices, 'anomalia_regressao'] = (np.asarray(score) > 2) | (np.asarray(score_mad) > 3.5)
    return df


if __name__ == '__main__':
    from Modelos.algoritmos.util_dados import carregar_dados
    dados = aplicar_baseline(carregar_dados())
    dados.to_csv('dados_aracaju_baseline.csv', sep=';', decimal=',', encoding='utf-8-sig', index=False)
    print(dados.groupby('Produto')['anomalia_regressao'].sum().to_string())
