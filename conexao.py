"""
conexao.py - Conexão com o MariaDB da VM Alpine (projeto USUPORT).

Segue o mesmo padrão do exemplo do professor (farmacia_streamlit.py):

    [Navegador + Streamlit no Windows]  --- TCP, porta 3306 --->  [VM Alpine no VirtualBox: MariaDB]

- O IP do Alpine e a senha são digitados na tela; a senha nunca fica gravada em arquivo.
- Arquivo COMPARTILHADO por todas as telas (consulta, cadastro, andamento e exclusão).
  Basta chamar barra_conexao() no início de cada tela.
"""
import pymysql
import streamlit as st

# Valores sugeridos no formulário de conexão (podem ser alterados na tela)
USUARIO_PADRAO = "usuport_app"
BANCO_PADRAO = "usuport"

# Mensagens amigáveis para os erros de conexão mais comuns
DICAS_CONEXAO = {
    2003: "Não alcancei o servidor. Confira se a VM está ligada, se o IP está certo (no Alpine: `ip a`), "
          "se a placa de rede da VM está em **Modo Bridge** ou **Host-only** e se o MariaDB está "
          "rodando e aceitando rede (`rc-service mariadb status`; rode o `preparar_alpine.sh`).",
    1045: "Usuário ou senha recusados. Para redefinir a senha, rode de novo o `preparar_alpine.sh`.",
    1130: "O MariaDB recusou o IP deste computador. Rode o `preparar_alpine.sh`, que libera o usuário para a rede.",
    1044: "O usuário não tem permissão neste banco. Rode o `preparar_alpine.sh` ou confira o nome do banco.",
}

# Erros de regra do banco (PK, FK, UNIQUE, NOT NULL, CHECK) - usados no cadastro e na exclusão.
# O PyMySQL classifica o erro 4025 (CHECK) como OperationalError e os demais como IntegrityError.
ERROS_DE_REGRA = (pymysql.err.IntegrityError, pymysql.err.OperationalError)
ERROS = {
    1048: "NOT NULL: campo obrigatório",
    1062: "UNIQUE/PK: valor repetido",
    1451: "FK: há registros apontando para este (ex.: chamados de um porto)",
    1452: "FK: o registro apontado não existe",
    4025: "CHECK: valor fora do domínio permitido",
}


# =====================================================================================
# Funções de banco
# =====================================================================================
def abrir_conexao(host, porta, usuario, senha, banco):
    """Abre a conexão com o MariaDB da VM, já dentro do banco do projeto."""
    return pymysql.connect(
        host=host, port=porta, user=usuario, password=senha, database=banco,
        charset="utf8mb4", autocommit=False, connect_timeout=8,
        cursorclass=pymysql.cursors.DictCursor,  # cada linha vem como dicionário {coluna: valor}
    )


def selecionar(con, sql, params=None):
    """Executa um SELECT e devolve a lista de linhas."""
    with con.cursor() as cur:
        cur.execute(sql, params)  # %s no SQL + params: protege contra SQL injection
        linhas = cur.fetchall()
    con.commit()  # encerra a leitura: a próxima enxerga dados gravados por outras telas
    return linhas


def executar(con, sql, params):
    """
    Roda INSERT, UPDATE ou DELETE.
    Devolve (True, id gerado) ou (False, texto explicando a regra que foi violada).
    """
    try:
        with con.cursor() as cur:
            cur.execute(sql, params)
            novo_id = cur.lastrowid
        con.commit()
        return True, novo_id
    except ERROS_DE_REGRA as e:
        con.rollback()  # desfaz: os dados antigos ficam intactos
        codigo, mensagem = e.args
        if codigo not in ERROS and isinstance(e, pymysql.err.OperationalError):
            raise  # outro problema (ex.: rede): não esconder
        return False, f"Erro {codigo} ({ERROS.get(codigo, 'integridade')}): {mensagem}"
    except pymysql.err.DataError as e:
        con.rollback()
        return False, f"Dado inválido: {e.args[1]}"


# =====================================================================================
# Formulário de conexão (barra lateral) - igual para todas as telas
# =====================================================================================
def barra_conexao():
    """Mostra o formulário de conexão. Devolve a conexão ativa ou None."""
    st.sidebar.header("Conexão com o Alpine")
    con = st.session_state.get("con")

    # Ainda não conectado: mostra o formulário
    if con is None:
        if "aviso" in st.session_state:
            st.sidebar.error(st.session_state.pop("aviso"))
        with st.sidebar.form("conexao"):
            host = st.text_input("IP do Alpine", placeholder="ex.: 192.168.56.101")
            porta = st.number_input("Porta", 1, 65535, 3306)
            usuario = st.text_input("Usuário", USUARIO_PADRAO)
            senha = st.text_input("Senha", type="password")
            banco = st.text_input("Banco", BANCO_PADRAO)
            enviar = st.form_submit_button("Conectar")
        if enviar:
            if not host.strip():
                st.sidebar.error("Digite o IP do Alpine. No Alpine, descubra com `ip a`.")
                return None
            try:
                st.session_state.con = abrir_conexao(host.strip(), int(porta), usuario.strip(), senha, banco.strip())
                st.session_state.destino = f"{host.strip()}:{int(porta)} · banco {banco.strip()}"
                st.rerun()
            except pymysql.err.Error as e:
                codigo = e.args[0] if e.args else "?"
                st.sidebar.error(f"Erro {codigo}: {e.args[1] if len(e.args) > 1 else e}")
                st.sidebar.warning(DICAS_CONEXAO.get(codigo, "Confira os dados da conexão."))
        return None

    # Já conectado: confere se a conexão continua viva (a VM pode ter sido reiniciada)
    try:
        con.ping(reconnect=False)
    except pymysql.err.Error as e:
        del st.session_state["con"]
        st.session_state.aviso = f"A conexão caiu: {e}. Conecte de novo."
        st.rerun()

    st.sidebar.success(f"Conectado a {st.session_state.destino}")
    st.sidebar.caption("MariaDB " + selecionar(con, "SELECT VERSION() AS v")[0]["v"])
    if st.sidebar.button("Desconectar"):
        con.close()
        del st.session_state["con"]
        st.rerun()
    return con
