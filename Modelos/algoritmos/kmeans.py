import numpy as np
from sklearn.cluster import KMeans

from util_dados import (
    FEATURES_ANOMALIA,
    carregar_dados,
    imprimir_resumo_base,
    padronizar_features,
    salvar_numero_txt,
    salvar_resultados,
    selecionar_registros_aptos,
    validar_colunas,
)


N_CLUSTERS = 3
PERCENTIL_ANOMALIA = 0.95
RANDOM_STATE = 42


def executar_kmeans(x_scaled):
    modelo = KMeans(
        n_clusters=N_CLUSTERS,
        random_state=RANDOM_STATE,
        n_init=10,
    )
    clusters = modelo.fit_predict(x_scaled)
    distancias = modelo.transform(x_scaled)
    scores = distancias.min(axis=1)
    limite_anomalia = float(np.quantile(scores, PERCENTIL_ANOMALIA))
    anomalias = scores >= limite_anomalia
    return modelo, clusters, scores, anomalias, limite_anomalia


def aplicar_resultados(df_original, indices_modelo, clusters, scores, anomalias):
    df_resultado = df_original.copy()
    df_resultado["utilizado_kmeans"] = False
    df_resultado["cluster_kmeans"] = ""
    df_resultado["score_kmeans"] = float("nan")
    df_resultado["anomalia_kmeans"] = False

    df_resultado.loc[indices_modelo, "utilizado_kmeans"] = True
    df_resultado.loc[indices_modelo, "cluster_kmeans"] = clusters
    df_resultado.loc[indices_modelo, "score_kmeans"] = scores
    df_resultado.loc[indices_modelo, "anomalia_kmeans"] = anomalias

    return df_resultado


def exibir_resultados(df_resultado, limite_anomalia):
    usados = int(df_resultado["utilizado_kmeans"].sum())
    quantidade_anomalias = int(df_resultado["anomalia_kmeans"].sum())

    print("\nResultados do KMeans:")
    print("Registros utilizados pelo modelo:", usados)
    print("Quantidade de possiveis anomalias:", quantidade_anomalias)
    print(f"Limite de score para anomalia: {limite_anomalia:.4f}")

    print("\nDistribuicao dos clusters:")
    print(
        df_resultado.loc[df_resultado["utilizado_kmeans"], "cluster_kmeans"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    colunas_amostra = [
        "Revenda",
        "CNPJ da Revenda",
        "Bairro",
        "Produto",
        "Data da Coleta",
        "Valor de Venda",
        "cluster_kmeans",
        "score_kmeans",
        "anomalia_kmeans",
    ]
    colunas_amostra = [c for c in colunas_amostra if c in df_resultado.columns]

    print("\nRegistros com maior distancia ao centroide:")
    amostra = (
        df_resultado.loc[df_resultado["utilizado_kmeans"], colunas_amostra]
        .sort_values("score_kmeans", ascending=False)
        .head(10)
    )
    print(amostra.to_string(index=False))


def main():
    df = carregar_dados()
    features = validar_colunas(df, FEATURES_ANOMALIA)
    df_modelo, mascara_apta = selecionar_registros_aptos(df, features)

    imprimir_resumo_base(df, df_modelo, mascara_apta, features)

    x_scaled, _ = padronizar_features(df_modelo, features)
    _, clusters, scores, anomalias, limite_anomalia = executar_kmeans(x_scaled)

    df_resultado = aplicar_resultados(
        df,
        df_modelo.index,
        clusters,
        scores,
        anomalias,
    )

    exibir_resultados(df_resultado, limite_anomalia)
    quantidade_anomalias = int(df_resultado["anomalia_kmeans"].sum())
    caminho_txt = salvar_numero_txt(quantidade_anomalias, "anomalias_kmeans.txt")
    caminho = salvar_resultados(df_resultado, "resultado_kmeans.csv")
    print(f"Arquivo TXT gerado: {caminho_txt}")
    print(f"\nArquivo gerado: {caminho}")


if __name__ == "__main__":
    main()
