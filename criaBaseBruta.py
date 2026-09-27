from pathlib import Path
import re
import unicodedata

import pandas as pd

# Define a pasta de entrada e garante uma ordem determinística para os arquivos.
CAMINHO = Path("planilhas")
ARQUIVOS = sorted(CAMINHO.glob("*.csv"))

# Mantém somente as colunas necessárias para a análise dos preços.
COLUNAS_ANALISE = [
    "Revenda",
    "CNPJ da Revenda",
    "Bairro",
    "Produto",
    "Data da Coleta",
    "Valor de Venda",
    "Bandeira",
]

# Identifica um registro repetido do mesmo posto, produto e data.
CHAVE_REGISTRO = ["CNPJ da Revenda", "Produto", "Data da Coleta"]


def converter_valor(valor):
    # Converte preços em real, como "6,79" ou "R$ 6,79", para número.
    if pd.isna(valor):
        return pd.NA

    texto = str(valor).strip().replace("R$", "").replace(" ", "")
    if not texto:
        return pd.NA

    if "," in texto and "." in texto:
        if texto.rfind(",") > texto.rfind("."):
            texto = texto.replace(".", "").replace(",", ".")
        else:
            texto = texto.replace(",", "")
    else:
        texto = texto.replace(",", ".")

    return pd.to_numeric(texto, errors="coerce")


def padronizar_produto(produto):
    # Uniformiza acentos, espaços e nomes equivalentes dos combustíveis.
    if pd.isna(produto):
        return pd.NA

    texto = unicodedata.normalize("NFKD", str(produto))
    texto = "".join(caractere for caractere in texto if not unicodedata.combining(caractere))
    texto = re.sub(r"\s+", " ", texto).strip().upper()

    equivalencias = {
        "DIESEL B S10": "DIESEL S10",
        "DIESEL S 10": "DIESEL S10",
        "DIESEL S-10": "DIESEL S10",
        "ETANOL HIDRATADO": "ETANOL",
        "GASOLINA COMUM": "GASOLINA",
    }
    return equivalencias.get(texto, texto)


def imprimir_ausentes(dados):
    # Exibe somente as colunas que ainda possuem valores ausentes.
    ausentes = dados.isna().sum()
    ausentes = ausentes[ausentes > 0]
    if ausentes.empty:
        print("Valores ausentes: nenhum")
        return

    print("Valores ausentes por coluna:")
    print(ausentes.to_string())

# Lê as quatro planilhas e armazena cada uma para a concatenação posterior.
lista = []

for arq in ARQUIVOS:
    # Evita inferências de tipo inconsistentes em arquivos grandes.
    df = pd.read_csv(arq, encoding="utf-8", sep=";", low_memory=False)
    lista.append(df)

# Une todas as planilhas em uma única tabela de trabalho.
dadosConcatenados = pd.concat(lista, ignore_index=True)

# Filtra as revendas de Aracaju e seleciona as colunas da análise.
dadosAracaju = dadosConcatenados[
    (dadosConcatenados["Estado - Sigla"] == "SE") &
    (dadosConcatenados["Municipio"] == "ARACAJU")
][COLUNAS_ANALISE].copy()

# Registra a quantidade de linhas antes da limpeza para comparação posterior.
quantidade_antes = len(dadosAracaju)

# Remove espaços, pontos, barras e hífens dos CNPJs.
dadosAracaju["CNPJ da Revenda"] = (
    dadosAracaju["CNPJ da Revenda"]
    .astype("string")
    .str.replace(r"\D", "", regex=True)
)

# Padroniza os nomes dos produtos e transforma as datas em valores comparáveis.
dadosAracaju["Produto"] = dadosAracaju["Produto"].map(padronizar_produto)
dadosAracaju["Data da Coleta"] = pd.to_datetime(
    dadosAracaju["Data da Coleta"],
    dayfirst=True,
    errors="coerce",
)

# Converte os preços para números antes de verificar valores inválidos.
dadosAracaju["Valor de Venda"] = dadosAracaju["Valor de Venda"].map(converter_valor)

# Informa a quantidade inicial e os valores ausentes encontrados.
print("Quantidade de registros antes da limpeza:", quantidade_antes)
imprimir_ausentes(dadosAracaju)

# Marca preços ausentes, iguais a zero ou menores que zero para remoção.
precos_invalidos = (
    dadosAracaju["Valor de Venda"].isna() |
    (dadosAracaju["Valor de Venda"] <= 0)
)
print("Preços nulos, iguais a zero ou negativos removidos:", precos_invalidos.sum())
dadosAracaju = dadosAracaju.loc[~precos_invalidos].copy()

# Remove linhas completamente duplicadas.
duplicados = dadosAracaju.duplicated(keep="first")
print("Registros duplicados removidos:", duplicados.sum())
dadosAracaju = dadosAracaju.loc[~duplicados].copy()

# Remove repetições da mesma combinação de posto, produto e data de coleta.
repetidos_posto_produto_data = dadosAracaju.duplicated(
    subset=CHAVE_REGISTRO,
    keep="first",
)
print(
    "Registros repetidos do mesmo posto, produto e data removidos:",
    repetidos_posto_produto_data.sum(),
)
dadosAracaju = dadosAracaju.loc[~repetidos_posto_produto_data].copy()

# Formata datas, ordena os registros e calcula o total final da limpeza.
dadosAracaju["Data da Coleta"] = dadosAracaju["Data da Coleta"].dt.strftime("%d/%m/%Y")
dadosAracaju = dadosAracaju.sort_values(CHAVE_REGISTRO).reset_index(drop=True)
quantidade_depois = len(dadosAracaju)
print("Quantidade de registros depois da limpeza:", quantidade_depois)
print("Total de registros removidos:", quantidade_antes - quantidade_depois)

# Grava um único CSV final com separador e decimal no padrão das planilhas.
dadosAracaju.to_csv(
    "base_limpa_aracaju.csv",
    index=False,
    encoding="utf-8-sig",
    sep=";",
    decimal=",",
    float_format="%.2f",
)
