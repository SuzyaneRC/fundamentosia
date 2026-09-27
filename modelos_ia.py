from pathlib import Path

import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


ARQUIVO_ENTRADA = Path("dados_aracaju_processados.csv")
ARQUIVO_SAIDA = Path("dados_modelos_ia.csv")

FEATURES = [
    "Valor de Venda",
    "variacao_percentual",
    "diff_mediana_historica_posto",
    "diff_mediana_municipal_percentual",
]

CONTAMINACOES = [
    0.01,
    0.03,
    0.05,
    0.10,
]

CONTAMINACAO_INICIAL = 0.05
RANDOM_STATE = 42
N_ESTIMATORS = 100


def carregar_dados(caminho=ARQUIVO_ENTRADA):
    return pd.read_csv(
        caminho,
        sep=";",
        decimal=",",
        encoding="utf-8-sig",
        dtype={"CNPJ da Revenda": "string"},
    )


def validar_features(df, features=FEATURES):
    faltantes = [feature for feature in features if feature not in df.columns]
    if faltantes:
        raise ValueError(
            "As seguintes features nao foram encontradas na base: "
            + ", ".join(faltantes)
        )
    return list(features)


def normalizar_coluna_booleana(serie):
    if pd.api.types.is_bool_dtype(serie):
        return serie.fillna(False)

    texto = serie.astype("string").str.strip().str.lower()
    return texto.isin(["true", "1", "sim", "s", "yes"])


def preparar_dados_modelo(df, features):
    df_modelo = df.copy()
    mascara_apta = pd.Series(True, index=df_modelo.index)

    if "poucos_registros" in df_modelo.columns:
        poucos_registros = normalizar_coluna_booleana(df_modelo["poucos_registros"])
        mascara_apta &= ~poucos_registros

    mascara_apta &= ~df_modelo[features].isna().any(axis=1)

    return df_modelo.loc[mascara_apta, features].copy(), mascara_apta


def padronizar_features(df_modelo, features):
    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(df_modelo[features])
    return x_scaled, scaler


def executar_isolation_forest(
    x_scaled,
    contamination=CONTAMINACAO_INICIAL,
    n_estimators=N_ESTIMATORS,
    random_state=RANDOM_STATE,
):
    modelo = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=random_state,
    )
    predicoes = modelo.fit_predict(x_scaled)

    # score_samples retorna valores maiores para pontos mais normais.
    # O sinal negativo inverte a escala: quanto maior, maior o grau de anomalia.
    scores = -modelo.score_samples(x_scaled)
    anomalias = predicoes == -1

    return modelo, anomalias, scores


def testar_contaminacoes(x_scaled, contaminacoes=CONTAMINACOES):
    resultados = {}

    for contamination in contaminacoes:
        _, anomalias, _ = executar_isolation_forest(
            x_scaled,
            contamination=contamination,
        )
        resultados[contamination] = int(anomalias.sum())

    return resultados


def aplicar_resultados_isolation(df_original, indices_modelo, anomalias, scores):
    df_resultado = df_original.copy()
    df_resultado["utilizado_modelo_ia"] = False
    df_resultado["anomalia_isolation"] = False
    df_resultado["score_isolation"] = float("nan")

    df_resultado.loc[indices_modelo, "utilizado_modelo_ia"] = True
    df_resultado.loc[indices_modelo, "anomalia_isolation"] = anomalias
    df_resultado.loc[indices_modelo, "score_isolation"] = scores

    return df_resultado


def preparar_estrutura_kmeans():
    """
    Estrutura planejada para etapa futura com K-Means:
    1. reutilizar as features numericas selecionadas;
    2. aplicar StandardScaler;
    3. executar KMeans, inicialmente com n_clusters=3 apenas para teste;
    4. registrar o cluster de cada registro;
    5. calcular a distancia do registro ao centroide do seu cluster;
    6. usar essa distancia como score experimental de anomalia.
    """
    return {
        "modelo": "KMeans",
        "n_clusters_inicial": 3,
        "score_planejado": "distancia_ao_centroide",
    }


def preparar_estrutura_random_forest():
    """
    Estrutura planejada para etapa futura com RandomForestRegressor.
    O alvo sera Valor de Venda, que nao deve entrar nas features X.
    Variaveis categoricas como Produto, Bairro e Bandeira precisarao de
    transformacao antes do treinamento.
    """
    features_base = [feature for feature in FEATURES if feature != "Valor de Venda"]
    return {
        "modelo": "RandomForestRegressor",
        "target": "Valor de Venda",
        "features_numericas_iniciais": features_base,
        "score_planejado": "erro_absoluto_previsao",
    }


def preparar_estrutura_comparacao():
    return {
        "metodos": [
            "baseline_regressao",
            "isolation_forest",
            "kmeans",
            "random_forest_regressor",
        ],
        "criterios": [
            "registros_sinalizados",
            "concordancia_entre_metodos",
            "score_de_anomalia",
            "inspecao_manual",
        ],
    }


def exibir_analise_inicial(df, df_modelo, mascara_apta, features):
    print("Colunas encontradas:")
    print(", ".join(df.columns))
    print("\nTipos das colunas:")
    print(df.dtypes.to_string())
    print("\nValores ausentes nas features selecionadas:")
    print(df[features].isna().sum().to_string())

    if "poucos_registros" in df.columns:
        print("\nDistribuicao de poucos_registros:")
        print(df["poucos_registros"].value_counts(dropna=False).to_string())

    print("\nResumo da base para modelagem:")
    print("Quantidade total de registros:", len(df))
    print("Quantidade de registros aptos para o modelo:", len(df_modelo))
    print("Quantidade de registros removidos da analise:", int((~mascara_apta).sum()))


def exibir_resultados(df_resultado, resultados_contaminacao):
    total = len(df_resultado)
    usados = int(df_resultado["utilizado_modelo_ia"].sum())
    nao_usados = total - usados
    quantidade_anomalias = int(df_resultado["anomalia_isolation"].sum())
    percentual_anomalias = (quantidade_anomalias / usados * 100) if usados else 0

    print("\nResultados do Isolation Forest:")
    print("Total de registros da base:", total)
    print("Registros utilizados pelo modelo:", usados)
    print("Registros nao utilizados:", nao_usados)
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
        "variacao_percentual",
        "diff_mediana_historica_posto",
        "diff_mediana_municipal_percentual",
        "score_isolation",
        "anomalia_isolation",
    ]
    colunas_amostra = [coluna for coluna in colunas_amostra if coluna in df_resultado.columns]

    print("\nRegistros com maior score de anomalia:")
    amostra = (
        df_resultado.loc[df_resultado["utilizado_modelo_ia"], colunas_amostra]
        .sort_values("score_isolation", ascending=False)
        .head(10)
    )
    print(amostra.to_string(index=False))


def salvar_resultados(df_resultado, caminho=ARQUIVO_SAIDA):
    df_resultado.to_csv(
        caminho,
        index=False,
        encoding="utf-8-sig",
        sep=";",
        decimal=",",
    )


def main():
    df = carregar_dados()
    features = validar_features(df)
    df_modelo, mascara_apta = preparar_dados_modelo(df, features)

    exibir_analise_inicial(df, df_modelo, mascara_apta, features)

    x_scaled, _ = padronizar_features(df_modelo, features)
    _, anomalias, scores = executar_isolation_forest(x_scaled)
    resultados_contaminacao = testar_contaminacoes(x_scaled)

    df_resultado = aplicar_resultados_isolation(
        df,
        df_modelo.index,
        anomalias,
        scores,
    )

    preparar_estrutura_kmeans()
    preparar_estrutura_random_forest()
    preparar_estrutura_comparacao()

    exibir_resultados(df_resultado, resultados_contaminacao)
    salvar_resultados(df_resultado)
    print(f"\nArquivo gerado: {ARQUIVO_SAIDA}")


if __name__ == "__main__":
    main()
