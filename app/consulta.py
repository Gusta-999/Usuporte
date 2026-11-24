"""
consulta.py - Tela de CONSULTA (Read) dos chamados da USUPORT, em Streamlit.
Versão para o modelo oficial do projeto (USUPORT_DDL_FINAL.sql + USUPORT_DML.sql).

Arquitetura (mesma do exemplo do professor):
  [Navegador + este programa no Windows]  --- TCP, porta 3306 --->  [VM Alpine no VirtualBox: MariaDB]

Como rodar (no Windows, no Prompt de Comando ou PowerShell, na pasta Usuporte):
  python -m pip install -r requirements.txt
  python -m streamlit run app/consulta.py

As outras telas (cadastro, agendamento e exclusão) ficam em app/pages/ e aparecem
sozinhas no menu lateral.

O IP do Alpine e a senha são digitados na barra lateral.
Obs.: no MariaDB da VM (Linux) os nomes de tabela diferenciam maiúsculas,
por isso as tabelas aparecem em MAIÚSCULAS, exatamente como no DDL.
"""
from datetime import date

import pandas as pd
import pymysql
import streamlit as st

from conexao import barra_conexao, selecionar

TABELAS_DO_PROJETO = {
    "ASSOCIADO", "ATENDENTE", "STATUS_CHAMADO", "CHAMADO", "HISTORICO_ATENDIMENTO",
    "ACIDENTE", "LOCALIZACAO", "ACIDENTE_CAUSA", "CAUSA_ACIDENTE", "ACIDENTE_TIPO", "TIPO_ACIDENTE",
}

# Códigos de prioridade gravados em CHAMADO.prioridade
PRIORIDADES = {"B": "Baixa", "M": "Média", "A": "Alta", "C": "Crítica"}

# Status que contam como "em aberto" nos indicadores
STATUS_EM_ABERTO = ("Aberto", "Em Andamento", "Aguardando Cliente")


# =====================================================================================
# 1. CONSULTA PRINCIPAL: chamados com JOIN (mostra nomes em vez de IDs)
#    LEFT JOIN em ATENDENTE e ACIDENTE: um chamado pode não ter atendente
#    nem acidente vinculado (colunas NULL). O WHERE é montado conforme os filtros.
# =====================================================================================
def buscar_chamados(con, status, prioridades, tipos_associado, periodo, busca):
    sql = """
        SELECT c.id_chamado                              AS id,
               c.titulo                                  AS titulo,
               a.nome                                    AS associado,
               a.tipo                                    AS tipo_associado,
               s.descricao                               AS status,
               c.prioridade                              AS prioridade,
               COALESCE(t.nome, '(sem atendente)')       AS atendente,
               c.data_abertura                           AS abertura,
               c.data_fechamento                         AS fechamento,
               CASE WHEN ac.id_acidente IS NULL THEN '-'
                    ELSE CONCAT(l.municipio, '/', l.uf) END AS local_acidente
        FROM CHAMADO c
        JOIN ASSOCIADO       a  ON a.id_associado = c.id_associado
        JOIN STATUS_CHAMADO  s  ON s.id_status    = c.id_status
        LEFT JOIN ATENDENTE  t  ON t.id_atendente = c.id_atendente
        LEFT JOIN ACIDENTE   ac ON ac.id_acidente = c.id_acidente
        LEFT JOIN LOCALIZACAO l ON l.id_localizacao = ac.id_localizacao
        WHERE 1 = 1"""
    params = []

    def filtro_lista(coluna, valores):
        """Acrescenta 'AND coluna IN (%s, %s, ...)' quando a lista não está vazia."""
        nonlocal sql
        if valores:
            sql += f" AND {coluna} IN ({', '.join(['%s'] * len(valores))})"
            params.extend(valores)

    filtro_lista("s.descricao", status)
    filtro_lista("c.prioridade", prioridades)
    filtro_lista("a.tipo", tipos_associado)

    # Filtro por data de abertura: o date_input devolve uma tupla (início, fim)
    if isinstance(periodo, tuple) and len(periodo) == 2:
        sql += " AND DATE(c.data_abertura) BETWEEN %s AND %s"
        params += [periodo[0], periodo[1]]

    # Busca sem diferenciar acentos nem maiúsculas: com a collation unicode_ci,
    # "solicitação", "solicitacao" e "SOLICITACAO" encontram o mesmo chamado.
    if busca:
        sql += " AND c.titulo COLLATE utf8mb4_unicode_ci LIKE %s"
        params.append(f"%{busca}%")

    sql += " ORDER BY c.data_abertura DESC"
    return selecionar(con, sql, params)


def resumo_por_status(con):
    """GROUP BY + COUNT + AVG: quantos chamados por status e o tempo médio até o fechamento."""
    return selecionar(con, """
        SELECT s.descricao AS status,
               COUNT(c.id_chamado) AS chamados,
               ROUND(AVG(TIMESTAMPDIFF(HOUR, c.data_abertura, c.data_fechamento)) / 24, 1)
                   AS dias_ate_fechar
        FROM STATUS_CHAMADO s
        LEFT JOIN CHAMADO c ON c.id_status = s.id_status
        GROUP BY s.id_status, s.descricao
        ORDER BY s.id_status""")


# =====================================================================================
# 2. TELA
# =====================================================================================
def filtros(con):
    """Desenha os filtros na barra lateral e devolve os valores escolhidos."""
    st.sidebar.header("Filtros")
    opcoes_status = [l["descricao"] for l in
                     selecionar(con, "SELECT descricao FROM STATUS_CHAMADO ORDER BY id_status")]
    opcoes_tipo = [l["tipo"] for l in
                   selecionar(con, "SELECT DISTINCT tipo FROM ASSOCIADO ORDER BY tipo")]
    limites = selecionar(con, "SELECT MIN(DATE(data_abertura)) AS ini, MAX(DATE(data_abertura)) AS fim FROM CHAMADO")[0]

    status = st.sidebar.multiselect("Status", opcoes_status)
    prioridades = st.sidebar.multiselect("Prioridade", list(PRIORIDADES),
                                         format_func=lambda p: f"{p} - {PRIORIDADES[p]}")
    tipos = st.sidebar.multiselect("Tipo de associado", opcoes_tipo)
    periodo = st.sidebar.date_input(
        "Período de abertura",
        value=(limites["ini"] or date.today(), limites["fim"] or date.today()),
        format="DD/MM/YYYY",
    )
    busca = st.sidebar.text_input("Buscar no título", help="Não diferencia acentos nem maiúsculas.").strip()
    return status, prioridades, tipos, periodo, busca


def detalhe_chamado(con, id_chamado):
    """Mostra o chamado escolhido, o acidente vinculado e o histórico de atendimento."""
    c = selecionar(con, """
        SELECT c.titulo, c.descricao, c.prioridade, c.data_abertura, c.data_fechamento,
               c.id_acidente, s.descricao AS status, a.nome AS associado, a.email, a.telefone
        FROM CHAMADO c
        JOIN STATUS_CHAMADO s ON s.id_status = c.id_status
        JOIN ASSOCIADO a      ON a.id_associado = c.id_associado
        WHERE c.id_chamado = %s""", (id_chamado,))[0]

    fechado = f" · fechado em {c['data_fechamento']:%d/%m/%Y %H:%M}" if c["data_fechamento"] else ""
    st.markdown(f"**{c['titulo']}**  \n"
                f"Status: `{c['status']}` · Prioridade: `{PRIORIDADES.get(c['prioridade'], c['prioridade'])}` · "
                f"aberto em {c['data_abertura']:%d/%m/%Y %H:%M}{fechado}")
    st.write(c["descricao"])
    st.caption(f"Associado: {c['associado']} · {c['email']} · {c['telefone']}")

    # Acidente vinculado (dados da planilha da PRF)
    st.markdown("**Acidente vinculado**")
    if c["id_acidente"] is None:
        st.caption("Este chamado não está ligado a nenhum acidente.")
    else:
        ac = selecionar(con, """
            SELECT ac.id_acidente, ac.data_inversa, ac.horario, ac.classificacao_acidente,
                   ac.ilesos, ac.feridos_leves, ac.feridos_graves, ac.mortos,
                   l.municipio, l.uf, l.br, l.km,
                   (SELECT ca.causa_acidente FROM ACIDENTE_CAUSA x
                      JOIN CAUSA_ACIDENTE ca ON ca.id_causa_acidente = x.id_causa_acidente
                     WHERE x.id_acidente = ac.id_acidente AND x.causa_principal = 1
                     LIMIT 1) AS causa_principal,
                   (SELECT GROUP_CONCAT(ta.tipo_acidente ORDER BY x.ordem_tipo_acidente SEPARATOR ', ')
                      FROM ACIDENTE_TIPO x
                      JOIN TIPO_ACIDENTE ta ON ta.id_tipo_acidente = x.id_tipo_acidente
                     WHERE x.id_acidente = ac.id_acidente) AS tipos
            FROM ACIDENTE ac
            JOIN LOCALIZACAO l ON l.id_localizacao = ac.id_localizacao
            WHERE ac.id_acidente = %s""", (c["id_acidente"],))[0]
        # O PyMySQL devolve TIME como timedelta: converte para HH:MM
        minutos = int(ac["horario"].total_seconds() // 60)
        hora = f"{minutos // 60:02d}:{minutos % 60:02d}"
        st.markdown(
            f"Acidente **{ac['id_acidente']}** · {ac['data_inversa']:%d/%m/%Y} às {hora} · "
            f"BR-{ac['br']}, km {float(ac['km']):g} · {ac['municipio']}/{ac['uf']}  \n"
            f"Classificação: {ac['classificacao_acidente']} · Tipos: {ac['tipos'] or '-'}  \n"
            f"Causa principal: {ac['causa_principal'] or '-'}  \n"
            f"Vítimas: {ac['ilesos']} ilesos, {ac['feridos_leves']} feridos leves, "
            f"{ac['feridos_graves']} feridos graves, {ac['mortos']} mortos"
        )

    # Histórico de atendimento
    st.markdown("**Histórico de atendimento**")
    historico = selecionar(con, """
        SELECT h.data_hora AS quando, COALESCE(t.nome, '-') AS atendente, h.descricao
        FROM HISTORICO_ATENDIMENTO h
        LEFT JOIN ATENDENTE t ON t.id_atendente = h.id_atendente
        WHERE h.id_chamado = %s
        ORDER BY h.data_hora""", (id_chamado,))
    if historico:
        st.dataframe(historico, hide_index=True, width="stretch",
                     column_config={"quando": st.column_config.DatetimeColumn("quando", format="DD/MM/YYYY HH:mm")})
    else:
        st.caption("Este chamado ainda não tem registros de atendimento.")


def tela_consulta(con):
    chamados = pd.DataFrame(buscar_chamados(con, *filtros(con)))

    # Indicadores no topo
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Chamados encontrados", len(chamados))
    if not chamados.empty:
        col2.metric("Em aberto", int(chamados["status"].isin(STATUS_EM_ABERTO).sum()))
        col3.metric("Ligados a acidente", int((chamados["local_acidente"] != "-").sum()))
        col4.metric("Prioridade alta ou crítica", int(chamados["prioridade"].isin(["A", "C"]).sum()))

    # Tabela de resultados
    st.subheader("Chamados")
    if chamados.empty:
        st.info("Nenhum chamado encontrado com esses filtros.")
    else:
        chamados["prioridade"] = chamados["prioridade"].map(lambda p: PRIORIDADES.get(p, p))
        st.dataframe(
            chamados, hide_index=True, width="stretch",
            column_config={
                "abertura": st.column_config.DatetimeColumn("abertura", format="DD/MM/YYYY HH:mm"),
                "fechamento": st.column_config.DatetimeColumn("fechamento", format="DD/MM/YYYY HH:mm"),
            },
        )

    # Resumo por status (GROUP BY, COUNT e AVG)
    st.subheader("Resumo por status")
    st.dataframe(resumo_por_status(con), hide_index=True, width="stretch",
                 column_config={"dias_ate_fechar": st.column_config.NumberColumn(
                     "média de dias até fechar", format="%.1f")})

    # Detalhe de um chamado
    if not chamados.empty:
        st.subheader("Detalhe do chamado")
        titulos = dict(zip(chamados["id"], chamados["titulo"]))
        id_escolhido = st.selectbox("Escolha um chamado", list(titulos),
                                    format_func=lambda i: f"#{i} - {titulos[i]}")
        detalhe_chamado(con, int(id_escolhido))


def main():
    st.set_page_config(page_title="USUPORT - Consulta", page_icon="⚓", layout="wide")
    st.title("USUPORT - Consulta de Chamados")
    st.caption("Windows (Streamlit) → rede → VirtualBox (Alpine Linux, MariaDB)")

    con = barra_conexao()
    if con is None:
        st.info("Preencha o IP do Alpine e a senha na barra lateral e clique em Conectar.")
        return

    # Confere se o DDL oficial já foi executado no banco
    existentes = {list(l.values())[0] for l in selecionar(con, "SHOW TABLES")}
    faltam = TABELAS_DO_PROJETO - existentes
    if faltam:
        st.warning(f"Faltam tabelas no banco: {', '.join(sorted(faltam))}. "
                   "Execute o USUPORT_DDL_FINAL.sql e depois o USUPORT_DML.sql.")
        return

    # Um erro do banco vira mensagem na tela, sem derrubar o programa
    try:
        tela_consulta(con)
    except pymysql.err.Error as e:
        con.rollback()
        st.error(f"Erro do banco: {e}")


if __name__ == "__main__":
    main()
