"""Ponto de entrada do projeto: executa todas as etapas, na ordem, de ponta a ponta.

Cada etapa lê o arquivo gerado pela anterior:

    planilhas/*.csv                      dados originais da ANP
      -> criaBaseBruta.py                base_limpa_aracaju.csv
      -> metricasBaseBruta.py            apenas imprime um resumo da base limpa
      -> processamento_temporal.py       dados_aracaju_processados.csv (com variáveis temporais)
      -> comparar_metodos.py             acrescenta os quatro métodos à mesma base e gera os relatórios
      -> analise_sensibilidade.py        repete os métodos em 34 configurações

Tudo o que cada etapa imprime fica guardado em um arquivo de `relatorios/`.
A execução completa leva alguns minutos, principalmente pelo Random Forest.
"""
from pathlib import Path
import subprocess
import sys
import os

RAIZ = Path(__file__).resolve().parent
relatorios = RAIZ / 'relatorios'
relatorios.mkdir(exist_ok=True)
# Pares (script a executar, arquivo que recebe o que o script imprimir).
for script, relatorio in [('criaBaseBruta.py', 'limpeza.txt'),
                          ('metricasBaseBruta.py', 'base.txt'),
                          ('processamento_temporal.py', 'temporal.txt'),
                          ('comparar_metodos.py', 'execucao_modelos.txt'),
                          ('analise_sensibilidade.py', 'execucao_sensibilidade.txt')]:
    # sys.executable usa o mesmo Python (e o mesmo ambiente virtual) deste script.
    # PYTHONIOENCODING garante acentos corretos na saída capturada, também no Windows.
    resultado = subprocess.run([sys.executable, str(RAIZ / script)], cwd=RAIZ,
                               capture_output=True, text=True, encoding='utf-8',
                               env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})
    (relatorios / relatorio).write_text(resultado.stdout + resultado.stderr, encoding='utf-8')
    # Texto sem acentos de propósito: aparece igual em qualquer codificação de terminal.
    print(f'{script}: retorno {resultado.returncode}; detalhes em relatorios/{relatorio}')
    # Interrompe na primeira falha: as etapas seguintes dependem desta.
    if resultado.returncode:
        raise RuntimeError(resultado.stderr)
