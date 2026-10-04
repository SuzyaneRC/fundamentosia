from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from util_dados import (
    carregar_dados,
    salvar_numero_txt,
    salvar_resultados,
    selecionar_registros_aptos,
    validar_colunas,
)


TARGET = "Valor de Venda"
FEATURES_NUMERICAS = [
    "preco_anterior",
    "media_historica_posto",
    "mediana_historica_posto",
    "mediana_municipal",
]
FEATURES_CATEGORICAS = ["Produto", "Bairro", "Bandeira"]
COLUNAS_MODELO = FEATURES_NUMERICAS + FEATURES_CATEGORICAS + [TARGET]
PERCENTIL_ANOMALIA = 0.95
RANDOM_STATE = 42


def criar_pipeline():
    pre_processador = ColumnTransformer(
        transformers=[
            ("categoricas", OneHotEncoder(handle_unknown="ignore"), FEATURES_CATEGORICAS),
            ("numericas", "passthrough", FEATURES_NUMERICAS),
        ]
    )

    return Pipeline(
        steps=[
            ("pre_processador", pre_processador),
            (
                "modelo",
                RandomForestRegressor(
                    n_estimators=200,
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
                ),
            ),
        ]
    )


def executar_random_forest(df_modelo):
    from avaliacao_temporal import avaliar_janelas
    return avaliar_janelas(
        df_modelo, FEATURES_NUMERICAS + FEATURES_CATEGORICAS,
        TARGET, criar_pipeline, PERCENTIL_ANOMALIA,
    )


def aplicar_resultados(df_original, indices_modelo, predicoes, erros, anomalias):
    df_resultado = df_original.copy()
    df_resultado["utilizado_random_forest"] = False
    df_resultado["previsao_random_forest"] = float("nan")
    df_resultado["erro_abs_random_forest"] = float("nan")
    df_resultado["anomalia_random_forest"] = False

    df_resultado.loc[indices_modelo, "utilizado_random_forest"] = True
    df_resultado.loc[indices_modelo, "previsao_random_forest"] = predicoes
    df_resultado.loc[indices_modelo, "erro_abs_random_forest"] = erros
    df_resultado.loc[indices_modelo, "anomalia_random_forest"] = anomalias

    return df_resultado


def exibir_resultados(df_resultado, limite_anomalia, metricas):
    usados = int(df_resultado["utilizado_random_forest"].sum())
    quantidade_anomalias = int(df_resultado["anomalia_random_forest"].sum())

    print("\nResultados do Random Forest:")
    print("Registros utilizados pelo modelo:", usados)
    print("Quantidade de possiveis anomalias:", quantidade_anomalias)
    print("Janelas temporais avaliadas:", len(metricas["janelas"]))

    print("\nMetricas no conjunto de teste:")
    print(f"MAE: {metricas['mae']:.4f}")
    print(f"RMSE: {metricas['rmse']:.4f}")
    print("R?:", metricas["r2"])

    colunas_amostra = [
        "Revenda",
        "CNPJ da Revenda",
        "Bairro",
        "Produto",
        "Data da Coleta",
        "Valor de Venda",
        "previsao_random_forest",
        "erro_abs_random_forest",
        "anomalia_random_forest",
    ]
    colunas_amostra = [c for c in colunas_amostra if c in df_resultado.columns]

    print("\nRegistros com maior erro de previsao:")
    amostra = (
        df_resultado.loc[df_resultado["utilizado_random_forest"], colunas_amostra]
        .sort_values("erro_abs_random_forest", ascending=False)
        .head(10)
    )
    print(amostra.to_string(index=False))


def main():
    df = carregar_dados()
    colunas_modelo = validar_colunas(df, COLUNAS_MODELO)
    df_modelo, mascara_apta = selecionar_registros_aptos(df, colunas_modelo)

    print("Resumo da base para modelagem:")
    print("Quantidade total de registros:", len(df))
    print("Quantidade de registros aptos para o modelo:", len(df_modelo))
    print("Quantidade de registros removidos da analise:", int((~mascara_apta).sum()))

    _, predicoes, erros, anomalias, limite_anomalia, metricas, indices_teste = executar_random_forest(
        df_modelo
    )

    df_resultado = aplicar_resultados(
        df,
        indices_teste,
        predicoes,
        erros,
        anomalias,
    )

    df_resultado["limite_erro_random_forest"] = float("nan")
    df_resultado.loc[indices_teste, "limite_erro_random_forest"] = limite_anomalia
    exibir_resultados(df_resultado, limite_anomalia, metricas)
    quantidade_anomalias = int(df_resultado["anomalia_random_forest"].sum())
    caminho_txt = salvar_numero_txt(
        quantidade_anomalias,
        "anomalias_random_forest.txt",
    )
    caminho = salvar_resultados(df_resultado, "resultado_random_forest.csv")
    print(f"Arquivo TXT gerado: {caminho_txt}")
    print(f"\nArquivo gerado: {caminho}")


if __name__ == "__main__":
    main()
