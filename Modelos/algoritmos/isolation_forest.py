from sklearn.ensemble import IsolationForest

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


CONTAMINACOES_TESTE = [0.01, 0.03, 0.05, 0.10]
CONTAMINACAO = 0.05
N_ESTIMATORS = 100
RANDOM_STATE = 42


def executar_isolation_forest(x_scaled, contamination=CONTAMINACAO):
    modelo = IsolationForest(
        n_estimators=N_ESTIMATORS,
        contamination=contamination,
        random_state=RANDOM_STATE,
    )
    predicoes = modelo.fit_predict(x_scaled)
    scores = -modelo.score_samples(x_scaled)
    anomalias = predicoes == -1
    return modelo, anomalias, scores


def testar_contaminacoes(x_scaled):
    resultados = {}

    for contamination in CONTAMINACOES_TESTE:
        _, anomalias, _ = executar_isolation_forest(
            x_scaled,
            contamination=contamination,
        )
        resultados[contamination] = int(anomalias.sum())

    return resultados


def aplicar_resultados(df_original, indices_modelo, anomalias, scores):
    df_resultado = df_original.copy()
    df_resultado["utilizado_isolation_forest"] = False
    df_resultado["anomalia_isolation_forest"] = False
    df_resultado["score_isolation_forest"] = float("nan")

    df_resultado.loc[indices_modelo, "utilizado_isolation_forest"] = True
    df_resultado.loc[indices_modelo, "anomalia_isolation_forest"] = anomalias
    df_resultado.loc[indices_modelo, "score_isolation_forest"] = scores

    return df_resultado


def exibir_resultados(df_resultado, resultados_contaminacao):
    usados = int(df_resultado["utilizado_isolation_forest"].sum())
    quantidade_anomalias = int(df_resultado["anomalia_isolation_forest"].sum())
    percentual_anomalias = (quantidade_anomalias / usados * 100) if usados else 0

    print("\nResultados do Isolation Forest:")
    print("Registros utilizados pelo modelo:", usados)
    print("Quantidade de possiveis anomalias:", quantidade_anomalias)
    print(f"Percentual de possiveis anomalias: {percentual_anomalias:.2f}%")

    print("\nTestes por contamination:")
    for contamination, quantidade in resultados_contaminacao.items():
        print(f"contamination={contamination:.2f}: {quantidade} registros sinalizados")

    colunas_amostra = [
        "Revenda",
        "CNPJ da Revenda",
        "Bairro",
        "Produto",
        "Data da Coleta",
        "Valor de Venda",
        "score_isolation_forest",
        "anomalia_isolation_forest",
    ]
    colunas_amostra = [c for c in colunas_amostra if c in df_resultado.columns]

    print("\nRegistros com maior score de anomalia:")
    amostra = (
        df_resultado.loc[df_resultado["utilizado_isolation_forest"], colunas_amostra]
        .sort_values("score_isolation_forest", ascending=False)
        .head(10)
    )
    print(amostra.to_string(index=False))


def main():
    from modelos_produto import aplicar_por_produto
    df_resultado, limites, contaminacoes = aplicar_por_produto(carregar_dados())
    print("Modelos e padroniza??o separados por combust?vel.")
    print("Limites K-Means:", limites)
    print("Testes de contamina??o por produto:", contaminacoes)
    quantidade_anomalias = int(df_resultado["anomalia_isolation_forest"].sum())
    caminho_txt = salvar_numero_txt(
        quantidade_anomalias,
        "anomalias_isolation_forest.txt",
    )
    caminho = salvar_resultados(df_resultado, "resultado_isolation_forest.csv")
    print(f"Arquivo TXT gerado: {caminho_txt}")
    print(f"\nArquivo gerado: {caminho}")


if __name__ == "__main__":
    main()
