"""Verificações usadas na limpeza, separadas de `criaBaseBruta.py` para poderem ser testadas.

`criaBaseBruta.py` executa toda a limpeza ao ser importado, então os testes usam este módulo.
"""


def encontrar_coletas_conflitantes(dados, chave):
    """Devolve as linhas cuja `chave` aparece com mais de um preço de venda.

    Essas linhas indicam uma divergência na fonte: não há como saber, pelos dados, qual preço
    está correto. Repetições com o mesmo preço não entram no resultado.
    """
    precos_por_chave = dados.groupby(chave, dropna=False)["Valor de Venda"].transform("nunique")
    return dados.loc[precos_por_chave > 1].sort_values(chave)
