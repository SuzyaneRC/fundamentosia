import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

# ==========================================
# 1. CARREGAR A BASE PROCESSADA
# ==========================================

arquivo_entrada = "dados_aracaju_processados.csv"

df = pd.read_csv(arquivo_entrada, sep=";", encoding="utf-8")

print(f"Registros carregados: {len(df)}")

# ==========================================
# 2. PREPARAR DATA E PREÇO
# ==========================================

df["Data da Coleta"] = pd.to_datetime(
    df["Data da Coleta"],
    dayfirst=True,
    errors="coerce"
)

df["Valor de Venda"] = (
    df["Valor de Venda"]
    .astype(str)
    .str.replace(",", ".", regex=False)
    .astype(float)
)

# Variável numérica representando o tempo
df["tempo"] = (
    df["Data da Coleta"] - df["Data da Coleta"].min()
).dt.days

# Criar coluna que receberá o preço estimado
df["preco_estimado"] = np.nan

# ==========================================
# 3. REGRESSÃO SEPARADA POR PRODUTO
# ==========================================

for produto, grupo in df.groupby("Produto"):

    # Remover registros sem data ou preço
    grupo_valido = grupo.dropna(
        subset=["tempo", "Valor de Venda"]
    )

    # É necessário ter pelo menos 2 registros
    if len(grupo_valido) < 2:
        print(f"Produto {produto}: poucos registros para regressão.")
        continue

    X = grupo_valido[["tempo"]]
    y = grupo_valido["Valor de Venda"]

    modelo = LinearRegression()
    modelo.fit(X, y)

    # Preço estimado
    estimado = modelo.predict(X)

    df.loc[
        grupo_valido.index,
        "preco_estimado"
    ] = estimado

    print(
        f"Produto: {produto} | "
        f"Registros: {len(grupo_valido)} | "
        f"Coeficiente: {modelo.coef_[0]:.6f}"
    )

# ==========================================
# 4. CALCULAR O RESÍDUO
# ==========================================

df["residuo_regressao"] = (
    df["Valor de Venda"] - df["preco_estimado"]
)

# ==========================================
# 5. CRITÉRIO PELO DESVIO PADRÃO
# ==========================================

desvio_padrao = df["residuo_regressao"].std()

limite_desvio = 2 * desvio_padrao

df["anomalia_desvio_padrao"] = (
    df["residuo_regressao"].abs() > limite_desvio
)

# ==========================================
# 6. CRITÉRIO PELO MAD
# ==========================================

mediana_residuo = df["residuo_regressao"].median()

desvios = (
    df["residuo_regressao"] - mediana_residuo
).abs()

mad = desvios.median()

# Evita divisão por zero
if mad == 0:
    df["score_mad"] = 0
else:
    df["score_mad"] = (
        (df["residuo_regressao"] - mediana_residuo).abs()
        / (1.4826 * mad)
    )

df["anomalia_mad"] = df["score_mad"] > 3.5

# ==========================================
# 7. DEFINIR A ANOMALIA FINAL
# ==========================================

df["anomalia_regressao"] = (
    df["anomalia_desvio_padrao"]
    | df["anomalia_mad"]
)

# ==========================================
# 8. PONTUAÇÃO DA ANOMALIA
# ==========================================

if desvio_padrao == 0:
    df["pontuacao_anomalia"] = 0
else:
    df["pontuacao_anomalia"] = (
        df["residuo_regressao"].abs()
        / desvio_padrao
    )

# ==========================================
# 9. SALVAR RESULTADO
# ==========================================

arquivo_saida = "dados_aracaju_baseline.csv"

df.to_csv(
    arquivo_saida,
    sep=";",
    index=False,
    encoding="utf-8"
)

# ==========================================
# 10. RESUMO
# ==========================================

print("\n==========================================")
print("RESULTADO DO BASELINE")
print("==========================================")

print(f"Total de registros: {len(df)}")
print(f"Desvio padrão dos resíduos: {desvio_padrao:.4f}")
print(f"Limite pelo desvio padrão: {limite_desvio:.4f}")
print(f"MAD: {mad:.4f}")
print(
    f"Anomalias pelo desvio padrão: "
    f"{df['anomalia_desvio_padrao'].sum()}"
)
print(
    f"Anomalias pelo MAD: "
    f"{df['anomalia_mad'].sum()}"
)
print(
    f"Anomalias finais: "
    f"{df['anomalia_regressao'].sum()}"
)

print(f"\nArquivo salvo: {arquivo_saida}")