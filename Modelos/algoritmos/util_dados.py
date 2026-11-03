"""Funções e caminhos compartilhados pelos modelos: leitura, seleção e gravação de dados."""
from pathlib import Path

import pandas as pd
from sklearn.preprocessing import StandardScaler


RAIZ_PROJETO = Path(__file__).resolve().parents[2]
PASTA_MODELOS = Path(__file__).resolve().parents[1]
PASTA_SAIDAS = PASTA_MODELOS / "Saídas"
ARQUIVO_ENTRADA = RAIZ_PROJETO / "dados_aracaju_processados.csv"

# Variáveis de entrada do Isolation Forest e do K-Means. Juntas, descrevem o nível do
# preço e sua distância para a coleta anterior, o histórico do posto e os outros postos.
FEATURES_ANOMALIA = [
    "Valor de Venda",
    "variacao_percentual",
    "diff_mediana_historica_posto",
    "diff_mediana_municipal_percentual",
]


def carregar_dados(caminho=ARQUIVO_ENTRADA):
    """Lê a base processada, mantendo o CNPJ como texto para preservar zeros à esquerda."""
    return pd.read_csv(
        caminho,
        sep=";",
        decimal=",",
        encoding="utf-8-sig",
        dtype={"CNPJ da Revenda": "string"},
    )


def salvar_resultados(df, nome_arquivo):
    """Grava `df` em `Modelos/Saídas` no padrão brasileiro e devolve o caminho."""
    PASTA_SAIDAS.mkdir(parents=True, exist_ok=True)
    caminho = PASTA_SAIDAS / nome_arquivo
    df.to_csv(
        caminho,
        index=False,
        encoding="utf-8-sig",
        sep=";",
        decimal=",",
    )
    return caminho


def salvar_numero_txt(numero, nome_arquivo):
    """Grava um número em um arquivo de texto de `Modelos/Saídas` e devolve o caminho."""
    PASTA_SAIDAS.mkdir(parents=True, exist_ok=True)
    caminho = PASTA_SAIDAS / nome_arquivo
    caminho.write_text(f"{numero}\n", encoding="utf-8")
    return caminho


def validar_colunas(df, colunas):
    """Interrompe com uma mensagem clara se faltar alguma coluna; senão, devolve a lista."""
    faltantes = [coluna for coluna in colunas if coluna not in df.columns]
    if faltantes:
        raise ValueError(
            "As seguintes colunas nao foram encontradas na base: "
            + ", ".join(faltantes)
        )
    return list(colunas)


def normalizar_coluna_booleana(serie):
    """Converte uma coluna em booleano; lida com valores como "True" ou "sim" lidos de CSV."""
    if pd.api.types.is_bool_dtype(serie):
        return serie.fillna(False)

    texto = serie.astype("string").str.strip().str.lower()
    return texto.isin(["true", "1", "sim", "s", "yes"])


def selecionar_registros_aptos(df, colunas_obrigatorias):
    """Separa os registros que um modelo pode usar.

    Exclui séries curtas e linhas com valor vazio em alguma coluna obrigatória. Devolve
    os registros aptos, com os índices originais, e a máscara True/False sobre `df`. Os
    índices preservados permitem gravar os resultados de volta nas linhas certas.
    """
    df_modelo = df.copy()
    mascara_apta = pd.Series(True, index=df_modelo.index)

    if "poucos_registros" in df_modelo.columns:
        poucos_registros = normalizar_coluna_booleana(df_modelo["poucos_registros"])
        mascara_apta &= ~poucos_registros

    mascara_apta &= ~df_modelo[colunas_obrigatorias].isna().any(axis=1)
    return df_modelo.loc[mascara_apta].copy(), mascara_apta


def padronizar_features(df_modelo, features):
    """Deixa cada variável com média 0 e desvio 1, para que nenhuma domine pela escala."""
    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(df_modelo[features])
    return x_scaled, scaler


def imprimir_resumo_base(df, df_modelo, mascara_apta, features):
    """Imprime quantos registros ficaram aptos e quantos valores faltam por variável."""
    print("Resumo da base para modelagem:")
    print("Quantidade total de registros:", len(df))
    print("Quantidade de registros aptos para o modelo:", len(df_modelo))
    print("Quantidade de registros removidos da analise:", int((~mascara_apta).sum()))

    print("\nValores ausentes nas features selecionadas:")
    print(df[features].isna().sum().to_string())
