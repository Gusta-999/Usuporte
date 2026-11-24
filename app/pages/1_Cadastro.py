"""
1_Cadastro.py - Tela de CADASTRO (Create) da USUPORT.

Cadastra:
  - um novo CHAMADO (INSERT em CHAMADO), ligado a um associado e, se houver, a um acidente da PRF;
  - um novo ASSOCIADO (INSERT em ASSOCIADO).

As regras de integridade ficam no banco (DDL): se o e-mail já existir (UNIQUE) ou a
prioridade for inválida (CHECK), o MariaDB recusa e a tela mostra o motivo.

Esta página aparece no menu lateral porque está dentro da pasta pages/
(rode o app com: python -m streamlit run app/consulta.py).
"""
import re

import pymysql
import streamlit as st

from conexao import barra_conexao, executar, guardar_mensagem, mostrar_mensagem, selecionar

# Códigos de prioridade aceitos pelo CHECK da tabela CHAMADO
PRIORIDADES = {"B": "Baixa", "M": "Média", "A": "Alta", "C": "Crítica"}


# =====================================================================================
# Telefone: DDD + número = no máximo 11 dígitos (sem contar o 55 do Brasil)
#   celular: (71) 99111-0001 -> 11 dígitos | fixo: (41) 3322-0002 -> 10 dígitos
# =====================================================================================
def formatar_telefone(texto):
    """
    Aceita o telefone digitado de qualquer jeito ("71991110001", "(71) 99111-0001",
    "+55 71 99111-0001") e devolve no padrão "(71) 99111-0001".
    Devolve None se não tiver 10 ou 11 dígitos.
    """
    digitos = re.sub(r"\D", "", texto)  # tira tudo que não é número: ( ) - espaço +
    if len(digitos) > 11 and digitos.startswith("55"):
        digitos = digitos[2:]  # descarta o código do país (55), que não entra na conta
    if len(digitos) not in (10, 11):
        return None
    return f"({digitos[:2]}) {digitos[2:-4]}-{digitos[-4:]}"


# =====================================================================================
# Listas usadas nos campos de escolha (selectbox)
# Cada função devolve um dicionário {id: texto que aparece na tela}
# =====================================================================================
def opcoes_associados(con):
    linhas = selecionar(con, "SELECT id_associado, nome, tipo FROM ASSOCIADO ORDER BY nome")
    return {l["id_associado"]: f"{l['nome']} ({l['tipo']})" for l in linhas}


def opcoes_atendentes(con):
    linhas = selecionar(con, "SELECT id_atendente, nome, setor FROM ATENDENTE ORDER BY nome")
    return {l["id_atendente"]: f"{l['nome']} - {l['setor']}" for l in linhas}


def opcoes_acidentes(con):
    """Acidentes da planilha da PRF, com cidade e data para facilitar a escolha (JOIN com LOCALIZACAO)."""
    linhas = selecionar(con, """
        SELECT ac.id_acidente, ac.data_inversa, ac.classificacao_acidente, l.municipio, l.uf
        FROM ACIDENTE ac
        JOIN LOCALIZACAO l ON l.id_localizacao = ac.id_localizacao
        ORDER BY ac.id_acidente""")
    return {l["id_acidente"]: f"{l['id_acidente']} · {l['municipio']}/{l['uf']} · "
                              f"{l['data_inversa']:%d/%m/%Y} · {l['classificacao_acidente']}"
            for l in linhas}


# =====================================================================================
# Cadastro de CHAMADO
# =====================================================================================
def cadastro_chamado(con):
    associados = opcoes_associados(con)
    atendentes = opcoes_atendentes(con)
    acidentes = opcoes_acidentes(con)

    # Todo chamado novo começa com o status "Aberto" (busca o id pelo nome)
    id_aberto = selecionar(con, "SELECT id_status FROM STATUS_CHAMADO WHERE descricao = 'Aberto'")[0]["id_status"]

    # st.form: os campos só são enviados ao clicar no botão (não recarrega a cada tecla)
    with st.form("form_chamado", clear_on_submit=True):
        id_associado = st.selectbox("Associado *", list(associados), format_func=associados.get)
        titulo = st.text_input("Título *", max_chars=150)  # VARCHAR(150) no DDL
        descricao = st.text_area("Descrição")
        col1, col2 = st.columns(2)
        prioridade = col1.selectbox("Prioridade *", list(PRIORIDADES), index=1,
                                    format_func=lambda p: f"{p} - {PRIORIDADES[p]}")
        # None = campo opcional (as colunas id_atendente e id_acidente aceitam NULL)
        id_atendente = col2.selectbox("Atendente responsável", [None, *atendentes],
                                      format_func=lambda i: "(definir depois)" if i is None else atendentes[i])
        id_acidente = st.selectbox("Acidente relacionado (planilha da PRF)", [None, *acidentes],
                                   format_func=lambda i: "(nenhum)" if i is None else acidentes[i])
        enviar = st.form_submit_button("Cadastrar chamado", type="primary")

    if enviar:
        # Validação na tela antes de ir ao banco
        if not titulo.strip():
            st.error("Informe o título do chamado.")
            return
        # INSERT com %s: o PyMySQL escapa os valores (proteção contra SQL injection).
        # NOW() grava a data/hora atual do servidor como data de abertura.
        ok, resultado = executar(con, """
            INSERT INTO CHAMADO (id_associado, id_acidente, id_atendente, id_status,
                                 titulo, descricao, prioridade, data_abertura)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())""",
            (id_associado, id_acidente, id_atendente, id_aberto,
             titulo.strip(), descricao.strip() or None, prioridade))
        # resultado = id gerado pelo AUTO_INCREMENT (sucesso) ou a mensagem de erro
        guardar_mensagem(ok, f"Chamado #{resultado} cadastrado." if ok else resultado)
        st.rerun()  # recarrega para a lista de últimos chamados já mostrar o novo


# =====================================================================================
# Cadastro de ASSOCIADO
# =====================================================================================
def cadastro_associado(con):
    tipos = [l["tipo"] for l in selecionar(con, "SELECT DISTINCT tipo FROM ASSOCIADO ORDER BY tipo")]

    with st.form("form_associado", clear_on_submit=True):
        nome = st.text_input("Nome *", max_chars=120)
        # accept_new_options: escolhe um tipo existente ou digita um novo
        tipo = st.selectbox("Tipo *", tipos, index=None, accept_new_options=True,
                            placeholder="Escolha ou digite um tipo")
        col1, col2 = st.columns(2)
        email = col1.text_input("E-mail *", max_chars=100)
        telefone = col2.text_input("Telefone", max_chars=20, placeholder="(71) 99999-0000",
                                   help="DDD + número: até 11 dígitos, sem o +55.")
        enviar = st.form_submit_button("Cadastrar associado", type="primary")

    if enviar:
        if not nome.strip() or not tipo or "@" not in email:
            st.error("Preencha nome, tipo e um e-mail válido.")
            return
        # Telefone é opcional; se preenchido, precisa ter DDD + número (10 ou 11 dígitos)
        telefone_formatado = None
        if telefone.strip():
            telefone_formatado = formatar_telefone(telefone)
            if telefone_formatado is None:
                st.error("Telefone inválido: use DDD + número, com 10 ou 11 dígitos "
                         "(ex.: (71) 99111-0001). Não precisa do +55.")
                return
        # Se o e-mail já existir, o UNIQUE (uq_associado_email) recusa com o erro 1062
        ok, resultado = executar(con, """
            INSERT INTO ASSOCIADO (nome, tipo, email, telefone)
            VALUES (%s, %s, %s, %s)""",
            (nome.strip(), tipo.strip(), email.strip().lower(), telefone_formatado))
        guardar_mensagem(ok, f"Associado #{resultado} cadastrado." if ok else resultado)
        st.rerun()


# =====================================================================================
# Tela
# =====================================================================================
def main():
    st.set_page_config(page_title="USUPORT - Cadastro", page_icon="⚓", layout="wide")
    st.title("USUPORT - Cadastro")

    con = barra_conexao()
    if con is None:
        st.info("Preencha o IP do Alpine e a senha na barra lateral e clique em Conectar.")
        return

    mostrar_mensagem()  # resultado do último cadastro (sucesso ou erro do banco)

    try:
        aba_chamado, aba_associado = st.tabs(["Novo chamado", "Novo associado"])
        with aba_chamado:
            cadastro_chamado(con)
            st.subheader("Últimos chamados cadastrados")
            st.dataframe(selecionar(con, """
                SELECT c.id_chamado AS id, c.titulo, a.nome AS associado, c.prioridade,
                       s.descricao AS status, c.data_abertura AS abertura
                FROM CHAMADO c
                JOIN ASSOCIADO a      ON a.id_associado = c.id_associado
                JOIN STATUS_CHAMADO s ON s.id_status = c.id_status
                ORDER BY c.id_chamado DESC LIMIT 5"""), hide_index=True, width="stretch")
        with aba_associado:
            cadastro_associado(con)
            st.subheader("Associados cadastrados")
            st.dataframe(selecionar(con, "SELECT * FROM ASSOCIADO ORDER BY id_associado DESC"),
                         hide_index=True, width="stretch")
    except pymysql.err.Error as e:
        # Erro inesperado do banco (ex.: tabela inexistente): mostra sem derrubar a tela
        con.rollback()
        st.error(f"Erro do banco: {e}")


main()
