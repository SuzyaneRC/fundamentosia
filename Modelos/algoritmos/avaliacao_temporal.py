"""Janelas crescentes: cada previsão usa somente datas anteriores ao teste.

Simula o uso real do modelo, que só conheceria o passado. Com datas em ordem:

    janela 1: [ treino ][ calibração ][ teste ]
    janela 2: [ treino ............. ][ calibração ][ teste ]
    janela 3: [ treino .......................... ][ calibração ][ teste ]

- Treino: ajusta o modelo.
- Calibração: mede os erros do modelo em datas que ele não viu e define o limite.
- Teste: recebe a previsão e o alerta. Cada registro é testado no máximo uma vez.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

CASAS_DECIMAIS = 8


def criar_janelas(datas):
    """Devolve uma lista de (dias de treino, dias de calibração, dias de teste).

    A divisão usa datas distintas, não linhas, para que coletas do mesmo dia nunca fiquem
    em conjuntos diferentes. Com menos de 10 datas, não há janelas.
    """
    dias = np.sort(pd.Series(datas).dropna().unique())
    if len(dias) < 10:
        return []
    # Cerca de 40% das datas formam o treino inicial; cada bloco seguinte tem cerca de 10%.
    aquecimento = max(4, int(len(dias) * 0.4))
    tamanho = max(2, int(len(dias) * 0.1))
    janelas = []
    for inicio in range(aquecimento + tamanho, len(dias), tamanho):
        inicio_calibracao = inicio - tamanho
        fim = min(inicio + tamanho, len(dias))
        janelas.append((dias[:inicio_calibracao], dias[inicio_calibracao:inicio], dias[inicio:fim]))
    return janelas


def avaliar_janelas(df, features, target, criar_modelo, percentil=0.95):
    """Treina um modelo novo por produto e janela e sinaliza erros acima do limite.

    O limite é o `percentil` dos erros da calibração da própria janela. Por isso, a taxa
    no teste pode passar muito de 5% quando os preços mudam depois da calibração.

    Devolve (último modelo, previsões, erros, sinalizações, limites, métricas, índices).
    Os arrays seguem a ordem de `índices`, e `métricas['janelas']` detalha cada janela.
    """
    previsoes, erros, flags, limites, indices = [], [], [], [], []
    detalhes = []
    ultimo_modelo = None
    for produto, grupo in df.groupby('Produto', sort=True):
        datas = pd.to_datetime(grupo['Data da Coleta'], dayfirst=True, errors='coerce')
        for numero, (dias_treino, dias_cal, dias_teste) in enumerate(criar_janelas(datas), 1):
            treino = grupo.loc[datas.isin(dias_treino)]
            cal = grupo.loc[datas.isin(dias_cal)]
            teste = grupo.loc[datas.isin(dias_teste)]
            # Sem dados suficientes, a janela é ignorada e seus registros ficam não avaliados.
            if len(treino) < 20 or len(cal) < 5 or teste.empty:
                continue
            modelo = criar_modelo()
            modelo.fit(treino[features], treino[target])
            # A soma paralela das árvores varia em ruído numérico; sem arredondar, empates com o limite mudam entre execuções.
            erro_cal = np.round(np.abs(cal[target].to_numpy() - np.round(modelo.predict(cal[features]), CASAS_DECIMAIS)), CASAS_DECIMAIS)
            limite = round(float(np.quantile(erro_cal, percentil)), CASAS_DECIMAIS)
            previsto = np.round(modelo.predict(teste[features]), CASAS_DECIMAIS)
            erro = np.round(np.abs(teste[target].to_numpy() - previsto), CASAS_DECIMAIS)
            # Erro zero não é anomalia, mesmo quando a calibração é constante.
            anomalia = (erro >= limite) & (erro > 1e-12)
            indices.extend(teste.index.tolist())
            previsoes.extend(previsto)
            erros.extend(erro)
            flags.extend(anomalia)
            limites.extend([limite] * len(teste))
            detalhes.append({
                'produto': str(produto), 'janela': numero,
                'treino': len(treino), 'calibracao': len(cal), 'teste': len(teste),
                'fim_treino': str(pd.Timestamp(dias_treino[-1]).date()),
                'inicio_calibracao': str(pd.Timestamp(dias_cal[0]).date()),
                'fim_calibracao': str(pd.Timestamp(dias_cal[-1]).date()),
                'inicio_teste': str(pd.Timestamp(dias_teste[0]).date()),
                'fim_teste': str(pd.Timestamp(dias_teste[-1]).date()),
                'limite_erro': limite, 'mae': float(erro.mean()),
                'rmse': float(np.sqrt(np.mean(erro ** 2))),
                'sinalizados': int(anomalia.sum()),
            })
            ultimo_modelo = modelo
    if not indices:
        raise ValueError('Sem histórico suficiente para treino, calibração e teste temporal.')
    if len(indices) != len(set(indices)):
        raise AssertionError('Um registro recebeu mais de uma previsão de teste.')
    real = df.loc[indices, target].to_numpy()
    # MAE: erro médio em R$. RMSE: pesa mais os erros grandes. R²: 1 seria previsão perfeita.
    metricas = {
        'mae': float(mean_absolute_error(real, previsoes)),
        'rmse': float(np.sqrt(mean_squared_error(real, previsoes))),
        'r2': float(r2_score(real, previsoes)) if len(indices) > 1 and np.var(real) > 0 else None,
        'teste': len(indices), 'janelas': detalhes,
        'inicio_teste': min(j['inicio_teste'] for j in detalhes),
    }
    return ultimo_modelo, np.asarray(previsoes), np.asarray(erros), np.asarray(flags), np.asarray(limites), metricas, pd.Index(indices)
