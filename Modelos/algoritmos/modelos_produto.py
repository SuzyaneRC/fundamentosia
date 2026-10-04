"""Padronização e modelos não supervisionados independentes por combustível."""
import numpy as np
from util_dados import FEATURES_ANOMALIA, selecionar_registros_aptos, padronizar_features
from isolation_forest import executar_isolation_forest, testar_contaminacoes, aplicar_resultados as aplicar_if
from kmeans import executar_kmeans, aplicar_resultados as aplicar_km, N_CLUSTERS


def aplicar_por_produto(df):
    aptos, _ = selecionar_registros_aptos(df, FEATURES_ANOMALIA)
    if_indices, if_flags, if_scores = [], [], []
    km_indices, km_clusters, km_flags, km_scores = [], [], [], []
    limites = {}
    testes = {}
    for produto, grupo in aptos.groupby('Produto', sort=True):
        # Histórico muito pequeno/constante permanece explicitamente não avaliado.
        if len(grupo) < 10:
            continue
        x, _ = padronizar_features(grupo, FEATURES_ANOMALIA)
        _, flags, scores = executar_isolation_forest(x)
        if_indices.extend(grupo.index)
        if_flags.extend(flags)
        if_scores.extend(scores)
        testes[str(produto)] = testar_contaminacoes(x)
        if len(np.unique(x, axis=0)) < N_CLUSTERS:
            continue
        _, clusters, scores, flags, limite = executar_kmeans(x)
        km_indices.extend(grupo.index)
        km_clusters.extend(clusters)
        km_flags.extend(flags)
        km_scores.extend(scores)
        limites[str(produto)] = limite
    resultado = aplicar_if(df, if_indices, if_flags, if_scores)
    resultado = aplicar_km(resultado, km_indices, km_clusters, km_scores, km_flags)
    resultado['limite_kmeans'] = resultado['Produto'].map(limites)
    return resultado, limites, testes
