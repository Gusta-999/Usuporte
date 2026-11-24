"""
2_Agendamento.py - Tela de AGENDAMENTO de atendimentos da USUPORT.

Para um chamado em aberto, o atendente agenda (ou registra) um atendimento:
  - INSERT em HISTORICO_ATENDIMENTO (quem atende, quando e o que será/foi feito);
  - UPDATE em CHAMADO (atendente responsável, novo status e data de fechamento).

Os dois comandos rodam numa TRANSAÇÃO: ou os dois são gravados, ou nenhum.
Data/hora no futuro = atendimento agendado; no passado = atendimento já realizado.
"""
from datetime import date, datetime, time

import pymysql
import streamlit as st

from conexao import (barra_conexao, executar_transacao, guardar_mensagem,
                     mostrar_mensagem, selecionar)

# Status que encerram o chamado: ao escolher um deles, grava a data de fechamento
STATUS_FINAIS = ("Resolvido", "Fechado")
# Chamados nesses status não recebem novos atendimentos
STATUS_INATIVOS = ("Fechado", "Cancelado")


def chamados_ativos(con):
    """Chamados que ainda podem receber atendimento (não fechados nem cancelados)."""
    linhas = selecionar(con, """
        SELECT c.id_chamado, c.titulo, c.id_atendente, c.id_status, s.descricao AS status,
               a.nome AS associado
        FROM CHAMADO c
        JOIN STATUS_CHAMADO s ON s.id_status = c.id_status
        JOIN ASSOCIADO a      ON a.id_associado = c.id_associado
        WHERE s.descricao NOT IN (%s, %s)
        ORDER BY c.id_chamado""", STATUS_INATIVOS)
    return {l["id_chamado"]: l for l in linhas}


def formulario_agendamento(con, chamado):
    atendentes = {l["id_atendente"]: f"{l['nome']} - {l['setor']}" for l in
                  selecionar(con, "SELECT id_atendente, nome, setor FROM ATENDENTE ORDER BY nome")}
    status = {l["id_status"]: l["descricao"] for l in
              selecionar(con, "SELECT id_status, descricao FROM STATUS_CHAMADO ORDER BY id_status")}

    # Sugere o atendente atual do chamado (se houver) e mantém o status atual
    lista_atendentes = list(atendentes)
    indice_atendente = (lista_atendentes.index(chamado["id_atendente"])
                        if chamado["id_atendente"] in atendentes else 0)
    lista_status = list(status)

    with st.form("form_agendamento", clear_on_submit=True):
        id_atendente = st.selectbox("Atendente *", lista_atendentes, index=indice_atendente,
                                    format_func=atendentes.get)
        col1, col2 = st.columns(2)
        dia = col1.date_input("Data *", value=date.today(), format="DD/MM/YYYY")
        hora = col2.time_input("Hora *", value=time(9, 0), step=900)  # de 15 em 15 minutos
        descricao = st.text_area("O que será feito / foi feito *",
                                 placeholder="ex.: Ligar para o associado e confirmar os dados do acidente.")
        id_status = st.selectbox("Status do chamado após o atendimento", lista_status,
                                 index=lista_status.index(chamado["id_status"]), format_func=status.get)
        enviar = st.form_submit_button("Agendar atendimento", type="primary")

    if enviar:
        if not descricao.strip():
            st.error("Descreva o atendimento.")
            return
        data_hora = datetime.combine(dia, hora)  # junta a data e a hora num DATETIME

        # Se o novo status encerra o chamado, a data de fechamento é a do atendimento;
        # se o chamado for reaberto, a data de fechamento volta a ficar vazia (NULL).
        fechamento = data_hora if status[id_status] in STATUS_FINAIS else None

        ok, resultado = executar_transacao(con, [
            # 1) registra o atendimento no histórico
            ("""INSERT INTO HISTORICO_ATENDIMENTO (id_chamado, id_atendente, data_hora, descricao)
                VALUES (%s, %s, %s, %s)""",
             (chamado["id_chamado"], id_atendente, data_hora, descricao.strip())),
            # 2) atualiza o chamado: responsável, status e fechamento
            ("""UPDATE CHAMADO
                SET id_atendente = %s, id_status = %s, data_fechamento = %s
                WHERE id_chamado = %s""",
             (id_atendente, id_status, fechamento, chamado["id_chamado"])),
        ])
        if ok:
            quando = "agendado para" if data_hora > datetime.now() else "registrado em"
            guardar_mensagem(True, f"Atendimento do chamado #{chamado['id_chamado']} "
                                   f"{quando} {data_hora:%d/%m/%Y %H:%M}.")
        else:
            guardar_mensagem(False, resultado)
        st.rerun()


def agenda(con):
    """Próximos atendimentos agendados (data/hora a partir de agora), de todos os chamados."""
    st.subheader("Próximos atendimentos agendados")
    proximos = selecionar(con, """
        SELECT h.data_hora AS quando, c.id_chamado AS chamado, c.titulo,
               t.nome AS atendente, h.descricao
        FROM HISTORICO_ATENDIMENTO h
        JOIN CHAMADO   c ON c.id_chamado   = h.id_chamado
        JOIN ATENDENTE t ON t.id_atendente = h.id_atendente
        WHERE h.data_hora >= NOW()
        ORDER BY h.data_hora""")
    if proximos:
        st.dataframe(proximos, hide_index=True, width="stretch",
                     column_config={"quando": st.column_config.DatetimeColumn("quando", format="DD/MM/YYYY HH:mm")})
    else:
        st.caption("Nenhum atendimento agendado.")


def main():
    st.set_page_config(page_title="USUPORT - Agendamento", page_icon="⚓", layout="wide")
    st.title("USUPORT - Agendamento de atendimento")

    con = barra_conexao()
    if con is None:
        st.info("Preencha o IP do Alpine e a senha na barra lateral e clique em Conectar.")
        return

    mostrar_mensagem()

    try:
        chamados = chamados_ativos(con)
        if not chamados:
            st.info("Não há chamados em aberto para agendar.")
        else:
            id_chamado = st.selectbox(
                "Chamado", list(chamados),
                format_func=lambda i: f"#{i} - {chamados[i]['titulo']} · "
                                      f"{chamados[i]['associado']} · {chamados[i]['status']}")
            chamado = chamados[id_chamado]
            esquerda, direita = st.columns([3, 2])
            with esquerda:
                formulario_agendamento(con, chamado)
            with direita:
                # Histórico do chamado escolhido, para o atendente ver o que já foi feito
                st.markdown(f"**Histórico do chamado #{id_chamado}**")
                historico = selecionar(con, """
                    SELECT h.data_hora AS quando, t.nome AS atendente, h.descricao
                    FROM HISTORICO_ATENDIMENTO h
                    JOIN ATENDENTE t ON t.id_atendente = h.id_atendente
                    WHERE h.id_chamado = %s
                    ORDER BY h.data_hora""", (id_chamado,))
                if historico:
                    st.dataframe(historico, hide_index=True, width="stretch",
                                 column_config={"quando": st.column_config.DatetimeColumn(
                                     "quando", format="DD/MM/YYYY HH:mm")})
                else:
                    st.caption("Ainda sem atendimentos.")
        agenda(con)
    except pymysql.err.Error as e:
        con.rollback()
        st.error(f"Erro do banco: {e}")


main()
