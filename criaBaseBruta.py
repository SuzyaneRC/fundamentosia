from pathlib import Path
import pandas as pd

CAMINHO = Path("planilhas")
ARQUIVOS = CAMINHO.glob("*.csv")

lista = []

for arq in ARQUIVOS:
    df = pd.read_csv(arq, encoding="utf-8", sep=";")
    lista.append(df)

dadosConcatenados = pd.concat(lista, ignore_index=True)

dadosAracaju = dadosConcatenados[
    (dadosConcatenados["Estado - Sigla"] == "SE") &
    (dadosConcatenados["Municipio"] == "ARACAJU")
]

dadosAracaju.to_csv(
    "base_bruta_aracaju.csv",
    index=False,
    encoding="utf-8-sig"
)