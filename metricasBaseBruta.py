import pandas as pd

# Lê a base limpa usando o mesmo separador e formato decimal da exportação.
df = pd.read_csv("base_limpa_aracaju.csv", sep=";", decimal=",")

# Imprime a quantidade de registros.
print("Quantidade de registros: ", len(df))

# Imprime a quantidade de postos sem repetir os nomes das revendas.
print("Quantidade dos postos de Gasolina ", len(df["Revenda"].unique()))

# Imprime os nomes dos postos sem repetições.
print("Postos de Gasolina ", df["Revenda"].unique())

# Imprime os produtos disponíveis sem repetições.
print(df["Produto"].unique())

# Converte as datas para calcular o período de coleta.

df["Data da Coleta"] = pd.to_datetime(
    df["Data da Coleta"],
    dayfirst=True,
    errors="coerce"
)

# Imprime a primeira e a última data de coleta encontradas.
print("Data Inicial da Coleta:", df["Data da Coleta"].min().strftime("%d/%m/%Y"))
print("Data Final da Coleta:", df["Data da Coleta"].max().strftime("%d/%m/%Y"))
