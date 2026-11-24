"""
conexao.py - Conexão com o MariaDB da VM Alpine (projeto USUPORT).

Segue o mesmo padrão do exemplo do professor (farmacia_streamlit.py):

    [Navegador + Streamlit no Windows]  --- TCP, porta 3306 --->  [VM Alpine no VirtualBox: MariaDB]

- O IP do Alpine e a senha são digitados na tela; a senha nunca fica gravada em arquivo.
- Arquivo COMPARTILHADO por todas as telas (consulta, cadastro, agendamento e exclusão).
  Basta chamar barra_conexao() no início de cada tela.
"""
import secrets

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
    1451: "FK: há registros apontando para este (ex.: chamados de um associado)",
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


def executar_transacao(con, comandos):
    """
    Roda vários INSERT/UPDATE/DELETE como UMA transação: ou todos são gravados, ou nenhum.
    Ex.: excluir um chamado exige apagar antes o histórico dele (tabela filha).
    Se o segundo comando falhar, o ROLLBACK desfaz também o primeiro.

    comandos: lista de pares (sql, params).
    Devolve (True, id gerado pelo último comando) ou (False, texto explicando a regra violada).
    """
    try:
        with con.cursor() as cur:
            for sql, params in comandos:
                cur.execute(sql, params)
            novo_id = cur.lastrowid
        con.commit()  # grava tudo de uma vez
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


def executar(con, sql, params):
    """
    Roda um único INSERT, UPDATE ou DELETE.
    Devolve (True, id gerado) ou (False, texto explicando a regra que foi violada).
    """
    return executar_transacao(con, [(sql, params)])


# =====================================================================================
# Mensagem que sobrevive ao st.rerun()
# Depois de gravar, as telas recarregam (st.rerun) para atualizar listas e tabelas.
# A mensagem de sucesso/erro é guardada antes e mostrada no recarregamento seguinte.
# =====================================================================================
def guardar_mensagem(ok, texto):
    st.session_state.mensagem = (ok, texto)


def mostrar_mensagem():
    if "mensagem" in st.session_state:
        ok, texto = st.session_state.pop("mensagem")
        (st.success if ok else st.error)(texto)


# =====================================================================================
# Manter conectado ao recarregar a página (F5) e ao trocar de tela
# O F5 cria uma sessão nova do Streamlit e apaga o st.session_state. Por isso a conexão
# aberta fica guardada no servidor do Streamlit, identificada por um código aleatório
# que vai na URL (?sessao=...). A senha não é gravada em lugar nenhum.
# =====================================================================================
@st.cache_resource
def _conexoes_abertas():
    """Dicionário {código da sessão: (conexão, destino)}, compartilhado entre recarregamentos."""
    return {}


def _lembrar(con, destino):
    codigo = secrets.token_urlsafe(16)
    _conexoes_abertas()[codigo] = (con, destino)
    st.session_state.sessao = codigo
    st.query_params["sessao"] = codigo


def _esquecer():
    codigo = st.session_state.pop("sessao", None) or st.query_params.get("sessao")
    _conexoes_abertas().pop(codigo, None)
    st.query_params.pop("sessao", None)
    st.session_state.pop("con", None)


# =====================================================================================
# Formulário de conexão (barra lateral) - igual para todas as telas
# =====================================================================================
def barra_conexao():
    """Mostra o formulário de conexão. Devolve a conexão ativa ou None."""
    st.sidebar.header("Conexão com o Alpine")
    con = st.session_state.get("con")

    # Página recarregada (F5): recupera a conexão pelo código da URL
    if con is None:
        codigo = st.query_params.get("sessao")
        salvo = _conexoes_abertas().get(codigo)
        if salvo:
            con, st.session_state.destino = salvo
            st.session_state.con = con
            st.session_state.sessao = codigo

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
                _lembrar(st.session_state.con, st.session_state.destino)
                st.rerun()
            except pymysql.err.Error as e:
                codigo = e.args[0] if e.args else "?"
                st.sidebar.error(f"Erro {codigo}: {e.args[1] if len(e.args) > 1 else e}")
                st.sidebar.warning(DICAS_CONEXAO.get(codigo, "Confira os dados da conexão."))
        return None

    # Ao trocar de tela o Streamlit limpa a URL: devolve o código para o F5 continuar funcionando
    if st.session_state.get("sessao") and st.query_params.get("sessao") != st.session_state.sessao:
        st.query_params["sessao"] = st.session_state.sessao

    # Já conectado: confere se a conexão continua viva (a VM pode ter sido reiniciada)
    try:
        con.ping(reconnect=False)
    except pymysql.err.Error as e:
        _esquecer()
        st.session_state.aviso = f"A conexão caiu: {e}. Conecte de novo."
        st.rerun()

    st.sidebar.success(f"Conectado a {st.session_state.destino}")
    st.sidebar.caption("MariaDB " + selecionar(con, "SELECT VERSION() AS v")[0]["v"])
    if st.sidebar.button("Desconectar"):
        con.close()
        _esquecer()
        st.rerun()
    return con
