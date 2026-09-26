import pandas as pd
from datetime import datetime

df = pd.read_csv("base_bruta_aracaju.csv")

#Imprime a quantidade de registros
print("Quantidade de registros: ", len(df))

#Imprime a quantidade de postos retirando as duplicatas
print("Quantidade dos postos de Gasolina ", len(df["Revenda"].unique()))

# Imprime os postos retirando as duplicatas
print("Postos de Gasolina ", df["Revenda"].unique())

# Imprime os produtos disponíveis retirando as duplicadas
print(df["Produto"].unique())

#Imprime o Período das coletas, com base na coluna "Data da Coleta"

df["Data da Coleta"] = pd.to_datetime(
    df["Data da Coleta"],
    dayfirst=True,
    errors="coerce"
)

print("Data Inicial da Coleta:", df["Data da Coleta"].min().strftime("%d/%m/%Y"))
print("Data Final da Coleta:", df["Data da Coleta"].max().strftime("%d/%m/%Y"))