"""
carregar_sql.py - Executa um arquivo .sql no MariaDB da VM Alpine, a partir do Windows.

Serve para rodar o teste_provisorio.sql agora e, depois, o DDL (Radija) e o DML (Lucas).

Como usar (no Prompt de Comando, na pasta do projeto):
  python carregar_sql.py teste_provisorio.sql
O programa pergunta o IP, o usuário e a senha.
"""
import getpass
import sys

import pymysql


def comandos_do_arquivo(caminho):
    """
    Lê o .sql, ignora as linhas de comentário '--' e separa os comandos pelo ';'.
    Um ';' dentro de um texto entre aspas (ex.: 'Interseção de Vias;Reta')
    NÃO separa comandos.
    """
    with open(caminho, encoding="utf-8-sig") as f:
        texto = "".join(l for l in f if not l.strip().startswith("--"))

    comandos, atual, aspas = [], [], None
    i = 0
    while i < len(texto):
        c = texto[i]
        if aspas:                                   # dentro de um texto
            atual.append(c)
            if c == "\\" and i + 1 < len(texto):    # caractere escapado: \'
                atual.append(texto[i + 1]); i += 1
            elif c == aspas:
                if i + 1 < len(texto) and texto[i + 1] == aspas:  # aspas dobradas: ''
                    atual.append(texto[i + 1]); i += 1
                else:
                    aspas = None
        elif c in ("'", '"', "`"):                  # começo de um texto
            aspas = c
            atual.append(c)
        elif c == ";":                              # fim de um comando
            comandos.append("".join(atual).strip())
            atual = []
        else:
            atual.append(c)
        i += 1
    comandos.append("".join(atual).strip())
    return [c for c in comandos if c]


def main():
    if len(sys.argv) != 2:
        print("Uso: python carregar_sql.py arquivo.sql")
        sys.exit(1)

    host = input("IP do Alpine: ").strip()
    usuario = input("Usuário [usuport_app]: ").strip() or "usuport_app"
    senha = getpass.getpass("Senha: ")  # não aparece na tela enquanto digita

    con = pymysql.connect(host=host, port=3306, user=usuario, password=senha,
                          database="usuport", charset="utf8mb4")
    try:
        with con.cursor() as cur:
            for i, comando in enumerate(comandos_do_arquivo(sys.argv[1]), start=1):
                cur.execute(comando)
                print(f"[{i}] ok: {comando.splitlines()[0][:70]}")
        con.commit()
        print("\nScript executado com sucesso.")
    except pymysql.err.Error as e:
        con.rollback()
        print(f"\nErro no comando [{i}]: {e}")
    finally:
        con.close()


if __name__ == "__main__":
    main()
