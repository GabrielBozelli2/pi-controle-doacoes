#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Testes automatizados (unittest) do sistema de doacoes. Execute: python3 test_doacoes.py -v"""

import os
import random
import tempfile
import unittest
from datetime import date
from unittest import mock

import doacoes as app
from doacoes import Doacao, Fila, Pedido


def lote(n=5):
    return [Doacao(c, a, q, date(2026, 10, d)) for (c, a, q, d) in
            [(30, "Arroz", 10, 5), (10, "Feijao", 8, 2), (50, "Arroz", 4, 1),
             (20, "Macarrao", 6, 9), (40, "Oleo", 3, 7)][:n]]


class TestBuscas(unittest.TestCase):
    def test_sequencial_encontra_e_conta(self):
        i, c = app.busca_sequencial(lote(), 20)
        self.assertEqual((i, c), (3, 4))

    def test_sequencial_inexistente(self):
        i, c = app.busca_sequencial(lote(), 99)
        self.assertEqual((i, c), (-1, 5))

    def test_sequencial_lista_vazia(self):
        self.assertEqual(app.busca_sequencial([], 1), (-1, 0))

    def test_binaria_encontra(self):
        l = lote()
        app.ordenar_insercao(l, "codigo")
        i, c = app.busca_binaria(l, 40)
        self.assertEqual(l[i].codigo, 40)
        self.assertLessEqual(c, 3)

    def test_binaria_inexistente_e_vazia(self):
        l = lote()
        app.ordenar_insercao(l, "codigo")
        self.assertEqual(app.busca_binaria(l, 25)[0], -1)
        self.assertEqual(app.busca_binaria([], 1), (-1, 0))

    def test_binaria_um_elemento(self):
        self.assertEqual(app.busca_binaria(lote(1), 30), (0, 1))

    def test_busca_por_nome_parcial(self):
        self.assertEqual(len(app.buscar_por_alimento(lote(), "  ARROZ ")), 2)
        self.assertEqual(app.buscar_por_alimento(lote(), "sal"), [])

    def test_binaria_igual_sequencial_em_massa(self):
        rnd = random.Random(1)
        codigos = rnd.sample(range(1, 5000), 300)
        l = [Doacao(c, "x", 1, date(2026, 1, 1)) for c in codigos]
        app.ordenar_insercao(l, "codigo")
        for alvo in list(range(0, 5100, 7)):
            self.assertEqual(app.busca_binaria(l, alvo)[0] != -1,
                             app.busca_sequencial(l, alvo)[0] != -1)


class TestOrdenacao(unittest.TestCase):
    def test_todas_as_chaves(self):
        for chave in app.CHAVES:
            l = lote()
            app.ordenar_insercao(l, chave)
            self.assertTrue(app.esta_ordenada(l, chave), chave)

    def test_estavel(self):
        l = lote()
        app.ordenar_insercao(l, "alimento")
        arroz = [d.codigo for d in l if d.alimento == "Arroz"]
        self.assertEqual(arroz, [30, 50])

    def test_mesmo_resultado_que_sorted(self):
        rnd = random.Random(7)
        l = [Doacao(c, "x", 1, date(2026, 1, 1)) for c in rnd.sample(range(1, 1000), 200)]
        esperado = sorted(l, key=lambda d: d.codigo)
        app.ordenar_insercao(l, "codigo")
        self.assertEqual(l, esperado)

    def test_vazia_e_um_elemento(self):
        self.assertEqual(app.ordenar_insercao([], "codigo"), 0)
        self.assertEqual(app.ordenar_insercao(lote(1), "data"), 0)


class TestFila(unittest.TestCase):
    def test_fifo(self):
        f = Fila()
        for s in (1, 2, 3):
            f.enfileirar(Pedido(s, "F", 1, "arroz"))
        self.assertEqual([f.desenfileirar().senha for _ in range(3)], [1, 2, 3])
        self.assertTrue(f.vazia())
        self.assertIsNone(f.desenfileirar())
        self.assertEqual(f.tamanho, 0)

    def test_reuso_apos_esvaziar(self):
        f = Fila()
        f.enfileirar(Pedido(1, "A", 1, "x"))
        f.desenfileirar()
        f.enfileirar(Pedido(2, "B", 1, "x"))
        self.assertEqual(f.primeiro().senha, 2)
        self.assertEqual(f.tamanho, 1)


class TestEstoqueEAtendimento(unittest.TestCase):
    def test_estoque_soma_lotes(self):
        self.assertEqual(app.estoque_de(lote(), " arroz"), 14)

    def test_retirada_comeca_pela_mais_antiga(self):
        l = lote()
        self.assertTrue(app.retirar_do_estoque(l, "arroz", 5))
        # lote 50 (01/10) tinha 4 e foi zerado; lote 30 (05/10) perdeu 1
        self.assertEqual(sorted((d.codigo, d.quantidade) for d in l if d.alimento == "Arroz"), [(30, 9)])

    def test_estoque_insuficiente_nao_altera(self):
        l = lote()
        antes = [(d.codigo, d.quantidade) for d in l]
        self.assertFalse(app.retirar_do_estoque(l, "arroz", 15))
        self.assertEqual(antes, [(d.codigo, d.quantidade) for d in l])

    def test_atender_mantem_ordem_se_faltar_estoque(self):
        l, f = lote(), Fila()
        f.enfileirar(Pedido(1, "Silva", 20, "feijao"))
        f.enfileirar(Pedido(2, "Souza", 1, "oleo"))
        p, msg = app.atender_proximo(f, l)
        self.assertIsNone(p)
        self.assertIn("insuficiente", msg)
        self.assertEqual(f.primeiro().senha, 1)

    def test_atender_com_sucesso(self):
        l, f = lote(), Fila()
        f.enfileirar(Pedido(1, "Silva", 3, "feijao"))
        p, _ = app.atender_proximo(f, l)
        self.assertEqual(p.senha, 1)
        self.assertEqual(app.estoque_de(l, "feijao"), 5)

    def test_atender_fila_vazia(self):
        self.assertEqual(app.atender_proximo(Fila(), lote())[0], None)

    def test_acentos_e_caixa_sao_ignorados(self):
        self.assertEqual(app.normalizar("  FEIJÃO  "), app.normalizar("feijao"))
        self.assertEqual(app.estoque_de(lote(), "oleo"), 3)
        l = [Doacao(1, "Água", 1, date(2026, 1, 1)), Doacao(2, "Zebu", 1, date(2026, 1, 1))]
        app.ordenar_insercao(l, "alimento")
        self.assertEqual(l[0].alimento, "Água")

    def test_resumo_ordem_alfabetica(self):
        nomes = [n for n, _ in app.resumo_estoque(lote())]
        self.assertEqual(nomes, sorted(nomes))


class TestCSV(unittest.TestCase):
    def test_ida_e_volta(self):
        with tempfile.TemporaryDirectory() as t:
            c = os.path.join(t, "d.csv")
            app.salvar_doacoes(lote(), c)
            lidas, erros = app.carregar_doacoes(c)
            self.assertEqual((lidas, erros), (lote(), 0))
            f = Fila()
            f.enfileirar(Pedido(1, "Maria, da Silva", 4, "arroz"))  # virgula no nome
            cf = os.path.join(t, "f.csv")
            app.salvar_fila(f, cf)
            f2, erros = app.carregar_fila(cf)
            self.assertEqual(f2.pedidos(), f.pedidos())
            self.assertEqual(erros, 0)

    def test_arquivo_inexistente(self):
        self.assertEqual(app.carregar_doacoes("/nao/existe.csv"), ([], 0))

    def test_linhas_invalidas_sao_descartadas(self):
        with tempfile.TemporaryDirectory() as t:
            c = os.path.join(t, "d.csv")
            with open(c, "w", encoding="utf-8") as f:
                f.write("codigo,alimento,quantidade,data\n"
                        "1,Arroz,5,01/10/2026\n"      # ok
                        "abc,Feijao,5,01/10/2026\n"   # codigo invalido
                        "2,Feijao,-3,01/10/2026\n"    # quantidade negativa
                        "3,Oleo,2,31/02/2026\n"       # data inexistente
                        "1,Arroz,9,02/10/2026\n"      # codigo repetido
                        "4,,2,01/10/2026\n"           # alimento vazio
                        "5,Sal\n")                    # linha incompleta
            lidas, erros = app.carregar_doacoes(c)
            self.assertEqual(len(lidas), 1)
            self.assertEqual(erros, 6)


class TestEntradas(unittest.TestCase):
    def test_inteiro_repete_ate_valido(self):
        with mock.patch("builtins.input", side_effect=["abc", "", "-2", "0", "7"]), \
                mock.patch("builtins.print"):
            self.assertEqual(app.ler_inteiro("n: "), 7)

    def test_inteiro_maximo(self):
        with mock.patch("builtins.input", side_effect=["31", "30"]), mock.patch("builtins.print"):
            self.assertEqual(app.ler_inteiro("n: ", 1, 30), 30)

    def test_data_invalida_e_futura(self):
        with mock.patch("builtins.input", side_effect=["32/01/2026", "2026-01-01", "01/01/2999", "15/10/2026"]), \
                mock.patch("builtins.print"):
            self.assertEqual(app.ler_data("d: "), date(2026, 10, 15))

    def test_texto_em_branco(self):
        with mock.patch("builtins.input", side_effect=["   ", "  Pao   frances "]), mock.patch("builtins.print"):
            self.assertEqual(app.ler_texto("t: "), "Pao frances")


if __name__ == "__main__":
    unittest.main()
