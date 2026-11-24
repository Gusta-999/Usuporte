"""
3_Exclusao.py - Tela de EXCLUSÃO e INATIVAÇÃO (Delete) da USUPORT.

Chamado - duas opções:
  - INATIVAR: UPDATE do status para "Cancelado". O chamado e o histórico continuam no banco
    (é a opção recomendada: não se perde o registro do que aconteceu).
  - EXCLUIR: DELETE definitivo. Como HISTORICO_ATENDIMENTO aponta para CHAMADO (chave
    estrangeira), primeiro apaga o histórico (filho) e depois o chamado (pai), na mesma transação.

Associado - EXCLUIR: DELETE em ASSOCIADO. Se ele tiver chamados, a chave estrangeira
fk_chamado_associado impede (erro 1451) e a tela explica o motivo: é a integridade
referencial do banco protegendo os dados.
"""
import pymysql
import streamlit as st

from conexao import (barra_conexao, executar, executar_transacao, guardar_mensagem,
                     mostrar_mensagem, selecionar)


# =====================================================================================
# Chamado: inativar (cancelar) ou excluir
# =====================================================================================
def excluir_chamado(con):
    st.subheader("Chamado")
    chamados = {l["id_chamado"]: l for l in selecionar(con, """
        SELECT c.id_chamado, c.titulo, s.descricao AS status, a.nome AS associado,
               (SELECT COUNT(*) FROM HISTORICO_ATENDIMENTO h
                 WHERE h.id_chamado = c.id_chamado) AS atendimentos
        FROM CHAMADO c
        JOIN STATUS_CHAMADO s ON s.id_status = c.id_status
        JOIN ASSOCIADO a      ON a.id_associado = c.id_associado
        ORDER BY c.id_chamado""")}
    if not chamados:
        st.caption("Nenhum chamado cadastrado.")
        return

    id_chamado = st.selectbox("Chamado", list(chamados),
                              format_func=lambda i: f"#{i} - {chamados[i]['titulo']} ({chamados[i]['status']})")
    c = chamados[id_chamado]
    st.caption(f"Associado: {c['associado']} · Status atual: {c['status']} · "
               f"{c['atendimentos']} atendimento(s) no histórico")

    acao = st.radio("O que fazer?", ["Inativar (cancelar o chamado)", "Excluir definitivamente"],
                    help="Inativar mantém o chamado e o histórico no banco. "
                         "Excluir apaga os dois e não tem como desfazer.")
    # Confirmação: evita apagar por um clique acidental
    confirmado = st.checkbox(f"Confirmo a ação no chamado #{id_chamado}", key=f"conf_chamado_{id_chamado}")

    if st.button("Executar", type="primary", disabled=not confirmado, key="btn_chamado"):
        if acao.startswith("Inativar"):
            if c["status"] == "Cancelado":
                guardar_mensagem(False, f"O chamado #{id_chamado} já está cancelado.")
                st.rerun()
            # Inativação = UPDATE (o registro continua existindo).
            # O id do status "Cancelado" é buscado por subconsulta; a data de fechamento
            # só é preenchida se ainda estiver vazia (COALESCE).
            ok, resultado = executar(con, """
                UPDATE CHAMADO
                SET id_status = (SELECT id_status FROM STATUS_CHAMADO WHERE descricao = 'Cancelado'),
                    data_fechamento = COALESCE(data_fechamento, NOW())
                WHERE id_chamado = %s""", (id_chamado,))
            texto = f"Chamado #{id_chamado} inativado (status Cancelado)."
        else:
            # Exclusão = DELETE, respeitando a ordem das chaves estrangeiras:
            # primeiro o filho (HISTORICO_ATENDIMENTO), depois o pai (CHAMADO).
            ok, resultado = executar_transacao(con, [
                ("DELETE FROM HISTORICO_ATENDIMENTO WHERE id_chamado = %s", (id_chamado,)),
                ("DELETE FROM CHAMADO WHERE id_chamado = %s", (id_chamado,)),
            ])
            texto = f"Chamado #{id_chamado} excluído, com {c['atendimentos']} atendimento(s) do histórico."
        guardar_mensagem(ok, texto if ok else resultado)
        st.rerun()  # recarrega a lista de chamados


# =====================================================================================
# Associado: excluir (bloqueado pela FK se tiver chamados)
# =====================================================================================
def excluir_associado(con):
    st.subheader("Associado")
    associados = {l["id_associado"]: l for l in selecionar(con, """
        SELECT a.id_associado, a.nome, a.tipo, COUNT(c.id_chamado) AS chamados
        FROM ASSOCIADO a
        LEFT JOIN CHAMADO c ON c.id_associado = a.id_associado
        GROUP BY a.id_associado, a.nome, a.tipo
        ORDER BY a.nome""")}
    if not associados:
        st.caption("Nenhum associado cadastrado.")
        return

    id_associado = st.selectbox("Associado", list(associados),
                                format_func=lambda i: f"{associados[i]['nome']} ({associados[i]['tipo']})")
    a = associados[id_associado]
    if a["chamados"]:
        st.caption(f"⚠️ Este associado tem {a['chamados']} chamado(s). O banco vai impedir a exclusão "
                   "(chave estrangeira). Exclua os chamados dele antes.")
    else:
        st.caption("Este associado não tem chamados e pode ser excluído.")

    confirmado = st.checkbox(f"Confirmo a exclusão de {a['nome']}", key=f"conf_assoc_{id_associado}")
    if st.button("Excluir associado", type="primary", disabled=not confirmado, key="btn_assoc"):
        # Não há verificação prévia no Python de propósito: quem garante a regra é a FK do banco.
        # Se houver chamados, o MariaDB devolve o erro 1451 e executar() transforma em mensagem.
        ok, resultado = executar(con, "DELETE FROM ASSOCIADO WHERE id_associado = %s", (id_associado,))
        guardar_mensagem(ok, f"Associado {a['nome']} excluído." if ok else resultado)
        st.rerun()


def main():
    st.set_page_config(page_title="USUPORT - Exclusão", page_icon="⚓", layout="wide")
    st.title("USUPORT - Exclusão e inativação")

    con = barra_conexao()
    if con is None:
        st.info("Preencha o IP do Alpine e a senha na barra lateral e clique em Conectar.")
        return

    mostrar_mensagem()

    try:
        col1, col2 = st.columns(2, gap="large")
        with col1:
            excluir_chamado(con)
        with col2:
            excluir_associado(con)
    except pymysql.err.Error as e:
        con.rollback()
        st.error(f"Erro do banco: {e}")


main()
