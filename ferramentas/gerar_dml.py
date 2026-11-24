"""
gerar_dml.py - Gera o USUPORT_DML.sql a partir da planilha da PRF.

Lê a planilha acidentes2024_todas_causas_tipos_Usuport.xlsx, respeita o limite de
300 linhas do trabalho (só acidentes completos), separa os dados nas tabelas do
modelo normalizado (sem repetir informação) e escreve os INSERTs.
A parte do atendimento (ASSOCIADO, ATENDENTE, STATUS_CHAMADO, CHAMADO e
HISTORICO_ATENDIMENTO) não existe na planilha: é copiada do arquivo
sql/dados_ficticios.sql, sem alteração.

Como usar (na pasta Usuporte):
  python ferramentas/gerar_dml.py
Depois, em um banco recém-criado pelo DDL:
  python ferramentas/carregar_sql.py sql/USUPORT_DML.sql
"""
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent  # pasta Usuporte (este arquivo está em ferramentas/)
PLANILHA = RAIZ / "dados" / "acidentes2024_todas_causas_tipos_Usuport.xlsx"
FICTICIOS = RAIZ / "sql" / "dados_ficticios.sql"
SAIDA = RAIZ / "sql" / "USUPORT_DML.sql"
LINHAS_POR_INSERT = 50  # quebra INSERTs grandes em blocos menores, mais fáceis de ler
LIMITE_LINHAS = 300     # limite do trabalho: no máximo 300 linhas da planilha na carga

# Centro aproximado de cada UF (latitude, longitude). Usado só para corrigir as coordenadas
# da planilha, que vieram sem a vírgula decimal (ex.: -2272935968 = -22,72935968).
CENTRO_UF = {
    "AC": (-9.0, -70.5), "AL": (-9.6, -36.6), "AP": (1.4, -51.8), "AM": (-4.2, -64.6),
    "BA": (-12.5, -41.7), "CE": (-5.2, -39.5), "DF": (-15.8, -47.9), "ES": (-19.6, -40.7),
    "GO": (-16.0, -49.6), "MA": (-5.0, -45.3), "MT": (-12.9, -55.9), "MS": (-20.5, -54.6),
    "MG": (-18.5, -44.6), "PA": (-4.0, -52.0), "PB": (-7.2, -36.8), "PR": (-24.6, -51.6),
    "PE": (-8.4, -37.9), "PI": (-7.7, -42.7), "RJ": (-22.3, -42.7), "RN": (-5.8, -36.6),
    "RS": (-29.7, -53.2), "RO": (-10.9, -62.8), "RR": (2.1, -61.4), "SC": (-27.2, -50.5),
    "SP": (-22.3, -48.7), "SE": (-10.6, -37.4), "TO": (-10.2, -48.3),
}


# =====================================================================================
# Conversões de valores da planilha
# =====================================================================================
def vazio(v):
    """True para células vazias (NaN/None) da planilha."""
    return v is None or (isinstance(v, float) and pd.isna(v))


def coordenada(inteiro, centro):
    """
    Recoloca a vírgula decimal: tenta 1 ou 2 dígitos antes da vírgula e fica com o
    valor mais perto do centro da UF. Ex.: -51282644 no PI -> -5.1282644 (e não -51.28).
    """
    sinal = -1 if inteiro < 0 else 1
    digitos = str(abs(int(inteiro)))
    candidatos = [sinal * int(digitos) / 10 ** (len(digitos) - k) for k in (1, 2)]
    return round(min(candidatos, key=lambda v: abs(v - centro)), 7)


def sql(v):
    """Converte um valor Python no texto SQL correspondente (NULL, número ou 'texto')."""
    if vazio(v):
        return "NULL"
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return f"{v:.7f}".rstrip("0").rstrip(".")
    return "'" + str(v).replace("'", "''") + "'"  # aspas simples dobradas = escape do SQL


def inteiro(v):
    return None if vazio(v) else int(v)


# =====================================================================================
# Normalização: planilha (1 linha = acidente x pessoa x causa x tipo) -> tabelas
# =====================================================================================
def montar_tabelas(df):
    t = {nome: [] for nome in ["LOCALIZACAO", "UNIDADE_POLICIAL", "CONDICAO_VIA_AMBIENTE",
                               "CAUSA_ACIDENTE", "TIPO_ACIDENTE", "ACIDENTE", "PESSOA",
                               "VEICULO", "ENVOLVIMENTO", "ACIDENTE_CAUSA", "ACIDENTE_TIPO"]}

    # Tabelas de domínio: um id para cada valor diferente, em ordem alfabética
    causas = {c: i for i, c in enumerate(sorted(df["causa_acidente"].dropna().unique()), 1)}
    tipos = {c: i for i, c in enumerate(sorted(df["tipo_acidente"].dropna().unique()), 1)}
    t["CAUSA_ACIDENTE"] = [(i, c) for c, i in causas.items()]
    t["TIPO_ACIDENTE"] = [(i, c) for c, i in tipos.items()]

    unidades, condicoes = {}, {}  # valor -> id (reaproveita quando já existe)
    pessoas_vistas, veiculos_vistos = set(), set()

    # Um acidente por vez, na ordem em que aparece na planilha
    for id_acidente, linhas in df.groupby("id", sort=False):
        # Dados do acidente se repetem em todas as linhas dele. bfill() pega, em cada coluna,
        # o primeiro valor preenchido (há linhas com células vazias, ex.: classificação do 571789).
        p = linhas.bfill().iloc[0]

        # LOCALIZACAO: uma por acidente
        id_loc = len(t["LOCALIZACAO"]) + 1
        lat_c, lon_c = CENTRO_UF[p["uf"]]
        t["LOCALIZACAO"].append((id_loc, p["uf"], int(p["br"]), float(p["km"]), p["municipio"],
                                 coordenada(p["latitude"], lat_c), coordenada(p["longitude"], lon_c)))

        # UNIDADE_POLICIAL e CONDICAO_VIA_AMBIENTE: sem repetir combinações iguais
        chave_un = (p["regional"], p["delegacia"], p["uop"])
        if chave_un not in unidades:
            unidades[chave_un] = len(unidades) + 1
            t["UNIDADE_POLICIAL"].append((unidades[chave_un], *chave_un))
        chave_cond = (p["condicao_metereologica"], p["tipo_pista"], p["tracado_via"], p["uso_solo"] == "Sim")
        if chave_cond not in condicoes:
            condicoes[chave_cond] = len(condicoes) + 1
            t["CONDICAO_VIA_AMBIENTE"].append((condicoes[chave_cond], *chave_cond))

        # Vítimas do acidente: soma de cada pessoa uma única vez (a pessoa se repete
        # em várias linhas, uma para cada causa/tipo do acidente)
        por_pessoa = linhas.drop_duplicates("pesid")
        vitimas = [int(por_pessoa[c].fillna(0).sum())
                   for c in ("ilesos", "feridos_leves", "feridos_graves", "mortos")]
        # Classificação vazia na planilha (só o 571789): deduz pela regra da PRF
        classificacao = p["classificacao_acidente"]
        if vazio(classificacao):
            ilesos, leves, graves, mortos = vitimas
            classificacao = ("Com Vítimas Fatais" if mortos else
                             "Com Vítimas Feridas" if leves or graves else "Sem Vítimas")
        t["ACIDENTE"].append((int(id_acidente), p["data_inversa"].strftime("%Y-%m-%d"), str(p["horario"]),
                              classificacao, p["fase_dia"], p["sentido_via"], *vitimas,
                              id_loc, unidades[chave_un], condicoes[chave_cond]))

        # VEICULO, PESSOA e ENVOLVIMENTO (quem estava no acidente e em qual veículo)
        for _, l in linhas.drop_duplicates("id_veiculo").iterrows():
            idv = inteiro(l["id_veiculo"])
            if idv is not None and idv not in veiculos_vistos:
                veiculos_vistos.add(idv)
                ano = inteiro(l["ano_fabricacao_veiculo"]) or None  # ano 0 na planilha = não informado
                t["VEICULO"].append((idv, int(id_acidente), l["tipo_veiculo"], l["marca"], ano))
        for _, l in por_pessoa.iterrows():
            pesid = inteiro(l["pesid"])
            if pesid is None:
                continue
            if pesid not in pessoas_vistas:
                pessoas_vistas.add(pesid)
                t["PESSOA"].append((pesid, inteiro(l["idade"]), l["sexo"]))
            t["ENVOLVIMENTO"].append((int(id_acidente), pesid, inteiro(l["id_veiculo"]),
                                      l["tipo_envolvido"], l["estado_fisico"]))

        # ACIDENTE_CAUSA: cada causa uma vez; é principal se alguma linha disser "Sim"
        for causa, g in linhas.groupby("causa_acidente", sort=False):
            t["ACIDENTE_CAUSA"].append((int(id_acidente), causas[causa], bool((g["causa_principal"] == "Sim").any())))
        # ACIDENTE_TIPO: o tipo de cada ordem (1º, 2º, ...)
        for ordem, g in linhas.groupby("ordem_tipo_acidente", sort=False):
            t["ACIDENTE_TIPO"].append((int(id_acidente), int(ordem), tipos[g["tipo_acidente"].iloc[0]]))

    return t


COLUNAS = {
    "LOCALIZACAO": "id_localizacao, uf, br, km, municipio, latitude, longitude",
    "UNIDADE_POLICIAL": "id_unidade_policial, regional, delegacia, uop",
    "CONDICAO_VIA_AMBIENTE": "id_condicao_via_ambiente, condicao_meteorologica, tipo_pista, tracado_via, uso_solo",
    "CAUSA_ACIDENTE": "id_causa_acidente, causa_acidente",
    "TIPO_ACIDENTE": "id_tipo_acidente, tipo_acidente",
    "ACIDENTE": "id_acidente, data_inversa, horario, classificacao_acidente, fase_dia, sentido_via, "
                "ilesos, feridos_leves, feridos_graves, mortos, id_localizacao, id_unidade_policial, "
                "id_condicao_via_ambiente",
    "PESSOA": "pesid, idade, sexo",
    "VEICULO": "id_veiculo, id_acidente, tipo_veiculo, marca, ano_fabricacao_veiculo",
    "ENVOLVIMENTO": "id_acidente, pesid, id_veiculo, tipo_envolvido, estado_fisico",
    "ACIDENTE_CAUSA": "id_acidente, id_causa_acidente, causa_principal",
    "ACIDENTE_TIPO": "id_acidente, ordem_tipo_acidente, id_tipo_acidente",
}


def selecionar_linhas(df, limite):
    """
    Pega acidentes INTEIROS, na ordem da planilha, até o próximo não caber no limite.
    Assim nenhum acidente fica pela metade (sem alguma pessoa, causa ou tipo).
    """
    escolhidos, total = [], 0
    for id_acidente, qtd in df.groupby("id", sort=False).size().items():
        if total + qtd > limite:
            break
        escolhidos.append(id_acidente)
        total += qtd
    return df[df["id"].isin(escolhidos)]


def inserts(tabela, linhas):
    """Escreve os INSERTs de uma tabela, em blocos de LINHAS_POR_INSERT linhas."""
    texto = [f"-- {tabela}"]
    for i in range(0, len(linhas), LINHAS_POR_INSERT):
        bloco = linhas[i:i + LINHAS_POR_INSERT]
        texto.append(f"INSERT INTO {tabela} ({COLUNAS[tabela]}) VALUES")
        texto.append(",\n".join("(" + ", ".join(sql(v) for v in l) + ")" for l in bloco) + ";")
    return "\n".join(texto) + "\n"


def main():
    planilha = pd.read_excel(PLANILHA)
    df = selecionar_linhas(planilha, LIMITE_LINHAS)
    tabelas = montar_tabelas(df)

    cabecalho = (
        "-- USUPORT | DML - carga inicial (somente INSERTs)\n"
        f"-- Origem: {PLANILHA.stem} ({len(planilha)} linhas na planilha)\n"
        f"-- Carga: {len(tabelas['ACIDENTE'])} acidentes completos "
        f"({len(df)} linhas da planilha, limite de {LIMITE_LINHAS})\n"
        "-- Arquivo gerado pelo gerar_dml.py (nao edite a mao: altere a planilha e gere de novo).\n"
        "-- Execute depois do USUPORT_DDL_FINAL.sql, em banco vazio.\n"
        "-- Todos os INSERTs rodam em uma unica transacao (COMMIT ao final).\n"
        "-- Os exemplos de UPDATE e DELETE ficam em USUPORT_DML_UPDATE_DELETE.sql (rodar na apresentacao).\n"
        "USE usuport;\nSET NAMES utf8mb4;\nSET FOREIGN_KEY_CHECKS = 1;\nSTART TRANSACTION;\n"
    )
    partes = [cabecalho] + [inserts(nome, linhas) for nome, linhas in tabelas.items()]
    partes.append(FICTICIOS.read_text(encoding="utf-8").strip() + "\n\nCOMMIT;\n")
    SAIDA.write_text("\n".join(partes), encoding="utf-8")

    for nome, linhas in tabelas.items():
        print(f"{nome:<24} {len(linhas)}")
    print(f"Gerado: {SAIDA.name}")


if __name__ == "__main__":
    main()
