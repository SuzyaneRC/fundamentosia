import json
from pathlib import Path
import unittest
import numpy as np
import pandas as pd
from baseline_regressao import aplicar_baseline
from comparar_metodos import comparar, METODOS
from avaliacao_temporal import criar_janelas, avaliar_janelas
from modelos_produto import aplicar_por_produto
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[1]


class MetodosTests(unittest.TestCase):
    def test_baseline_limites_por_produto_e_exclusao_series_curtas(self):
        ruido = np.array([0, 0.1, -0.1, 0.05, 0, 0.1, 0, 0, 0, 2.0])
        df = pd.DataFrame({'Produto': ['A'] * 10 + ['B'] * 10,
                           'Data da Coleta': [f'{d:02d}/01/2026' for d in range(1, 11)] * 2,
                           'Valor de Venda': np.concatenate([5 + ruido, 50 + ruido * 10]),
                           'poucos_registros': False})
        result = aplicar_baseline(df)
        np.testing.assert_allclose(result.loc[:9, 'pontuacao_anomalia'], result.loc[10:, 'pontuacao_anomalia'], atol=1e-10)
        df.loc[0, 'poucos_registros'] = True
        self.assertFalse(aplicar_baseline(df).loc[0, 'utilizado_regressao'])

    def test_comparacao_ignora_nao_avaliados(self):
        df = pd.DataFrame({f'utilizado_{m}': [True, True, False] for m in METODOS})
        for m in METODOS:
            df[f'anomalia_{m}'] = [True, False, False]
        df.loc[1, 'anomalia_kmeans'] = True
        par = next(p for p in comparar(df) if p['metodo_a'] == 'regressao' and p['metodo_b'] == 'kmeans')
        self.assertEqual(par['avaliados_em_comum'], 2)
        self.assertEqual(par['concordancia'], 0.5)
        self.assertEqual(par['jaccard'], 0.5)

    def test_resultados_consolidados_e_teste_temporal(self):
        df = pd.read_csv(RAIZ / 'dados_aracaju_processados.csv', sep=';', decimal=',', dtype={'CNPJ da Revenda': 'string'})
        relatorio = json.loads((RAIZ / 'relatorios/comparacao.json').read_text(encoding='utf-8'))
        self.assertEqual(len(df), 4816)
        self.assertFalse(df.duplicated(['CNPJ da Revenda', 'Produto', 'Data da Coleta']).any())
        datas = pd.to_datetime(df['Data da Coleta'], dayfirst=True)
        corte = pd.Timestamp(relatorio['random_forest']['inicio_teste'])
        self.assertTrue((datas[df['utilizado_random_forest']] >= corte).all())
        self.assertFalse(df.loc[datas < corte, 'utilizado_random_forest'].any())
        for m in METODOS:
            usados = df[f'utilizado_{m}']
            self.assertFalse(df.loc[~usados, f'anomalia_{m}'].any())
            self.assertFalse((usados & df['poucos_registros']).any())
            self.assertEqual(int(usados.sum()), relatorio['metodos'][m]['avaliados'])
        self.assertEqual(comparar(df), relatorio['comparacoes'])
        for janela in relatorio['random_forest']['janelas']:
            self.assertLess(janela['fim_treino'], janela['inicio_calibracao'])
            self.assertLess(janela['fim_calibracao'], janela['inicio_teste'])
        self.assertTrue(df.loc[df['utilizado_random_forest'], 'limite_erro_random_forest'].notna().all())

    def test_janelas_sem_datas_compartilhadas_ou_testes_repetidos(self):
        datas = pd.date_range('2025-01-01', periods=40)
        testes = []
        for treino, cal, teste in criar_janelas(datas):
            self.assertLess(treino[-1], cal[0])
            self.assertLess(cal[-1], teste[0])
            testes.extend(teste)
        self.assertEqual(len(testes), len(set(testes)))
        self.assertEqual(criar_janelas(datas[:5]), [])

    def test_random_forest_nao_usa_preco_futuro_no_treino(self):
        treinados = []
        class Modelo:
            def fit(self, x, y):
                self.maximo = x['tempo'].max()
                treinados.append(self.maximo)
            def predict(self, x):
                self_teste = x['tempo'].min()
                if self_teste <= self.maximo:
                    raise AssertionError('Previsão sobre data usada no treino')
                return np.zeros(len(x))
        df = pd.DataFrame({'Produto': 'A', 'Data da Coleta': pd.date_range('2025-01-01', periods=40).repeat(3),
                           'tempo': np.repeat(np.arange(40), 3), 'preco': 1.0})
        _, _, _, flags, limites, metricas, indices = avaliar_janelas(df, ['tempo'], 'preco', Modelo)
        self.assertEqual(len(indices), len(set(indices)))
        self.assertTrue(treinados)
        self.assertTrue((limites == 1).all())
        self.assertEqual(len(flags), metricas['teste'])

    def test_padronizacao_independente_por_produto(self):
        df = pd.DataFrame({'Produto': ['A'] * 12 + ['B'] * 12 + ['C'] * 3,
                           'poucos_registros': False})
        for coluna in ['Valor de Venda', 'variacao_percentual', 'diff_mediana_historica_posto', 'diff_mediana_municipal_percentual']:
            df[coluna] = np.concatenate([np.arange(12), 100 + np.arange(12) * 10, [1, 2, 3]])
        entradas = []
        def executar(x):
            entradas.append(x)
            return None, np.zeros(len(x), dtype=bool), np.zeros(len(x))
        with patch('modelos_produto.executar_isolation_forest', side_effect=executar), patch('modelos_produto.testar_contaminacoes', return_value={}):
            resultado, _, _ = aplicar_por_produto(df)
        self.assertEqual(len(entradas), 2)
        for x in entradas:
            np.testing.assert_allclose(x.mean(axis=0), 0, atol=1e-12)
        self.assertFalse(resultado.loc[df['Produto'].eq('C'), 'utilizado_isolation_forest'].any())


if __name__ == '__main__':
    unittest.main()
