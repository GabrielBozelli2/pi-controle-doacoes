#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Controle de Doacoes e Fila de Distribuicao de Alimentos.

Projeto Integrador - Laboratorio de Programacao (UNISA).
Linguagem: Python 3 (testado na versao 3.13), somente biblioteca padrao.

Estruturas e algoritmos implementados manualmente (sem sorted(), sort(),
bisect ou collections.deque):
  - registros (dataclass) em listas;
  - busca sequencial e busca binaria, ambas com contador de comparacoes;
  - ordenacao por insercao (estavel) com chave escolhida pelo usuario;
  - fila FIFO por lista encadeada (inicio e fim);
  - persistencia em arquivos CSV, com validacao de entradas.
"""

import csv
import os
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime

PASTA = os.path.dirname(os.path.abspath(__file__))
ARQ_DOACOES = os.path.join(PASTA, "doacoes.csv")
ARQ_FILA = os.path.join(PASTA, "fila.csv")
FORMATO_DATA = "%d/%m/%Y"


# ----------------------------------------------------------------------
# Registros
# ----------------------------------------------------------------------
@dataclass
class Doacao:
    codigo: int
    alimento: str
    quantidade: int
    data: date


@dataclass
class Pedido:
    senha: int
    familia: str
    pessoas: int
    alimento: str


def normalizar(texto):
    """Padroniza o texto para comparar e ordenar: sem espacos extras, sem
    acentos e em minusculas ("Feijao", "feijão " e "FEIJAO" ficam iguais)."""
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", texto) if not unicodedata.combining(c)
    )
    return " ".join(sem_acento.split()).casefold()


# ----------------------------------------------------------------------
# Busca sequencial e binaria (retornam indice e numero de comparacoes)
# ----------------------------------------------------------------------
def busca_sequencial(lista, codigo):
    """Percorre a lista do inicio ao fim ate achar o codigo."""
    comparacoes = 0
    for i in range(len(lista)):
        comparacoes += 1
        if lista[i].codigo == codigo:
            return i, comparacoes
    return -1, comparacoes


def busca_binaria(lista, codigo):
    """Exige a lista ordenada por codigo (crescente)."""
    esq, dir_ = 0, len(lista) - 1
    comparacoes = 0
    while esq <= dir_:
        meio = (esq + dir_) // 2
        comparacoes += 1
        if lista[meio].codigo == codigo:
            return meio, comparacoes
        if lista[meio].codigo < codigo:
            esq = meio + 1
        else:
            dir_ = meio - 1
    return -1, comparacoes


def buscar_por_alimento(lista, termo):
    """Busca sequencial que devolve todas as doacoes cujo alimento contem o termo."""
    termo = normalizar(termo)
    achados = []
    for d in lista:
        if termo in normalizar(d.alimento):
            achados.append(d)
    return achados


# ----------------------------------------------------------------------
# Ordenacao por insercao (estavel)
# ----------------------------------------------------------------------
CHAVES = {
    "codigo": lambda d: d.codigo,
    "alimento": lambda d: normalizar(d.alimento),
    "quantidade": lambda d: d.quantidade,
    "data": lambda d: d.data,
}


def ordenar_insercao(lista, chave="codigo"):
    """Ordena a propria lista de forma crescente; devolve o n. de comparacoes."""
    f = CHAVES[chave]
    comparacoes = 0
    for i in range(1, len(lista)):
        atual = lista[i]
        j = i - 1
        while j >= 0:
            comparacoes += 1
            if f(lista[j]) > f(atual):
                lista[j + 1] = lista[j]
                j -= 1
            else:
                break
        lista[j + 1] = atual
    return comparacoes


def esta_ordenada(lista, chave="codigo"):
    f = CHAVES[chave]
    for i in range(1, len(lista)):
        if f(lista[i - 1]) > f(lista[i]):
            return False
    return True


# ----------------------------------------------------------------------
# Fila FIFO por lista encadeada
# ----------------------------------------------------------------------
class No:
    def __init__(self, pedido):
        self.pedido = pedido
        self.proximo = None


class Fila:
    def __init__(self):
        self.inicio = None
        self.fim = None
        self.tamanho = 0

    def vazia(self):
        return self.inicio is None

    def enfileirar(self, pedido):
        no = No(pedido)
        if self.fim is None:
            self.inicio = no
        else:
            self.fim.proximo = no
        self.fim = no
        self.tamanho += 1

    def desenfileirar(self):
        if self.inicio is None:
            return None
        no = self.inicio
        self.inicio = no.proximo
        if self.inicio is None:
            self.fim = None
        self.tamanho -= 1
        return no.pedido

    def primeiro(self):
        return None if self.inicio is None else self.inicio.pedido

    def pedidos(self):
        """Lista dos pedidos na ordem de atendimento."""
        resultado = []
        atual = self.inicio
        while atual is not None:
            resultado.append(atual.pedido)
            atual = atual.proximo
        return resultado


# ----------------------------------------------------------------------
# Regras de negocio
# ----------------------------------------------------------------------
def estoque_de(doacoes, alimento):
    alvo = normalizar(alimento)
    total = 0
    for d in doacoes:
        if normalizar(d.alimento) == alvo:
            total += d.quantidade
    return total


def resumo_estoque(doacoes):
    """Total por alimento, em ordem alfabetica (usa a ordenacao propria)."""
    totais, nomes = {}, {}
    for d in doacoes:
        chave = normalizar(d.alimento)
        nomes.setdefault(chave, d.alimento)
        totais[chave] = totais.get(chave, 0) + d.quantidade
    linhas = [Doacao(0, nomes[k], qtd, date.min) for k, qtd in totais.items()]
    ordenar_insercao(linhas, "alimento")
    return [(d.alimento, d.quantidade) for d in linhas]


def retirar_do_estoque(doacoes, alimento, quantidade):
    """Retira a quantidade comecando pelas doacoes mais antigas (validade/giro).

    Devolve True se havia estoque suficiente; caso contrario nada e alterado.
    """
    if estoque_de(doacoes, alimento) < quantidade:
        return False
    alvo = normalizar(alimento)
    candidatas = [d for d in doacoes if normalizar(d.alimento) == alvo]
    ordenar_insercao(candidatas, "data")
    falta = quantidade
    for d in candidatas:
        if falta == 0:
            break
        usado = min(d.quantidade, falta)
        d.quantidade -= usado
        falta -= usado
    doacoes[:] = [d for d in doacoes if d.quantidade > 0]
    return True


def atender_proximo(fila, doacoes):
    """Atende o primeiro da fila se houver estoque (cada pessoa recebe 1 unidade).

    Devolve (pedido, mensagem). Se nao houver estoque, o pedido continua na
    frente da fila, preservando a ordem de chegada.
    """
    pedido = fila.primeiro()
    if pedido is None:
        return None, "A fila esta vazia."
    if retirar_do_estoque(doacoes, pedido.alimento, pedido.pessoas):
        fila.desenfileirar()
        return pedido, "Atendimento concluido."
    disp = estoque_de(doacoes, pedido.alimento)
    return None, (
        f"Estoque insuficiente de '{pedido.alimento}': "
        f"necessario {pedido.pessoas}, disponivel {disp}."
    )


# ----------------------------------------------------------------------
# Persistencia em CSV
# ----------------------------------------------------------------------
def salvar_doacoes(doacoes, caminho=ARQ_DOACOES):
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["codigo", "alimento", "quantidade", "data"])
        for d in doacoes:
            w.writerow([d.codigo, d.alimento, d.quantidade, d.data.strftime(FORMATO_DATA)])


def carregar_doacoes(caminho=ARQ_DOACOES):
    """Le o CSV; linhas invalidas ou codigos repetidos sao descartados e contados."""
    doacoes, erros, vistos = [], 0, set()
    if not os.path.exists(caminho):
        return doacoes, erros
    with open(caminho, newline="", encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            try:
                d = Doacao(
                    int(linha["codigo"]),
                    " ".join(linha["alimento"].split()),
                    int(linha["quantidade"]),
                    datetime.strptime(linha["data"], FORMATO_DATA).date(),
                )
                if d.codigo <= 0 or d.quantidade <= 0 or not d.alimento or d.codigo in vistos:
                    raise ValueError
                vistos.add(d.codigo)
                doacoes.append(d)
            except (ValueError, KeyError, TypeError, AttributeError):
                erros += 1
    return doacoes, erros


def salvar_fila(fila, caminho=ARQ_FILA):
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["senha", "familia", "pessoas", "alimento"])
        for p in fila.pedidos():
            w.writerow([p.senha, p.familia, p.pessoas, p.alimento])


def carregar_fila(caminho=ARQ_FILA):
    fila, erros = Fila(), 0
    if not os.path.exists(caminho):
        return fila, erros
    with open(caminho, newline="", encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            try:
                p = Pedido(
                    int(linha["senha"]),
                    " ".join(linha["familia"].split()),
                    int(linha["pessoas"]),
                    " ".join(linha["alimento"].split()),
                )
                if p.senha <= 0 or p.pessoas <= 0 or not p.familia or not p.alimento:
                    raise ValueError
                fila.enfileirar(p)
            except (ValueError, KeyError, TypeError, AttributeError):
                erros += 1
    return fila, erros


# ----------------------------------------------------------------------
# Conversao e validacao de entradas (usadas pelo menu e pela interface grafica)
# ----------------------------------------------------------------------
def converter_texto(bruto):
    valor = " ".join(bruto.split())
    if not valor:
        raise ValueError("Valor inválido: não pode ficar em branco.")
    return valor


def converter_inteiro(bruto, minimo=1, maximo=None):
    try:
        n = int(bruto.strip())
    except ValueError:
        raise ValueError("Valor inválido: digite um número inteiro.") from None
    if n < minimo or (maximo is not None and n > maximo):
        limite = f"entre {minimo} e {maximo}" if maximo is not None else f"maior ou igual a {minimo}"
        raise ValueError(f"Valor inválido: use um número {limite}.")
    return n


def converter_data(bruto):
    try:
        d = datetime.strptime(bruto.strip(), FORMATO_DATA).date()
    except ValueError:
        raise ValueError("Data inválida: use o formato dd/mm/aaaa.") from None
    if d > date.today():
        raise ValueError("Data inválida: não pode estar no futuro.")
    return d


def _ler(msg, conversor, *args):
    while True:
        try:
            return conversor(input(msg), *args)
        except ValueError as erro:
            print(" ", erro)


def ler_texto(msg):
    return _ler(msg, converter_texto)


def ler_inteiro(msg, minimo=1, maximo=None):
    return _ler(msg, converter_inteiro, minimo, maximo)


def ler_data(msg):
    return _ler(msg, converter_data)


# ----------------------------------------------------------------------
# Interface de menu
# ----------------------------------------------------------------------
def mostrar_doacoes(lista):
    if not lista:
        print("  (nenhuma doacao)")
        return
    print(f"  {'Codigo':>6}  {'Alimento':<20} {'Qtd':>5}  Data")
    for d in lista:
        print(f"  {d.codigo:>6}  {d.alimento:<20} {d.quantidade:>5}  {d.data.strftime(FORMATO_DATA)}")


def cadastrar_doacao(doacoes):
    codigo = ler_inteiro("Codigo do lote: ")
    if busca_sequencial(doacoes, codigo)[0] != -1:
        print("  Codigo ja cadastrado.")
        return
    alimento = ler_texto("Alimento: ")
    qtd = ler_inteiro("Quantidade (unidades ou kg): ")
    data = ler_data("Data da doacao (dd/mm/aaaa): ")
    doacoes.append(Doacao(codigo, alimento, qtd, data))
    print("  Doacao cadastrada.")


def menu_buscar(doacoes):
    print("  1) Sequencial por codigo  2) Binaria por codigo  3) Por nome do alimento")
    op = ler_inteiro("  Opcao: ", 1, 3)
    if op == 3:
        achados = buscar_por_alimento(doacoes, ler_texto("  Termo: "))
        mostrar_doacoes(achados)
        return
    codigo = ler_inteiro("  Codigo: ")
    if op == 1:
        i, c = busca_sequencial(doacoes, codigo)
    else:
        if not esta_ordenada(doacoes, "codigo"):
            print("  Lista fora de ordem: ordenando por codigo antes da busca binaria.")
            ordenar_insercao(doacoes, "codigo")
        i, c = busca_binaria(doacoes, codigo)
    if i == -1:
        print(f"  Codigo nao encontrado ({c} comparacoes).")
    else:
        print(f"  Encontrado na posicao {i} ({c} comparacoes):")
        mostrar_doacoes([doacoes[i]])


def menu_ordenar(doacoes):
    nomes = list(CHAVES)
    for n, nome in enumerate(nomes, 1):
        print(f"  {n}) {nome}")
    chave = nomes[ler_inteiro("  Ordenar por: ", 1, len(nomes)) - 1]
    c = ordenar_insercao(doacoes, chave)
    print(f"  Lista ordenada por {chave} ({c} comparacoes).")
    mostrar_doacoes(doacoes)


def registrar_pedido(fila, proxima_senha):
    familia = ler_texto("Nome da familia/responsavel: ")
    pessoas = ler_inteiro("Numero de pessoas: ", 1, 30)
    alimento = ler_texto("Alimento solicitado: ")
    p = Pedido(proxima_senha, familia, pessoas, alimento)
    fila.enfileirar(p)
    print(f"  Pedido registrado. Senha {p.senha}; posicao {fila.tamanho} na fila.")


def mostrar_fila(fila):
    if fila.vazia():
        print("  (fila vazia)")
        return
    print(f"  {'Pos':>3}  {'Senha':>5}  {'Familia':<20} {'Pessoas':>7}  Alimento")
    for pos, p in enumerate(fila.pedidos(), 1):
        print(f"  {pos:>3}  {p.senha:>5}  {p.familia:<20} {p.pessoas:>7}  {p.alimento}")


def menu():
    print("\n=== CONTROLE DE DOACOES E FILA DE DISTRIBUICAO ===")
    print(" 1 Cadastrar doacao        6 Registrar pedido na fila")
    print(" 2 Listar doacoes          7 Exibir fila")
    print(" 3 Buscar doacao           8 Atender proximo da fila")
    print(" 4 Ordenar doacoes         9 Resumo do estoque")
    print(" 0 Salvar e sair")


def main():
    doacoes, e1 = carregar_doacoes()
    fila, e2 = carregar_fila()
    if e1 or e2:
        print(f"Aviso: {e1 + e2} linha(s) invalida(s) ignorada(s) ao carregar os arquivos.")
    proxima_senha = max([p.senha for p in fila.pedidos()], default=0) + 1
    while True:
        menu()
        op = ler_inteiro("Opcao: ", 0, 9)
        if op == 0:
            salvar_doacoes(doacoes)
            salvar_fila(fila)
            print("Dados salvos. Ate logo!")
            break
        elif op == 1:
            cadastrar_doacao(doacoes)
        elif op == 2:
            mostrar_doacoes(doacoes)
        elif op == 3:
            menu_buscar(doacoes)
        elif op == 4:
            menu_ordenar(doacoes)
        elif op == 6:
            registrar_pedido(fila, proxima_senha)
            proxima_senha += 1
        elif op == 7:
            mostrar_fila(fila)
        elif op == 8:
            pedido, msg = atender_proximo(fila, doacoes)
            print(" ", msg)
            if pedido is not None:
                print(f"  Senha {pedido.senha} - {pedido.familia}: {pedido.pessoas} un. de {pedido.alimento}.")
        elif op == 9:
            for nome, qtd in resumo_estoque(doacoes):
                print(f"  {nome:<20} {qtd:>6}")
            if not doacoes:
                print("  (estoque vazio)")


if __name__ == "__main__":
    main()
