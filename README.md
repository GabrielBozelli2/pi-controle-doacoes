# Sistema de Controle de Doações e Fila de Distribuição de Alimentos

Projeto Integrador – Laboratório de Programação (UNISA) – Engenharia de Software.
Programa em Python 3 (testado nas versões 3.12 e 3.13), somente biblioteca padrão. Não precisa instalar nada.

## Como executar

    python gui.py               # interface gráfica (programa principal)
    python test_doacoes.py -v   # 29 testes da lógica
    python test_gui.py -v       # 7 testes da interface (precisam de tela)
    python experimento.py       # busca sequencial x binária (100, 1.000 e 10.000 registros)
    python doacoes.py           # versão opcional em menu de texto

No Mac/Linux use `python3` no lugar de `python`.
No Windows e no Mac (instalador de python.org) a interface já vem junto com o Python.
No Linux/Ubuntu, se aparecer "No module named tkinter", instale com: `sudo apt install python3-tk`.

Os dados são salvos em `doacoes.csv` e `fila.csv`, na mesma pasta do programa.

## Arquivos

- `gui.py` – interface gráfica (Tkinter): abas Doações, Fila de distribuição e Estoque
- `doacoes.py` – lógica: registros, buscas, ordenação, fila FIFO, estoque, CSV e menu de texto
- `test_doacoes.py` / `test_gui.py` – testes automatizados (unittest)
- `experimento.py` – experimento da seção 3.5 do artigo
