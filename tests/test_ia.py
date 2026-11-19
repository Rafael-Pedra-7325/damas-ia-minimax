import os
import sys
import time
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from jogo import PartidaDamas, FEN_INICIAL
from ia import melhor_jogada
from app import app


class DamasRegrasETaticaTestCase(unittest.TestCase):
    def test_captura_obrigatoria_e_captura_para_tras(self):
        # Pedra branca em d4 pode capturar pedra preta para trás em c3 -> b2
        fen = "8/8/8/8/3w4/2b5/8/8 w 0"
        partida = PartidaDamas(fen)
        legais = partida.lances_legais()
        self.assertEqual(len(legais), 1)
        self.assertEqual(legais[0]["uci"], "d4xb2")
        self.assertTrue(legais[0]["captura"])

        with self.assertRaises(ValueError):
            partida.jogar("d4-e5")

    def test_lei_da_maioria_captura_dupla_obrigatoria(self):
        # Pedra branca em a1 pode capturar 1 peça (a1xc3) ou 2 peças (a1xc3xe5)
        fen = "8/8/8/3b4/8/1b6/8/w7 w 0"
        partida = PartidaDamas(fen)
        legais = partida.lances_legais()
        self.assertEqual(len(legais), 1)
        self.assertEqual(legais[0]["uci"], "a1xc3xe5")
        self.assertEqual(legais[0]["qtd_capturas"], 2)

    def test_dama_voadora_e_coroacao(self):
        # Pedra branca em b7 coroa em a8
        fen = "8/1w6/8/8/8/8/8/7b w 0"
        partida = PartidaDamas(fen)
        info = partida.jogar("b7-a8")
        self.assertTrue(info["promocao"])

        # Dama branca em a8 pode voar pela diagonal longa até g2
        partida.turno = 1
        legais_dama = [l["uci"] for l in partida.lances_legais()]
        self.assertIn("a8-g2", legais_dama)

    def test_ia_encontra_golpe_tatico_e_respeita_orcamento_tempo(self):
        # IA (brancas) possui captura dupla vencedora
        fen = "8/8/4b3/8/2b5/1w6/8/7b w 0"
        partida = PartidaDamas(fen)
        inicio = time.perf_counter()
        lance, detalhes = melhor_jogada(partida, dificuldade="mestre")
        duracao = time.perf_counter() - inicio

        self.assertEqual(lance, "b3xd5xf7")
        self.assertLess(duracao, 3.0)
        self.assertGreater(detalhes["nos_avaliados"], 0)


class DamasWebApiTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_pagina_principal_e_health(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        resp_health = self.client.get("/health")
        self.assertEqual(resp_health.status_code, 200)

    def test_fluxo_validar_e_jogada_ia(self):
        resp_val = self.client.post("/api/validar", json={"fen": FEN_INICIAL, "lance": "c3-d4"})
        self.assertEqual(resp_val.status_code, 200)
        novo_fen = resp_val.get_json()["estado"]["fen"]

        resp_ia = self.client.post(
            "/api/jogada",
            json={"fen": novo_fen, "dificuldade": "medio", "historico_fens": [FEN_INICIAL, novo_fen]},
        )
        self.assertEqual(resp_ia.status_code, 200)
        dados = resp_ia.get_json()
        self.assertIsNotNone(dados["lance"])
        self.assertGreater(dados["telemetria"]["nos_avaliados"], 0)

    def test_api_resiste_a_payloads_malformados(self):
        casos_invalidos = [
            ("/api/validar", {"fen": FEN_INICIAL}),
            ("/api/validar", {"fen": "", "lance": "c3-d4"}),
            ("/api/jogada", {"fen": "8/8/8/8/8/8/8/8 w 0"}),
            ("/api/analisar", {"fen": None}),
        ]
        for rota, payload in casos_invalidos:
            resp = self.client.post(rota, json=payload)
            self.assertEqual(resp.status_code, 400, f"Falhou em {rota} com {payload}")
            self.assertIn("erro", resp.get_json())


if __name__ == "__main__":
    unittest.main()
