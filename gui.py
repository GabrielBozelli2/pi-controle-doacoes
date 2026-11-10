#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface grafica (Tkinter) do Sistema de Controle de Doacoes e Fila de
Distribuicao de Alimentos.

Projeto Integrador - Laboratorio de Programacao (UNISA).
Uso: python3 gui.py

Toda a logica (registros, buscas, ordenacao, fila FIFO, estoque e CSV) esta em
doacoes.py; este arquivo apenas monta as janelas e chama essas funcoes.
"""

import tkinter as tk
from datetime import date
from tkinter import ttk

import doacoes as app
from doacoes import Doacao, Pedido

COR_OK = "#1b6e2d"
COR_ERRO = "#b3261e"


class Janela:
    def __init__(self, raiz, arq_doacoes=app.ARQ_DOACOES, arq_fila=app.ARQ_FILA):
        self.raiz = raiz
        self.arq_doacoes, self.arq_fila = arq_doacoes, arq_fila
        self.doacoes, erros1 = app.carregar_doacoes(arq_doacoes)
        self.fila, erros2 = app.carregar_fila(arq_fila)
        self.proxima_senha = max([p.senha for p in self.fila.pedidos()], default=0) + 1

        raiz.title("Controle de Doações e Fila de Distribuição de Alimentos")
        raiz.geometry("860x640")
        raiz.minsize(760, 560)
        self.msg = tk.StringVar()
        self._montar_abas()
        self.rotulo_status = tk.Label(raiz, textvariable=self.msg, anchor="w", justify="left", wraplength=820, padx=10, pady=6,
                                    font=("TkDefaultFont", 10, "bold"))
        self.rotulo_status.pack(fill="x", side="bottom")
        self.atualizar_tudo()
        if erros1 or erros2:
            self.status(f"{erros1 + erros2} linha(s) inválida(s) ignorada(s) ao carregar os arquivos.", ok=False)
        else:
            self.status("Pronto.")
        raiz.protocol("WM_DELETE_WINDOW", self.fechar)

    # ------------------------------------------------------------ utilidades
    def status(self, texto, ok=True):
        self.msg.set(texto)
        self.rotulo_status.config(fg=COR_OK if ok else COR_ERRO)

    def salvar(self):
        app.salvar_doacoes(self.doacoes, self.arq_doacoes)
        app.salvar_fila(self.fila, self.arq_fila)

    def fechar(self):
        self.salvar()
        self.raiz.destroy()

    def atualizar_tudo(self):
        self.mostrar_doacoes(self.doacoes)
        self.atualizar_fila()
        self.atualizar_estoque()

    def _campo(self, pai, rotulo, linha, coluna, largura=14, valor=""):
        tk.Label(pai, text=rotulo).grid(row=linha, column=coluna * 2, sticky="e", padx=(8, 3), pady=3)
        var = tk.StringVar(value=valor)
        ttk.Entry(pai, textvariable=var, width=largura).grid(row=linha, column=coluna * 2 + 1, sticky="w", pady=3)
        return var

    @staticmethod
    def _tabela(pai, colunas, larguras, altura=10):
        quadro = tk.Frame(pai)
        tv = ttk.Treeview(quadro, columns=[c for c, _ in colunas], show="headings", height=altura)
        for (c, titulo), larg in zip(colunas, larguras):
            tv.heading(c, text=titulo)
            tv.column(c, width=larg, anchor="w" if c in ("alimento", "familia") else "center")
        barra = ttk.Scrollbar(quadro, orient="vertical", command=tv.yview)
        tv.configure(yscrollcommand=barra.set)
        tv.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        quadro.pack(fill="both", expand=True, padx=10, pady=6)
        return tv

    # ------------------------------------------------------------ montagem
    def _montar_abas(self):
        abas = ttk.Notebook(self.raiz)
        abas.pack(fill="both", expand=True, padx=6, pady=6)
        self.abas = abas
        self._aba_doacoes(abas)
        self._aba_fila(abas)
        self._aba_estoque(abas)
        abas.bind("<<NotebookTabChanged>>", lambda _e: self.atualizar_estoque())

    def _aba_doacoes(self, abas):
        aba = tk.Frame(abas)
        abas.add(aba, text="  Doações  ")
        cad = ttk.LabelFrame(aba, text="Cadastrar doação")
        cad.pack(fill="x", padx=10, pady=(8, 2))
        self.v_codigo = self._campo(cad, "Código do lote:", 0, 0, 10)
        self.v_alimento = self._campo(cad, "Alimento:", 0, 1, 20)
        self.v_qtd = self._campo(cad, "Quantidade:", 1, 0, 10)
        self.v_data = self._campo(cad, "Data (dd/mm/aaaa):", 1, 1, 14, date.today().strftime(app.FORMATO_DATA))
        ttk.Button(cad, text="Cadastrar doação", command=self.cadastrar).grid(row=1, column=4, padx=12)

        busca = ttk.LabelFrame(aba, text="Buscar e ordenar")
        busca.pack(fill="x", padx=10, pady=4)
        self.v_busca_cod = self._campo(busca, "Código:", 0, 0, 10)
        ttk.Button(busca, text="Busca sequencial", command=lambda: self.buscar_codigo(False)).grid(row=0, column=2, padx=4)
        ttk.Button(busca, text="Busca binária", command=lambda: self.buscar_codigo(True)).grid(row=0, column=3, padx=4)
        self.v_busca_nome = self._campo(busca, "Alimento:", 1, 0, 20)
        ttk.Button(busca, text="Buscar por nome", command=self.buscar_nome).grid(row=1, column=2, padx=4)
        ttk.Button(busca, text="Mostrar todas", command=lambda: self.mostrar_doacoes(self.doacoes)).grid(row=1, column=3, padx=4)
        tk.Label(busca, text="Ordenar por:").grid(row=0, column=4, padx=(16, 3))
        self.v_chave = tk.StringVar(value="codigo")
        ttk.Combobox(busca, textvariable=self.v_chave, values=list(app.CHAVES), state="readonly", width=11).grid(row=0, column=5)
        ttk.Button(busca, text="Ordenar", command=self.ordenar).grid(row=0, column=6, padx=6)

        self.tab_doacoes = self._tabela(
            aba, [("codigo", "Código"), ("alimento", "Alimento"), ("quantidade", "Quantidade"), ("data", "Data")],
            [90, 280, 110, 120])

    def _aba_fila(self, abas):
        aba = tk.Frame(abas)
        abas.add(aba, text="  Fila de distribuição  ")
        ped = ttk.LabelFrame(aba, text="Registrar pedido")
        ped.pack(fill="x", padx=10, pady=(8, 2))
        self.v_familia = self._campo(ped, "Família/responsável:", 0, 0, 24)
        self.v_pessoas = self._campo(ped, "Nº de pessoas (1 a 30):", 0, 1, 8)
        self.v_alimento_pedido = self._campo(ped, "Alimento:", 1, 0, 24)
        ttk.Button(ped, text="Registrar na fila", command=self.registrar_pedido).grid(row=1, column=2, columnspan=2, padx=12)
        self.tab_fila = self._tabela(
            aba, [("pos", "Posição"), ("senha", "Senha"), ("familia", "Família"), ("pessoas", "Pessoas"), ("alimento", "Alimento")],
            [80, 80, 260, 90, 200])
        ttk.Button(aba, text="Atender próximo da fila", command=self.atender).pack(pady=(0, 8))

    def _aba_estoque(self, abas):
        aba = tk.Frame(abas)
        abas.add(aba, text="  Estoque  ")
        tk.Label(aba, text="Total disponível por alimento (soma de todos os lotes)", anchor="w").pack(fill="x", padx=12, pady=(10, 0))
        self.tab_estoque = self._tabela(aba, [("alimento", "Alimento"), ("quantidade", "Quantidade")], [300, 140])

    # ------------------------------------------------------------ doações
    def mostrar_doacoes(self, lista):
        self.tab_doacoes.delete(*self.tab_doacoes.get_children())
        for i, d in enumerate(lista):
            self.tab_doacoes.insert("", "end", iid=str(i),
                                    values=(d.codigo, d.alimento, d.quantidade, d.data.strftime(app.FORMATO_DATA)))

    def cadastrar(self):
        try:
            codigo = app.converter_inteiro(self.v_codigo.get())
            if app.busca_sequencial(self.doacoes, codigo)[0] != -1:
                raise ValueError("Código já cadastrado.")
            alimento = app.converter_texto(self.v_alimento.get())
            qtd = app.converter_inteiro(self.v_qtd.get())
            data = app.converter_data(self.v_data.get())
        except ValueError as erro:
            return self.status(str(erro), ok=False)
        self.doacoes.append(Doacao(codigo, alimento, qtd, data))
        self.salvar()
        for v in (self.v_codigo, self.v_alimento, self.v_qtd):
            v.set("")
        self.atualizar_tudo()
        self.status(f"Doação {codigo} cadastrada ({qtd} de {alimento}).")

    def buscar_codigo(self, binaria):
        try:
            codigo = app.converter_inteiro(self.v_busca_cod.get())
        except ValueError as erro:
            return self.status(str(erro), ok=False)
        aviso = ""
        if binaria:
            if not app.esta_ordenada(self.doacoes, "codigo"):
                app.ordenar_insercao(self.doacoes, "codigo")
                self.mostrar_doacoes(self.doacoes)
                aviso = "Lista estava fora de ordem e foi ordenada por código antes da busca. "
            pos, comp = app.busca_binaria(self.doacoes, codigo)
        else:
            pos, comp = app.busca_sequencial(self.doacoes, codigo)
        metodo = "binária" if binaria else "sequencial"
        if pos == -1:
            return self.status(f"{aviso}Busca {metodo}: código {codigo} não encontrado ({comp} comparações).", ok=False)
        self.tab_doacoes.selection_set(str(pos))
        self.tab_doacoes.see(str(pos))
        self.status(f"{aviso}Busca {metodo}: código {codigo} encontrado na posição {pos + 1} ({comp} comparações).")

    def buscar_nome(self):
        try:
            termo = app.converter_texto(self.v_busca_nome.get())
        except ValueError as erro:
            return self.status(str(erro), ok=False)
        achados = app.buscar_por_alimento(self.doacoes, termo)
        self.mostrar_doacoes(achados)
        self.status(f"{len(achados)} lote(s) com “{termo}”.", ok=bool(achados))

    def ordenar(self):
        chave = self.v_chave.get()
        comp = app.ordenar_insercao(self.doacoes, chave)
        self.salvar()
        self.mostrar_doacoes(self.doacoes)
        self.status(f"Lista ordenada por {chave} ({comp} comparações).")

    # ------------------------------------------------------------ fila
    def atualizar_fila(self):
        self.tab_fila.delete(*self.tab_fila.get_children())
        for pos, p in enumerate(self.fila.pedidos(), 1):
            self.tab_fila.insert("", "end", values=(pos, p.senha, p.familia, p.pessoas, p.alimento))

    def registrar_pedido(self):
        try:
            familia = app.converter_texto(self.v_familia.get())
            pessoas = app.converter_inteiro(self.v_pessoas.get(), 1, 30)
            alimento = app.converter_texto(self.v_alimento_pedido.get())
        except ValueError as erro:
            return self.status(str(erro), ok=False)
        pedido = Pedido(self.proxima_senha, familia, pessoas, alimento)
        self.proxima_senha += 1
        self.fila.enfileirar(pedido)
        self.salvar()
        for v in (self.v_familia, self.v_pessoas, self.v_alimento_pedido):
            v.set("")
        self.atualizar_fila()
        self.status(f"Pedido registrado. Senha {pedido.senha}; posição {self.fila.tamanho} na fila.")

    def atender(self):
        primeiro = self.fila.primeiro()
        pedido, _ = app.atender_proximo(self.fila, self.doacoes)
        if pedido is None:
            if primeiro is None:
                return self.status("A fila está vazia.", ok=False)
            disp = app.estoque_de(self.doacoes, primeiro.alimento)
            return self.status(f"Estoque insuficiente de “{primeiro.alimento}”: necessário {primeiro.pessoas}, "
                               f"disponível {disp}. O pedido continua no início da fila.", ok=False)
        self.salvar()
        self.atualizar_tudo()
        self.status(f"Senha {pedido.senha} – {pedido.familia}: {pedido.pessoas} un. de {pedido.alimento} entregues.")

    # ------------------------------------------------------------ estoque
    def atualizar_estoque(self):
        self.tab_estoque.delete(*self.tab_estoque.get_children())
        for nome, qtd in app.resumo_estoque(self.doacoes):
            self.tab_estoque.insert("", "end", values=(nome, qtd))


def main():
    raiz = tk.Tk()
    Janela(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    main()
