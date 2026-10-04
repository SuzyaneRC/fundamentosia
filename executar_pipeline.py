"""Reproduz as etapas e guarda os resumos sem exigir planilhas por etapa."""
from pathlib import Path
import subprocess
import sys
import os

RAIZ = Path(__file__).resolve().parent
relatorios = RAIZ / 'relatorios'
relatorios.mkdir(exist_ok=True)
for script, relatorio in [('criaBaseBruta.py', 'limpeza.txt'),
                          ('metricasBaseBruta.py', 'base.txt'),
                          ('processamento_temporal.py', 'temporal.txt'),
                          ('comparar_metodos.py', 'execucao_modelos.txt')]:
    resultado = subprocess.run([sys.executable, str(RAIZ / script)], cwd=RAIZ,
                               capture_output=True, text=True, encoding='utf-8',
                               env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})
    (relatorios / relatorio).write_text(resultado.stdout + resultado.stderr, encoding='utf-8')
    print(f'{script}: código {resultado.returncode}; relatório em relatorios/{relatorio}')
    if resultado.returncode:
        raise RuntimeError(resultado.stderr)
