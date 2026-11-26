from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split


#Obtem o arquivo com os dados ja processados pelo pipeline, define a semente como 42 e define as métricas da
# divisao de cada subset.
PASTA_RAIZ = Path(__file__).resolve().parent

ARQUIVO_DADOS = PASTA_RAIZ / "dados_aracaju_processados.csv"

PASTA_SAIDA = PASTA_RAIZ / "experimentos" / "subsets"
PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

SEMENTE = 42

EXPERIMENTOS = {
    "70_30": 0.30,
    "75_25": 0.25,
    "80_20": 0.20,
}


#obtem as variaveis que ja sao utilizadas no projeto, para serem utilizadas

TARGET = "Valor de Venda"

VARIAVEIS_NUMERICAS = [
    "preco_anterior",
    "media_historica_posto",
    "mediana_historica_posto",
    "mediana_municipal",
]

VARIAVEIS_CATEGORICAS = [
    "Produto",
    "Bairro",
    "Bandeira",
]

FEATURES = VARIAVEIS_NUMERICAS + VARIAVEIS_CATEGORICAS

COLUNAS_OBRIGATORIAS = [
    "CNPJ da Revenda",
    "Produto",
    "Bairro",
    "Bandeira",
    "Data da Coleta",
    TARGET,
]


#obtem a base e adiciona as colunas que estao faltantes em relação a base anterior
#adiciona um identificador para cada registro da base, para facilitar a comparação entre as bases divididas
def carregar_base():

    if not ARQUIVO_DADOS.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {ARQUIVO_DADOS}\n"
            "Execute primeiro o pipeline do projeto."
        )

    df = pd.read_csv(
        ARQUIVO_DADOS,
        sep=";",
        decimal=",",
        encoding="utf-8-sig",
        dtype={"CNPJ da Revenda": "string"},
    )

    faltantes = [
        coluna for coluna in COLUNAS_OBRIGATORIAS
        if coluna not in df.columns
    ]

    if faltantes:
        raise ValueError(
            f"Colunas obrigatórias ausentes: {faltantes}"
        )

#
    df = df.reset_index(drop=True)
    df.insert(0, "id_registro", np.arange(len(df)))

    df[TARGET] = pd.to_numeric(
        df[TARGET],
        errors="coerce"
    )

    df["Data da Coleta"] = pd.to_datetime(
        df["Data da Coleta"],
        dayfirst=True,
        errors="coerce"
    )

    # Reproduz a regra de exclusão de séries curtas ja usada no projeto.
    if "poucos_registros" in df.columns:

        coluna = df["poucos_registros"]

        if pd.api.types.is_bool_dtype(coluna):
            poucos = coluna.fillna(False)
        else:
            poucos = (
                coluna.astype("string")
                .str.strip()
                .str.lower()
                .isin(["true", "1", "sim", "yes"])
            )

    else:
        contagem = df.groupby(
            ["CNPJ da Revenda", "Produto"]
        )[TARGET].transform("count")

        poucos = contagem < 3

    mascara = (
        ~poucos
        & df[COLUNAS_OBRIGATORIAS].notna().all(axis=1)
    )

    df_apto = df.loc[mascara].copy()

    if df_apto.empty:
        raise ValueError("Nenhum registro válido para os experimentos.")

    if df_apto["id_registro"].duplicated().any():
        raise AssertionError("Existem registros com os mesmos identificadores .")

    return df_apto.reset_index(drop=True), len(df)



def gerar_features_sem_vazamento(alvo, referencia):

    resultado = alvo.copy()

    resultado["preco_anterior"] = np.nan
    resultado["media_historica_posto"] = np.nan
    resultado["mediana_historica_posto"] = np.nan
    resultado["mediana_municipal"] = np.nan

# Índice de históricos por posto e produto.
    historicos = {
        chave: grupo
        for chave, grupo in referencia.groupby(
            ["CNPJ da Revenda", "Produto"],
            sort=False
        )
    }

    # Índice de preços municipais por produto e data.
    municipais = {
        chave: grupo
        for chave, grupo in referencia.groupby(
            ["Produto", "Data da Coleta"],
            sort=False
        )
    }

    for indice, linha in resultado.iterrows():

        cnpj = linha["CNPJ da Revenda"]
        produto = linha["Produto"]
        data = linha["Data da Coleta"]

        # Histórico do mesmo posto e produto.
        grupo = historicos.get((cnpj, produto))

        if grupo is not None:

            anteriores = grupo.loc[
                grupo["Data da Coleta"] < data,
                TARGET
            ].dropna()

            if not anteriores.empty:

                resultado.at[
                    indice, "preco_anterior"
                ] = anteriores.iloc[-1]

                resultado.at[
                    indice, "media_historica_posto"
                ] = anteriores.mean()

                resultado.at[
                    indice, "mediana_historica_posto"
                ] = anteriores.median()

        # Referência de outros postos da cidade para o mesmo produto e mesma data
        grupo_municipal = municipais.get((produto, data))

        if grupo_municipal is not None:

            outros_postos = grupo_municipal.loc[
                grupo_municipal["CNPJ da Revenda"] != cnpj,
                TARGET
            ].dropna()

            if not outros_postos.empty:

                resultado.at[
                    indice, "mediana_municipal"
                ] = outros_postos.median()

    return resultado


def validar_divisao(treino, teste, total, nome):

    ids_treino = set(treino["id_registro"])
    ids_teste = set(teste["id_registro"])

# avalia que um registro não pode estar nos dois conjuntos, e que todos os registros aptos devem estar representados.

    assert ids_treino.isdisjoint(ids_teste)

    assert len(treino) + len(teste) == total

    assert len(ids_treino) == len(treino)
    assert len(ids_teste) == len(teste)

    assert TARGET not in FEATURES

    for coluna in FEATURES + [TARGET]:
        assert coluna in treino.columns
        assert coluna in teste.columns

    return {
        "experimento": nome,
        "total": total,
        "n_treino": len(treino),
        "n_teste": len(teste),
        "sobreposicao_ids": len(ids_treino & ids_teste),
        "ids_unicos": True,
        "cobertura_completa": True,
        "alvo_fora_de_X": True,
        "cnpjs_presentes_nos_dois": len(
            set(treino["CNPJ da Revenda"])
            & set(teste["CNPJ da Revenda"])
        ),
        "datas_presentes_nos_dois": len(
            set(treino["Data da Coleta"])
            & set(teste["Data da Coleta"])
        ),
        "n_treino_features_completas": int(
            treino[FEATURES].notna().all(axis=1).sum()
        ),
        "n_teste_features_completas": int(
            teste[FEATURES].notna().all(axis=1).sum()
        ),
        "n_treino_features_com_faltantes": int(
            treino[FEATURES].isna().any(axis=1).sum()
        ),
        "n_teste_features_com_faltantes": int(
            teste[FEATURES].isna().any(axis=1).sum()
        ),
    }


#salva os arquivos csv
def salvar_csv(df, caminho):

    df.to_csv(
        caminho,
        index=False,
        sep=";",
        decimal=",",
        encoding="utf-8-sig",
    )



def executar_experimentos():

    df, total_original = carregar_base()

    total_apto = len(df)

    print("\nBASE CARREGADA")
    print("Registros originais:", total_original)
    print("Registros aptos:", total_apto)
    print("Registros excluídos:", total_original - total_apto)

    relatorio = []
    validacoes = []
    indices = []

    for nome, percentual_teste in EXPERIMENTOS.items():

        print(f"\nExecutando experimento {nome}...")

        ids_treino, ids_teste = train_test_split(
            df["id_registro"].to_numpy(),
            test_size=percentual_teste,
            random_state=SEMENTE,
            shuffle=True,
        )

        treino = (
            df.loc[df["id_registro"].isin(ids_treino)]
            .copy()
            .sort_values("id_registro")
        )

        teste = (
            df.loc[df["id_registro"].isin(ids_teste)]
            .copy()
            .sort_values("id_registro")
        )


        treino = gerar_features_sem_vazamento(
            treino,
            treino
        )

        teste = gerar_features_sem_vazamento(
            teste,
            treino
        )

        resultado_validacao = validar_divisao(
            treino,
            teste,
            total_apto,
            nome
        )

        validacoes.append(resultado_validacao)

        salvar_csv(
            treino,
            PASTA_SAIDA / f"treino_{nome}.csv"
        )

        salvar_csv(
            teste,
            PASTA_SAIDA / f"teste_{nome}.csv"
        )

        for identificador in ids_treino:

            indices.append({
                "experimento": nome,
                "id_registro": identificador,
                "divisao": "treino",
                "semente": SEMENTE,
            })

        for identificador in ids_teste:

            indices.append({
                "experimento": nome,
                "id_registro": identificador,
                "divisao": "teste",
                "semente": SEMENTE,
            })

        relatorio.append({
            "experimento": nome,
            "percentual_treino": 1 - percentual_teste,
            "percentual_teste": percentual_teste,
            "n_treino": len(treino),
            "n_teste": len(teste),
            "total": total_apto,
            "semente": SEMENTE,
            "random_state": SEMENTE,
        })

        print("Treinamento:", len(treino))
        print("Teste:", len(teste))
        print("Sobreposição:", resultado_validacao["sobreposicao_ids"])

    
    #salva os documentos finais
    salvar_csv(
        pd.DataFrame(relatorio),
        PASTA_SAIDA / "relatorio_divisoes.csv"
    )

    salvar_csv(
        pd.DataFrame(validacoes),
        PASTA_SAIDA / "validacao_conjuntos.csv"
    )

    salvar_csv(
        pd.DataFrame(indices),
        PASTA_SAIDA / "indices_divisoes.csv"
    )
    
if __name__ == "__main__":
    executar_experimentos()

    print("\n" + "=" * 50)
    print("EXPERIMENTOS CONCLUÍDOS!")
    print("=" * 50)

    print("\nArquivos salvos em:", PASTA_SAIDA)
