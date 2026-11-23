# USUPORT – Canal do Usuário

Banco de dados e aplicação para registrar e acompanhar os chamados da USUPORT (Associação de Usuários dos Portos da Bahia), ligados aos acidentes da base da PRF.

Trabalho A3 – Banco de Dados – UNIFACS.

## Arquitetura

```
[Windows: navegador + Streamlit]  --- rede, TCP 3306 --->  [VirtualBox: VM Alpine Linux + MariaDB]
```

- **VM:** Alpine_0411.ova, com a placa de rede em **modo Bridge**
- **Banco:** MariaDB, banco `usuport`, usuário `usuport_app`
- **Aplicação:** Python + Streamlit + PyMySQL, executada no Windows

## Arquivos

| Arquivo | O que é |
|---|---|
| `USUPORT_DDL_FINAL.sql` | Cria as tabelas do modelo oficial |
| `USUPORT_DML.sql` | Carga inicial: 43 acidentes da planilha da PRF e os dados do canal de atendimento |
| `USUPORT_DQL.sql` | Consultas da apresentação (JOIN, GROUP BY, COUNT, AVG e filtro por data) |
| `USUPORT_DML_UPDATE_DELETE.sql` | Exemplos de UPDATE e DELETE, para rodar na apresentação |
| `limpar_provisorio.sql` | Apaga as tabelas do banco provisório usado nos primeiros testes |
| `carregar_sql.py` | Executa um arquivo `.sql` no banco da VM a partir do Windows |
| `conexao.py` | Conexão com o banco, compartilhada por todas as telas |
| `consulta.py` | Tela de consulta de chamados (Read) |
| `requirements.txt` | Bibliotecas Python necessárias |

## Como rodar

**1. Na VM** (login `root`): confira o IP com `ip a` e se o MariaDB está rodando com `rc-status`.

**2. No Windows**, na pasta do projeto:

```
python -m pip install -r requirements.txt
```

**3. Carregar o banco**, uma vez só e nesta ordem:

```
python carregar_sql.py limpar_provisorio.sql
python carregar_sql.py USUPORT_DDL_FINAL.sql
python carregar_sql.py USUPORT_DML.sql
```

O `carregar_sql.py` pede o IP da VM, o usuário (Enter aceita `usuport_app`) e a senha. O `limpar_provisorio.sql` só é necessário num banco que ainda tenha as tabelas provisórias.

**4. Abrir a tela de consulta:**

```
python -m streamlit run consulta.py
```

O navegador abre em `http://localhost:8501`. Na barra lateral, digite o IP da VM e a senha e clique em **Conectar**.

**5. Na apresentação:** rode o `USUPORT_DQL.sql` e depois o `USUPORT_DML_UPDATE_DELETE.sql` (pelo DBeaver ou pelo `carregar_sql.py`).

## Telas novas

Para criar uma tela que use o mesmo banco, comece por:

```python
from conexao import barra_conexao, selecionar, executar

con = barra_conexao()          # formulário de conexão na barra lateral
if con is not None:
    linhas = selecionar(con, "SELECT * FROM CHAMADO WHERE id_status = %s", (1,))
    ok, resultado = executar(con, "UPDATE CHAMADO SET id_status = %s WHERE id_chamado = %s", (2, 1))
```

`executar()` devolve `(True, id gerado)` ou `(False, mensagem)`, explicando a regra que o banco recusou (FK, CHECK, UNIQUE etc.).

## Equipe

Gustavo Pitangueira, Suzana Ísis, Radija Menezes, Manuela Souza, João Carvalho, Cassio Bustamante e Lucas Quezado.
