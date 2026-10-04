"""Executa os quatro métodos e atualiza a mesma base usada pelo painel."""
from pathlib import Path
from itertools import combinations
import json
import sys
import pandas as pd

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / 'Modelos' / 'algoritmos'))
from util_dados import carregar_dados, selecionar_registros_aptos
from modelos_produto import aplicar_por_produto
from random_forest import executar_random_forest, aplicar_resultados as aplicar_rf, COLUNAS_MODELO
from baseline_regressao import aplicar_baseline

METODOS = {
    'regressao': ('Baseline', 'pontuacao_anomalia'),
    'isolation_forest': ('Isolation Forest', 'score_isolation_forest'),
    'kmeans': ('K-Means', 'score_kmeans'),
    'random_forest': ('Random Forest', 'erro_abs_random_forest'),
}


def comparar(df):
    pares = []
    for a, b in combinations(METODOS, 2):
        comum = df[f'utilizado_{a}'] & df[f'utilizado_{b}']
        x, y = df.loc[comum, f'anomalia_{a}'], df.loc[comum, f'anomalia_{b}']
        uniao, ambos = int((x | y).sum()), int((x & y).sum())
        pares.append({'metodo_a': a, 'metodo_b': b, 'avaliados_em_comum': int(comum.sum()),
                      'sinalizados_por_ambos': ambos, 'uniao_sinalizados': uniao,
                      'concordancia': float((x == y).mean()) if len(x) else None,
                      'jaccard': ambos / uniao if uniao else None})
    return pares


def main():
    df = aplicar_baseline(carregar_dados())
    df, limite_km, contaminacoes = aplicar_por_produto(df)
    aptos_rf, _ = selecionar_registros_aptos(df, COLUNAS_MODELO)
    _, previsoes, erros, flags, limite_rf, metricas, indices_teste = executar_random_forest(aptos_rf)
    df = aplicar_rf(df, indices_teste, previsoes, erros, flags)
    df['limite_erro_random_forest'] = float('nan')
    df.loc[indices_teste, 'limite_erro_random_forest'] = limite_rf
    df['janela_random_forest'] = ''
    datas = pd.to_datetime(df['Data da Coleta'], dayfirst=True)
    for janela in metricas['janelas']:
        mascara = (df['Produto'].eq(janela['produto']) & df['utilizado_random_forest']
                   & datas.between(janela['inicio_teste'], janela['fim_teste']))
        df.loc[mascara, 'janela_random_forest'] = f"{janela['produto']} / {janela['janela']}"
    df['metodos_avaliados'] = sum(df[f'utilizado_{m}'].astype(int) for m in METODOS)
    df['metodos_sinalizando'] = sum((df[f'utilizado_{m}'] & df[f'anomalia_{m}']).astype(int) for m in METODOS)
    resumo = {m: {'nome': nome, 'avaliados': int(df[f'utilizado_{m}'].sum()),
                  'sinalizados': int(df[f'anomalia_{m}'].sum())} for m, (nome, _) in METODOS.items()}
    pares = comparar(df)
    relatorios = RAIZ / 'relatorios'
    relatorios.mkdir(exist_ok=True)
    por_produto = {}
    for produto, grupo in df.groupby('Produto'):
        por_produto[str(produto)] = {
            m: {'avaliados': int(grupo[f'utilizado_{m}'].sum()), 'sinalizados': int(grupo[f'anomalia_{m}'].sum())}
            for m in METODOS
        }
    por_mes = []
    rf = df.loc[df['utilizado_random_forest']].copy()
    rf['mes'] = pd.to_datetime(rf['Data da Coleta'], dayfirst=True).dt.to_period('M').astype(str)
    for (produto, mes), grupo in rf.groupby(['Produto', 'mes']):
        por_mes.append({'produto': str(produto), 'mes': str(mes), 'avaliados': len(grupo),
                       'sinalizados': int(grupo['anomalia_random_forest'].sum()),
                       'mae': float(grupo['erro_abs_random_forest'].mean())})
    conteudo = {'metodos': resumo, 'comparacoes': pares, 'random_forest': metricas,
                'por_produto': por_produto, 'random_forest_por_mes': por_mes,
                'limite_distancia_kmeans': limite_km,
                'testes_contaminacao': contaminacoes}
    (relatorios / 'comparacao.json').write_text(json.dumps(conteudo, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    linhas = ['# Resultados e comparação dos métodos', '',
              'Relatório reproduzível gerado por `python comparar_metodos.py`.', '',
              '| Método | Avaliados | Sinalizados | Taxa |', '|---|---:|---:|---:|']
    for r in resumo.values():
        taxa = f"{r['sinalizados']/r['avaliados']:.2%}" if r['avaliados'] else 'N/D'
        linhas.append(f"| {r['nome']} | {r['avaliados']} | {r['sinalizados']} | {taxa} |")
    linhas += ['', '## Concordância na interseção dos registros avaliados', '',
               '| Par | Em comum | Ambos sinalizam | Concordância total | Jaccard das sinalizações |', '|---|---:|---:|---:|---:|']
    for p in pares:
        concordancia = f"{p['concordancia']:.2%}" if p['concordancia'] is not None else 'N/D'
        jaccard = f"{p['jaccard']:.2%}" if p['jaccard'] is not None else 'N/D'
        linhas.append(f"| {METODOS[p['metodo_a']][0]} × {METODOS[p['metodo_b']][0]} | {p['avaliados_em_comum']} | {p['sinalizados_por_ambos']} | {concordancia} | {jaccard} |")
    linhas += ['', '## Random Forest: avaliação temporal', '',
               f'{len(metricas["janelas"])} janelas por produto; {metricas["teste"]} previsões de teste distintas. Primeiro teste desde {metricas["inicio_teste"]}.',
               f'MAE: R$ {metricas["mae"]:.4f}; RMSE: R$ {metricas["rmse"]:.4f}; R²: {metricas["r2"]:.4f}.',
               'Cada janela calibra seu próprio limite no percentil 95 dos erros anteriores ao teste. Não há previsão de treino na pontuação.', '',
               '## Casos para conferência', '',
               'Amostra por consenso e distância municipal. A sinalização não comprova irregularidade.', '',
               '| CNPJ | Produto | Data | Preço | Mediana dos outros postos | Diferença % | Métodos sinalizando / avaliados |',
               '|---|---|---|---:|---:|---:|---:|']
    casos = df.loc[df['metodos_sinalizando'] > 0].assign(distancia=lambda d: d['diff_mediana_municipal_percentual'].abs()).sort_values(['metodos_sinalizando', 'distancia'], ascending=False).head(10)
    for _, r in casos.iterrows():
        linhas.append(f"| {r['CNPJ da Revenda']} | {r['Produto']} | {r['Data da Coleta']} | {r['Valor de Venda']:.2f} | {r['mediana_municipal']:.2f} | {r['diff_mediana_municipal_percentual']:.2f} | {r['metodos_sinalizando']} / {r['metodos_avaliados']} |")
    linhas += ['', '## Parâmetros e limitações', '',
               '- Baseline: regressão linear por produto, tempo em dias; resíduos acima de 2 desvios padrão ou 3,5 MAD normalizado. Limites por produto; séries com menos de 3 registros excluídas.',
               '- Isolation Forest: 100 árvores, seed 42, contaminação inicial 5%; testes de 1%, 3%, 5% e 10%.',
               '- K-Means: 3 grupos, n_init=10, seed 42; distância ao centroide, limite no percentil 95.',
               '- IA não supervisionada: modelos e StandardScaler independentes por produto, sobre preço, variação percentual, diferença histórica e diferença municipal percentual. Ajuste descritivo na base inteira; não mede generalização futura. Grupos com menos de 10 registros aptos ficam fora; K-Means também exige 3 vetores distintos.',
               '- Random Forest: 200 árvores, seed 42; treino inicial com 40% das datas distintas, calibração e testes em blocos de aproximadamente 10%. Treino crescente e testes sem sobreposição, por produto. Exige 20 registros de treino, 5 de calibração e 10 datas distintas. Somente teste recebe pontuação. O total final da série foi removido das entradas para evitar informação futura.',
               '- A mediana municipal usa outros postos no mesmo dia: é uma referência contemporânea, que exige coletas daquele dia; não é previsão antecipada.',
               '- Baseline é descritivo e ajustado na base analisada. Não deve ser interpretado como previsão fora do treino.',
               '- Pontuações têm escalas diferentes. Compare sinalizações e rankings, não os valores brutos entre métodos.',
               '- Concordância total pode ser alta pela predominância de registros não sinalizados; Jaccard compara apenas a união das sinalizações.',
               '- Não há rótulos de anomalias confirmadas: concordância e coerência não substituem precisão/recall nem validação humana.',
               '- Próximos testes: K=2/3/4/5, percentis 90/95/99, RF 100/200/400 árvores e limites baseline 2/2,5/3 desvios e 3/3,5/4 MAD. Comparar por produto e em janelas temporais.']
    linhas += ['', '## Diagnóstico por produto e mês — Random Forest', '',
               '| Produto | Mês | Avaliados | Sinalizados | Taxa | MAE |', '|---|---|---:|---:|---:|---:|']
    for r in por_mes:
        linhas.append(f"| {r['produto']} | {r['mes']} | {r['avaliados']} | {r['sinalizados']} | {r['sinalizados']/r['avaliados']:.2%} | {r['mae']:.4f} |")
    linhas += ['', '## Auditoria das janelas temporais', '',
               '| Produto | Janela | Fim treino | Calibração | Teste | N treino / cal / teste | Limite |', '|---|---:|---|---|---|---|---:|']
    for j in metricas['janelas']:
        linhas.append(f"| {j['produto']} | {j['janela']} | {j['fim_treino']} | {j['inicio_calibracao']} a {j['fim_calibracao']} | {j['inicio_teste']} a {j['fim_teste']} | {j['treino']} / {j['calibracao']} / {j['teste']} | {j['limite_erro']:.4f} |")
    (relatorios / 'resultados.md').write_text('\n'.join(linhas) + '\n', encoding='utf-8')
    df.to_csv(RAIZ / 'dados_aracaju_processados.csv', sep=';', decimal=',', encoding='utf-8-sig', index=False)
    # Compatibilidade com os scripts individuais; a interface usa somente a base consolidada.
    df.to_csv(RAIZ / 'dados_aracaju_baseline.csv', sep=';', decimal=',', encoding='utf-8-sig', index=False)
    for metodo in ('isolation_forest', 'kmeans', 'random_forest'):
        pasta = RAIZ / 'Modelos' / 'Saídas'
        df.to_csv(pasta / f'resultado_{metodo}.csv', sep=';', decimal=',', encoding='utf-8-sig', index=False)
        (pasta / f'anomalias_{metodo}.txt').write_text(str(resumo[metodo]['sinalizados']) + '\n', encoding='utf-8')
    print(json.dumps(conteudo, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
