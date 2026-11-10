#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Testes da interface grafica. Precisam de Tkinter e de uma tela (nao rodam em servidor sem display)."""

import os
import tempfile
import unittest

try:
    import tkinter as tk
    _raiz_teste = tk.Tk()
    _raiz_teste.destroy()
    TEM_TELA = True
except Exception:  # sem tkinter ou sem display
    TEM_TELA = False

if TEM_TELA:
    import gui
    import doacoes as app


@unittest.skipUnless(TEM_TELA, "Tkinter/tela indisponivel")
class TestJanela(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = os.path.join(self.tmp.name, "d.csv")
        self.f = os.path.join(self.tmp.name, "f.csv")
        self.raiz = tk.Tk()
        self.j = gui.Janela(self.raiz, self.d, self.f)

    def tearDown(self):
        self.raiz.destroy()
        self.tmp.cleanup()

    def cadastrar(self, cod, alim, qtd, data="05/10/2026"):
        self.j.v_codigo.set(cod); self.j.v_alimento.set(alim); self.j.v_qtd.set(qtd); self.j.v_data.set(data)
        self.j.cadastrar()

    def pedir(self, fam, pessoas, alim):
        self.j.v_familia.set(fam); self.j.v_pessoas.set(pessoas); self.j.v_alimento_pedido.set(alim)
        self.j.registrar_pedido()

    def test_cadastro_valido_e_persistencia(self):
        self.cadastrar("30", "Arroz", "10")
        self.assertEqual(len(self.j.doacoes), 1)
        self.assertEqual(len(self.j.tab_doacoes.get_children()), 1)
        self.assertEqual(len(app.carregar_doacoes(self.d)[0]), 1)

    def test_cadastro_invalido_nao_altera(self):
        for args in (("abc", "Arroz", "1"), ("1", "  ", "1"), ("1", "Arroz", "0"), ("1", "Arroz", "1", "32/10/2026"),
                     ("1", "Arroz", "1", "01/01/2999")):
            self.cadastrar(*args)
            self.assertEqual(self.j.doacoes, [])
            self.assertEqual(self.j.rotulo_status.cget("fg"), gui.COR_ERRO)

    def test_codigo_duplicado(self):
        self.cadastrar("30", "Arroz", "10")
        self.cadastrar("30", "Feijão", "5")
        self.assertEqual(len(self.j.doacoes), 1)
        self.assertIn("já cadastrado", self.j.msg.get())

    def test_buscas_e_ordenacao(self):
        for c, a in (("30", "Arroz"), ("10", "Feijão"), ("50", "Óleo"), ("20", "Macarrão")):
            self.cadastrar(c, a, "5")
        self.j.v_busca_cod.set("20"); self.j.buscar_codigo(False)
        self.assertIn("posição 4 (4 comparações)", self.j.msg.get())
        self.j.buscar_codigo(True)  # lista fora de ordem: ordena antes
        self.assertIn("foi ordenada", self.j.msg.get())
        self.assertTrue(app.esta_ordenada(self.j.doacoes, "codigo"))
        self.j.v_busca_cod.set("99"); self.j.buscar_codigo(True)
        self.assertIn("não encontrado", self.j.msg.get())
        self.j.v_chave.set("alimento"); self.j.ordenar()
        self.assertTrue(app.esta_ordenada(self.j.doacoes, "alimento"))
        self.j.v_busca_nome.set("oleo"); self.j.buscar_nome()
        self.assertEqual(len(self.j.tab_doacoes.get_children()), 1)

    def test_fila_e_atendimento(self):
        self.cadastrar("1", "Arroz", "10"); self.cadastrar("2", "Feijão", "5")
        self.pedir("Maria", "4", "arroz"); self.pedir("João", "3", "feijao"); self.pedir("Ana", "20", "feijao")
        self.assertEqual(len(self.j.tab_fila.get_children()), 3)
        self.j.atender(); self.j.atender()
        self.assertEqual(self.j.fila.tamanho, 1)
        self.assertEqual(app.estoque_de(self.j.doacoes, "arroz"), 6)
        self.j.atender()  # estoque insuficiente
        self.assertEqual(self.j.fila.primeiro().familia, "Ana")
        self.assertIn("Estoque insuficiente", self.j.msg.get())
        self.assertEqual(self.j.rotulo_status.cget("fg"), gui.COR_ERRO)

    def test_pedido_invalido_e_fila_vazia(self):
        self.pedir("", "2", "arroz"); self.pedir("A", "31", "arroz"); self.pedir("A", "x", "arroz")
        self.assertEqual(self.j.fila.tamanho, 0)
        self.j.atender()
        self.assertIn("fila está vazia", self.j.msg.get())

    def test_estoque_e_recarga(self):
        self.cadastrar("1", "Arroz", "10"); self.cadastrar("2", "arroz ", "5"); self.pedir("Maria", "2", "Arroz")
        self.j.atualizar_estoque()
        self.assertEqual(self.j.tab_estoque.item(self.j.tab_estoque.get_children()[0])["values"], ["Arroz", 15])
        outra = tk.Tk()
        try:
            j2 = gui.Janela(outra, self.d, self.f)
            self.assertEqual((len(j2.doacoes), j2.fila.tamanho, j2.proxima_senha), (2, 1, 2))
        finally:
            outra.destroy()


if __name__ == "__main__":
    unittest.main()
