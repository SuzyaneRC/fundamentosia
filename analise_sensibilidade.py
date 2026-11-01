"""Mede quanto os alertas dos quatro métodos dependem dos parâmetros escolhidos."""
from pathlib import Path
from itertools import product
import json
import sys
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / 'Modelos' / 'algoritmos'))
from util_dados import FEATURES_ANOMALIA, carregar_dados, selecionar_registros_aptos, padronizar_features
from isolation_forest import executar_isolation_forest, CONTAMINACOES_TESTE
from kmeans import executar_kmeans
from random_forest import executar_random_forest, COLUNAS_MODELO
from baseline_regressao import aplicar_baseline
from comparar_metodos import METODOS

GRADES = {
    'regressao': list(product((2, 2.5, 3), (3, 3.5, 4))),
    'isolation_forest': list(CONTAMINACOES_TESTE),
    'kmeans': list(product((2, 3, 4, 5), (0.90, 0.95, 0.99))),
    'random_forest': list(product((100, 200, 400), (0.90, 0.95, 0.99))),
}
REFERENCIAS = {'regressao': (2, 3.5), 'isolation_forest': 0.05, 'kmeans': (3, 0.95), 'random_forest': (200, 0.95)}
NOMES_PARAMETROS = {'regressao': 'desvios={}, MAD={}', 'isolation_forest': 'contaminação={}',
                    'kmeans': 'K={}, percentil={}', 'random_forest': 'árvores={}, percentil={}'}
# Faixa descritiva para separar preço alinhado aos outros postos; não é critério de alerta.
FAIXA_MEDIANA_MUNICIPAL = 1.0


def nome_configuracao(metodo, parametros):
    valores = parametros if isinstance(parametros, tuple) else (parametros,)
    return NOMES_PARAMETROS[metodo].format(*valores)


def resultado_vazio(df):
    return pd.Series(False, index=df.index), pd.Series(False, index=df.index)


def rodar_baseline(df, parametros):
    resultado = aplicar_baseline(df, *parametros)
    return resultado['utilizado_regressao'], resultado['anomalia_regressao'], None


def rodar_por_produto(df, executar, minimo_distintos=1):
    # Repete os critérios de aptidão de aplicar_por_produto para cada configuração.
    usados, flags = resultado_vazio(df)
    aptos, _ = selecionar_registros_aptos(df, FEATURES_ANOMALIA)
    for _, grupo in aptos.groupby('Produto', sort=True):
        if len(grupo) < 10:
            continue
        x, _ = padronizar_features(grupo, FEATURES_ANOMALIA)
        if len(np.unique(x, axis=0)) < minimo_distintos:
            continue
        usados.loc[grupo.index] = True
        flags.loc[grupo.index] = executar(x)
    return usados, flags, None


def rodar_isolation_forest(df, contaminacao):
    return rodar_por_produto(df, lambda x: executar_isolation_forest(x, contaminacao)[1])


def rodar_kmeans(df, parametros):
    k, percentil = parametros
    return rodar_por_produto(df, lambda x: executar_kmeans(x, k, percentil)[3], minimo_distintos=k)


def rodar_random_forest(df, parametros):
    usados, flags = resultado_vazio(df)
    aptos, _ = selecionar_registros_aptos(df, COLUNAS_MODELO)
    _, _, _, sinalizados, _, metricas, indices = executar_random_forest(aptos, *parametros)
    usados.loc[indices] = True
    flags.loc[indices] = sinalizados
    return usados, flags, metricas


EXECUTORES = {'regressao': rodar_baseline, 'isolation_forest': rodar_isolation_forest,
              'kmeans': rodar_kmeans, 'random_forest': rodar_random_forest}


def comparar_com_referencia(usados, flags, usados_ref, flags_ref):
    # Compara apenas a interseção avaliada, como na comparação entre métodos.
    comum = usados & usados_ref
    x, y = flags[comum], flags_ref[comum]
    ambos, uniao, total_ref = int((x & y).sum()), int((x | y).sum()), int(y.sum())
    return {'jaccard_referencia': ambos / uniao if uniao else None,
            'alertas_referencia_mantidos': ambos / total_ref if total_ref else None}


def contar(usados, flags):
    avaliados, sinalizados = int(usados.sum()), int((usados & flags).sum())
    return {'avaliados': avaliados, 'sinalizados': sinalizados,
            'taxa': sinalizados / avaliados if avaliados else None}


def resumir_grupos(chaves, execucoes):
    """Devolve uma linha por configuração e valor de agrupamento (produto ou mês)."""
    linhas = []
    for execucao in execucoes:
        for valor, indices in chaves.groupby(chaves).groups.items():
            usados, flags = execucao['usados'].loc[indices], execucao['flags'].loc[indices]
            if usados.any():
                linhas.append({'metodo': execucao['metodo'], 'configuracao': execucao['nome'],
                               'referencia': execucao['referencia'], 'grupo': str(valor), **contar(usados, flags)})
    return linhas


def calcular_estabilidade(df, execucoes):
    """Calcula em que fração das configurações cada registro foi sinalizado, por método."""
    estabilidade = df[['CNPJ da Revenda', 'Produto', 'Data da Coleta', 'Valor de Venda',
                       'mediana_municipal', 'diff_mediana_municipal_percentual']].copy()
    for metodo in METODOS:
        do_metodo = [e for e in execucoes if e['metodo'] == metodo]
        avaliadas = sum(e['usados'].astype(int) for e in do_metodo)
        sinalizadas = sum((e['usados'] & e['flags']).astype(int) for e in do_metodo)
        estabilidade[f'fracao_{metodo}'] = (sinalizadas / avaliadas.where(avaliadas > 0))
    fracoes = estabilidade[[f'fracao_{m}' for m in METODOS]]
    estabilidade['metodos_estaveis'] = fracoes.eq(1).sum(axis=1)
    estabilidade['distancia_municipal'] = estabilidade['diff_mediana_municipal_percentual'].abs()
    return (estabilidade.loc[fracoes.gt(0).any(axis=1)]
            .sort_values(['metodos_estaveis', 'distancia_municipal'], ascending=False)
            .drop(columns='distancia_municipal'))


def percentual(valor):
    return 'N/D' if valor is None or pd.isna(valor) else f'{valor:.2%}'


def faixa(linhas, campo='taxa'):
    valores = [l[campo] for l in linhas if l[campo] is not None]
    return f'{min(valores):.2%} a {max(valores):.2%}' if valores else 'N/D'


def tabela_grupos(titulo, rotulo, linhas):
    saida = ['', titulo, '', f'| Método | {rotulo} | Referência | Faixa entre configurações |', '|---|---|---:|---|']
    for metodo, (nome, _) in METODOS.items():
        grupos = sorted({l['grupo'] for l in linhas if l['metodo'] == metodo})
        for grupo in grupos:
            atuais = [l for l in linhas if l['metodo'] == metodo and l['grupo'] == grupo]
            referencia = next((l for l in atuais if l['referencia']), None)
            saida.append(f"| {nome} | {grupo} | {percentual(referencia['taxa'] if referencia else None)} | {faixa(atuais)} |")
    return saida


def gerar_relatorio(geral, por_produto, por_mes, alinhamento, estaveis):
    linhas = ['# Análise de sensibilidade dos parâmetros', '',
              'Relatório reproduzível gerado por `python analise_sensibilidade.py`. A base consolidada e o painel continuam usando os parâmetros de referência.', '',
              'Mantidos: parcela dos alertas da referência também sinalizada na configuração. Jaccard e mantidos usam a interseção dos registros avaliados.', '',
              '| Método | Configuração | Avaliados | Sinalizados | Taxa | Jaccard com a referência | Mantidos | MAE (R$) |',
              '|---|---|---:|---:|---:|---:|---:|---:|']
    for r in geral:
        marca = ' (referência)' if r['referencia'] else ''
        mae = f"{r['mae']:.4f}" if r.get('mae') is not None else '—'
        linhas.append(f"| {METODOS[r['metodo']][0]} | {r['configuracao']}{marca} | {r['avaliados']} | {r['sinalizados']} | {percentual(r['taxa'])} | {percentual(r['jaccard_referencia'])} | {percentual(r['alertas_referencia_mantidos'])} | {mae} |")
    linhas += ['', '## Alertas próximos à mediana dos outros postos', '',
               f'Alertas da referência com preço a até {FAIXA_MEDIANA_MUNICIPAL:g}% da mediana do mesmo dia. Sugerem acompanhamento do mercado local, sem excluir a necessidade de conferência; alertas sem mediana disponível ficam fora da conta.', '',
               '| Método | Alertas com mediana | Próximos da mediana | Parcela |', '|---|---:|---:|---:|']
    for metodo, r in alinhamento.items():
        linhas.append(f"| {METODOS[metodo][0]} | {r['com_mediana']} | {r['proximos']} | {percentual(r['parcela'])} |")
    linhas += ['', '## Alertas estáveis', '',
               'Um alerta é estável em um método quando é sinalizado em todas as configurações que avaliaram o registro. A lista por registro está em `relatorios/estabilidade_alertas.csv`.', '',
               '| Métodos em que o alerta é estável | Registros |', '|---:|---:|']
    linhas += [f'| {quantidade} | {total} |' for quantidade, total in estaveis.items()]
    linhas += tabela_grupos('## Taxa por produto', 'Produto', por_produto)
    linhas += tabela_grupos('## Taxa por mês', 'Mês', por_mes)
    linhas += ['', '## Limitações', '',
               '- Nos métodos não supervisionados, a taxa acompanha o parâmetro por construção; a estabilidade dos registros sinalizados é o indicador mais informativo.',
               '- A grade não escolhe parâmetros melhores: sem rótulos confirmados não é possível calcular precisão e recall.',
               '- Sinalização estável indica robustez à configuração, não irregularidade.']
    return '\n'.join(linhas) + '\n'


def main():
    df = carregar_dados()
    datas = pd.to_datetime(df['Data da Coleta'], dayfirst=True)
    execucoes = []
    for metodo, grade in GRADES.items():
        for parametros in grade:
            usados, flags, metricas = EXECUTORES[metodo](df, parametros)
            execucoes.append({'metodo': metodo, 'nome': nome_configuracao(metodo, parametros),
                              'referencia': parametros == REFERENCIAS[metodo],
                              'usados': usados, 'flags': flags, 'metricas': metricas})
            print(f"{execucoes[-1]['nome']}: {int((usados & flags).sum())} de {int(usados.sum())}", flush=True)
    referencias = {e['metodo']: e for e in execucoes if e['referencia']}
    geral = []
    for e in execucoes:
        ref = referencias[e['metodo']]
        linha = {'metodo': e['metodo'], 'configuracao': e['nome'], 'referencia': e['referencia'],
                 **contar(e['usados'], e['flags']),
                 **comparar_com_referencia(e['usados'], e['flags'], ref['usados'], ref['flags'])}
        if e['metricas']:
            linha.update(mae=e['metricas']['mae'], rmse=e['metricas']['rmse'], r2=e['metricas']['r2'])
        geral.append(linha)
    por_produto = resumir_grupos(df['Produto'], execucoes)
    por_mes = resumir_grupos(datas.dt.to_period('M').astype(str), execucoes)
    alinhamento = {}
    for metodo, ref in referencias.items():
        distancia = df.loc[ref['usados'] & ref['flags'], 'diff_mediana_municipal_percentual'].dropna().abs()
        proximos = int(distancia.le(FAIXA_MEDIANA_MUNICIPAL).sum())
        alinhamento[metodo] = {'com_mediana': len(distancia), 'proximos': proximos,
                               'parcela': proximos / len(distancia) if len(distancia) else None}
    estabilidade = calcular_estabilidade(df, execucoes)
    estaveis = {int(k): int(v) for k, v in estabilidade['metodos_estaveis'].value_counts().sort_index(ascending=False).items()}
    relatorios = RAIZ / 'relatorios'
    relatorios.mkdir(exist_ok=True)
    estabilidade.to_csv(relatorios / 'estabilidade_alertas.csv', sep=';', decimal=',', encoding='utf-8-sig', index=False)
    conteudo = {'geral': geral, 'por_produto': por_produto, 'por_mes': por_mes,
                'alertas_proximos_mediana': alinhamento, 'registros_por_metodos_estaveis': estaveis}
    (relatorios / 'sensibilidade.json').write_text(json.dumps(conteudo, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    (relatorios / 'sensibilidade.md').write_text(gerar_relatorio(geral, por_produto, por_mes, alinhamento, estaveis), encoding='utf-8')


if __name__ == '__main__':
    main()
