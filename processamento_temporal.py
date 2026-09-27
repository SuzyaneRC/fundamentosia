from pathlib import Path
import pandas as pd

# Limite mínimo de observações para considerar o histórico de um posto+produto
# estatisticamente confiável. Não é usado para remover dados, apenas para
# marcar a coluna 'poucos_registros'.
MINIMO_REGISTROS_CONFIAVEL = 3


def processar_variaveis_temporais(df, minimo_registros_confiavel=MINIMO_REGISTROS_CONFIAVEL):
    # Recebe o DataFrame já limpo e devolve o mesmo DataFrame com as 
    # variáveis temporais e de histórico adicionadas.
    # Apenas adiciona colunas.
    
    df = df.copy()
    df["Data da Coleta"] = pd.to_datetime(df["Data da Coleta"], dayfirst=True, errors="coerce")
    df["CNPJ da Revenda"] = df["CNPJ da Revenda"].astype("string")

    df = _ordenar_por_posto_produto_data(df)
    df = _calcular_variacoes_temporais(df)
    df = _calcular_historico_posto(df)
    df = _calcular_mediana_municipal(df)
    df = _marcar_series_curtas(df, minimo_registros_confiavel)

    return df


def _ordenar_por_posto_produto_data(df):
    # Ordena cada série (posto + produto) cronologicamente
    return df.sort_values(["CNPJ da Revenda", "Produto", "Data da Coleta"]).reset_index(drop=True)


def _calcular_variacoes_temporais(df):
    # Agrupa por posto+produto para comparar cada preço só com o histórico dele mesmo
    grupo = df.groupby(["CNPJ da Revenda", "Produto"], sort=False)["Valor de Venda"]
    df["preco_anterior"] = grupo.shift(1)
    df["variacao_absoluta"] = df["Valor de Venda"] - df["preco_anterior"]
    df["variacao_percentual"] = (df["variacao_absoluta"] / df["preco_anterior"]) * 100
    return df


def _calcular_historico_posto(df):
    grupo = df.groupby(["CNPJ da Revenda", "Produto"], sort=False)["Valor de Venda"]

     # Média/mediana histórica do posto até o registro anterior
    df["media_historica_posto"] = grupo.transform(lambda s: s.expanding().mean().shift(1))
    df["mediana_historica_posto"] = grupo.transform(lambda s: s.expanding().median().shift(1))

     # Diferença do preço atual em relação ao histórico do próprio posto
    df["diff_historico_posto"] = df["Valor de Venda"] - df["mediana_historica_posto"]
    return df


def _calcular_mediana_municipal(df):
    # Agrupa por produto + data (período = data exata de coleta)
    # para comparar cada posto com os outros postos de Aracaju no mesmo dia/produto
    grupo = df.groupby(["Produto", "Data da Coleta"])["Valor de Venda"]
    df["mediana_municipal"] = grupo.transform("median")

    # Quanto o preço do posto se distancia do "normal" do município naquele dia
    df["diff_mediana_municipal"] = df["Valor de Venda"] - df["mediana_municipal"]
    df["diff_mediana_municipal_percentual"] = (
        df["diff_mediana_municipal"] / df["mediana_municipal"]
    ) * 100
    return df


def _marcar_series_curtas(df, minimo):
    # Marca (sem remover) posto+produto com poucas observações no total
    contagem = df.groupby(["CNPJ da Revenda", "Produto"])["Valor de Venda"].transform("count")
    df["total_registros_serie"] = contagem
    df["poucos_registros"] = contagem < minimo
    return df


def _imprimir_resumo(df, minimo):
    total_series = df.groupby(["CNPJ da Revenda", "Produto"]).ngroups
    series_curtas = df.loc[df["poucos_registros"], ["CNPJ da Revenda", "Produto"]].drop_duplicates()
    print("Quantidade de registros:", len(df))
    print("Quantidade de séries (posto + produto):", total_series)
    print(f"Séries com menos de {minimo} registros:", len(series_curtas))
    print("Registros sem preço anterior (primeira coleta da série):", df["preco_anterior"].isna().sum())


def _rodar_isolado():
    # Uso apenas para depuração local desta etapa: lê a base limpa do disco,
    # processa e salva um CSV de conferência. 
    caminho_entrada = Path("base_limpa_aracaju.csv")
    caminho_saida = Path("dados_aracaju_processados.csv")

    df = pd.read_csv(
        caminho_entrada,
        sep=";",
        decimal=",",
        encoding="utf-8-sig",
        dtype={"CNPJ da Revenda": "string"},
    )
    df_processado = processar_variaveis_temporais(df)
    _imprimir_resumo(df_processado, MINIMO_REGISTROS_CONFIAVEL)

    df_processado.to_csv(
        caminho_saida,
        index=False,
        encoding="utf-8-sig",
        sep=";",
        decimal=",",
        date_format="%d/%m/%Y",
    )
    print(f"[depuração] Base processada salva em {caminho_saida}")


if __name__ == "__main__":
    _rodar_isolado()
