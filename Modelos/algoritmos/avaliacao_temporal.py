"""Janelas crescentes: cada previsão usa somente datas anteriores ao teste."""
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def criar_janelas(datas):
    dias = np.sort(pd.Series(datas).dropna().unique())
    if len(dias) < 10:
        return []
    aquecimento = max(4, int(len(dias) * 0.4))
    tamanho = max(2, int(len(dias) * 0.1))
    janelas = []
    for inicio in range(aquecimento + tamanho, len(dias), tamanho):
        inicio_calibracao = inicio - tamanho
        fim = min(inicio + tamanho, len(dias))
        janelas.append((dias[:inicio_calibracao], dias[inicio_calibracao:inicio], dias[inicio:fim]))
    return janelas


def avaliar_janelas(df, features, target, criar_modelo, percentil=0.95):
    previsoes, erros, flags, limites, indices = [], [], [], [], []
    detalhes = []
    ultimo_modelo = None
    for produto, grupo in df.groupby('Produto', sort=True):
        datas = pd.to_datetime(grupo['Data da Coleta'], dayfirst=True, errors='coerce')
        for numero, (dias_treino, dias_cal, dias_teste) in enumerate(criar_janelas(datas), 1):
            treino = grupo.loc[datas.isin(dias_treino)]
            cal = grupo.loc[datas.isin(dias_cal)]
            teste = grupo.loc[datas.isin(dias_teste)]
            if len(treino) < 20 or len(cal) < 5 or teste.empty:
                continue
            modelo = criar_modelo()
            modelo.fit(treino[features], treino[target])
            erro_cal = np.abs(cal[target].to_numpy() - modelo.predict(cal[features]))
            limite = float(np.quantile(erro_cal, percentil))
            previsto = modelo.predict(teste[features])
            erro = np.abs(teste[target].to_numpy() - previsto)
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
    metricas = {
        'mae': float(mean_absolute_error(real, previsoes)),
        'rmse': float(np.sqrt(mean_squared_error(real, previsoes))),
        'r2': float(r2_score(real, previsoes)) if len(indices) > 1 and np.var(real) > 0 else None,
        'teste': len(indices), 'janelas': detalhes,
        'inicio_teste': min(j['inicio_teste'] for j in detalhes),
    }
    return ultimo_modelo, np.asarray(previsoes), np.asarray(erros), np.asarray(flags), np.asarray(limites), metricas, pd.Index(indices)
