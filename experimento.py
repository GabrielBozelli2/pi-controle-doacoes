#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Experimento: busca sequencial x busca binaria por volume de registros.

Para cada volume N, gera N doacoes com codigos distintos embaralhados, ordena
por codigo (insercao propria para N pequeno; ver observacao) e sorteia 1000
codigos existentes (semente fixa). Mede comparacoes medias e tempo medio por busca.
"""

import random
import time
from datetime import date

import doacoes as app
from doacoes import Doacao

SEMENTE = 2026
BUSCAS = 1000
VOLUMES = (100, 1000, 10000)


def montar(n, rnd):
    codigos = rnd.sample(range(1, n * 10), n)
    lista = [Doacao(c, "Arroz", 1, date(2026, 10, 1)) for c in codigos]
    t0 = time.perf_counter()
    comp = app.ordenar_insercao(lista, "codigo")
    return lista, comp, time.perf_counter() - t0


def medir(funcao, lista, alvos):
    comparacoes = 0
    t0 = time.perf_counter()
    for a in alvos:
        i, c = funcao(lista, a)
        assert i != -1
        comparacoes += c
    tempo = time.perf_counter() - t0
    return comparacoes / len(alvos), tempo / len(alvos) * 1e6  # microssegundos


def main():
    rnd = random.Random(SEMENTE)
    print(f"Semente {SEMENTE}; {BUSCAS} buscas por volume; Python "
          f"{__import__('platform').python_version()}")
    print(f"{'N':>7} | {'comp.seq':>9} {'comp.bin':>9} | {'t.seq(us)':>10} {'t.bin(us)':>10} | "
          f"{'ordenacao: comp.':>16} {'tempo(ms)':>10}")
    for n in VOLUMES:
        lista, comp_ord, t_ord = montar(n, rnd)
        alvos = [rnd.choice(lista).codigo for _ in range(BUSCAS)]
        cs, ts = medir(app.busca_sequencial, lista, alvos)
        cb, tb = medir(app.busca_binaria, lista, alvos)
        print(f"{n:>7} | {cs:>9.1f} {cb:>9.2f} | {ts:>10.2f} {tb:>10.2f} | {comp_ord:>16} {t_ord*1000:>10.1f}")


if __name__ == "__main__":
    main()
