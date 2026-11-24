# USUPORT | Canal do Usuário

Sistema de banco de dados e aplicação para consulta e acompanhamento de chamados da **USUPORT (Associação de Usuários dos Portos da Bahia)**, relacionados aos acidentes registrados na base de dados da Polícia Rodoviária Federal (PRF).

O projeto foi desenvolvido como parte do **Trabalho A3 da disciplina Banco de Dados, na UNIFACS**, com foco na modelagem relacional, normalização, integridade referencial e manipulação de dados utilizando SQL.

## Objetivo do projeto

Desenvolver uma estrutura de banco de dados capaz de integrar informações sobre acidentes rodoviários e solicitações de atendimento, permitindo organizar, consultar e analisar os registros relacionados ao canal de atendimento da USUPORT.

O sistema reúne informações de associados, atendentes, chamados, histórico de atendimento e acidentes, oferecendo consultas que relacionam os dados operacionais com os registros da PRF.

## Arquitetura

A solução utiliza uma arquitetura distribuída, na qual a aplicação é executada no Windows e o banco de dados permanece hospedado em uma máquina virtual Linux.

```text
┌──────────────────────────────┐
│          WINDOWS             │
│                              │
│  Navegador + Streamlit       │
│  Python + PyMySQL            │
│                              │
└──────────────┬───────────────┘
               │
               │ TCP / Porta 3306
               │ Rede local
               │
┌──────────────▼───────────────┐
│          VIRTUALBOX          │
│                              │
│  Alpine Linux                │
│  MariaDB                     │
│                              │
│  Banco: usuport              │
│  Usuário: usuport_app        │
│                              │
└──────────────────────────────┘
```

### Tecnologias utilizadas

| Tecnologia | Finalidade |
|---|---|
| Python | Linguagem da aplicação |
| Streamlit | Interface web |
| PyMySQL | Comunicação com o banco |
| Pandas | Organização e apresentação dos dados |
| openpyxl | Leitura da planilha da PRF pelo `gerar_dml.py` |
| MariaDB | Gerenciamento do banco de dados |
| Alpine Linux | Sistema operacional da máquina virtual |
| VirtualBox | Virtualização do servidor de banco |
| SQL | Criação, manipulação e consulta dos dados |

### Configuração do ambiente

- Máquina virtual: `Alpine_0411.ova`.
- Virtualização: Oracle VirtualBox.
- Rede: adaptador configurado em modo Bridge.
- Banco de dados: `usuport`.
- Usuário de aplicação: `usuport_app`.
- Porta de comunicação: `3306`.

> A máquina virtual e sua imagem OVA são recursos externos e não estão incluídos nos arquivos deste repositório.

## Estrutura do banco de dados

O modelo relacional contempla **16 tabelas**, organizadas para representar os registros de acidentes, seus envolvidos e as operações de atendimento.

### Módulo de acidentes (PRF)

- `LOCALIZACAO`
- `UNIDADE_POLICIAL`
- `CONDICAO_VIA_AMBIENTE`
- `ACIDENTE`
- `PESSOA`
- `VEICULO`
- `ENVOLVIMENTO`
- `CAUSA_ACIDENTE`
- `ACIDENTE_CAUSA`
- `TIPO_ACIDENTE`
- `ACIDENTE_TIPO`

### Módulo de atendimento (USUPORT)

- `ASSOCIADO`
- `ATENDENTE`
- `STATUS_CHAMADO`
- `CHAMADO`
- `HISTORICO_ATENDIMENTO`

O relacionamento entre as tabelas utiliza chaves primárias, chaves estrangeiras, restrições de integridade e validação de valores, incluindo a restrição de prioridade dos chamados.

A modelagem também contempla relacionamentos muitos-para-muitos, representados por tabelas associativas, como `ACIDENTE_CAUSA` e `ACIDENTE_TIPO`.

## Dados utilizados

A carga inicial foi construída a partir de uma planilha de acidentes da PRF.

O conjunto disponibilizado no projeto contempla:

- 43 acidentes rodoviários completos (296 das 499 linhas da planilha, respeitando o limite de 300 linhas);
- informações de localização, rodovia e quilometragem;
- condições da via e do ambiente;
- causas e tipos de acidentes;
- pessoas, veículos e envolvimentos;
- registros de associados, atendentes e chamados;
- histórico de atendimento.

Os dados são distribuídos entre as tabelas do modelo para preservar a organização relacional e a integridade referencial.

## Aplicação

A aplicação utiliza Streamlit para disponibilizar uma interface de consulta aos chamados armazenados no MariaDB.

### Funcionalidades disponíveis

- Conexão com o banco de dados pela barra lateral.
- Consulta de chamados com relacionamentos entre tabelas (JOIN).
- Filtro por status do chamado.
- Filtro por prioridade.
- Filtro por tipo de associado.
- Filtro por período de abertura.
- Pesquisa pelo título do chamado.
- Indicadores de quantidade de chamados encontrados, em aberto, vinculados a acidentes e de prioridade alta ou crítica.
- Resumo de chamados por status, incluindo quantidade e média de dias até o fechamento.
- Visualização detalhada de um chamado.
- Consulta do acidente relacionado, quando existente.
- Exibição do histórico de atendimento.

A conexão é realizada diretamente com a máquina virtual. O endereço IP, a porta, o usuário, o banco e a senha podem ser informados na interface.

A senha não fica gravada no código-fonte.

## Organização dos arquivos

```text
Usuporte/
├── app/            aplicação Streamlit (telas e conexão com o banco)
│   └── pages/      telas extras, que aparecem no menu lateral
├── sql/            scripts SQL (DDL, DML, DQL e exemplos)
├── ferramentas/    scripts de apoio (carregar SQL na VM e gerar o DML)
├── dados/          planilha da PRF usada na carga
└── docs/           material de apoio
```

| Arquivo | Descrição |
|---|---|
| `app/consulta.py` | Aplicação Streamlit responsável pela interface de consulta de chamados (tela inicial). |
| `app/conexao.py` | Módulo compartilhado para conexão, consultas e operações de escrita no MariaDB. |
| `app/pages/1_Cadastro.py` | Tela de cadastro (Create) de chamados e associados. |
| `app/pages/2_Agendamento.py` | Tela de agendamento de atendimentos: grava o histórico e atualiza o chamado numa transação. |
| `app/pages/3_Exclusao.py` | Tela de exclusão (Delete) e inativação: cancelar ou excluir chamados e excluir associados. |
| `sql/USUPORT_DDL_FINAL.sql` | Criação do banco de dados, das 16 tabelas, relacionamentos, restrições e índices. |
| `sql/USUPORT_DML.sql` | Carga inicial dos dados da PRF e dos registros do canal de atendimento (gerado pelo `gerar_dml.py`). |
| `sql/dados_ficticios.sql` | Associados, atendentes, status, chamados e histórico fictícios, incluídos no final do DML. |
| `sql/USUPORT_DQL.sql` | Consultas SQL para análise dos chamados, acidentes e integração entre os módulos. |
| `sql/USUPORT_DML_UPDATE_DELETE.sql` | Exemplos de atualização e exclusão de registros para demonstração. |
| `sql/limpar_provisorio.sql` | Remoção das tabelas de testes do banco provisório utilizado nas etapas iniciais. |
| `ferramentas/carregar_sql.py` | Ferramenta Python para executar scripts SQL remotamente na máquina virtual. |
| `ferramentas/gerar_dml.py` | Lê a planilha da PRF (até 300 linhas, só acidentes completos), normaliza os dados nas tabelas do modelo e gera o `sql/USUPORT_DML.sql`. |
| `dados/acidentes2024_todas_causas_tipos_Usuport.xlsx` | Planilha de acidentes da PRF, origem dos dados. |
| `docs/NORMALIZAÇÃO.pdf` | Material de apoio referente à normalização do modelo de dados. |
| `docs/DICIONÁRIO DE DADOS – DER USUPORT.pdf` | Dicionário de dados do modelo. |
| `docs/DER USUPORT CORRIGIDO.pdf` | Diagrama entidade-relacionamento (DER) do banco. |
| `requirements.txt` | Dependências Python necessárias para executar a aplicação. |

## Instalação e execução

### 1. Preparar a máquina virtual

Inicie a máquina virtual Alpine Linux pelo VirtualBox.

Entre no sistema utilizando o usuário `root`.

Confira o endereço IP da máquina:

```bash
ip a
```

Verifique se o serviço MariaDB está em execução:

```bash
rc-status
```

Também é possível consultar diretamente:

```bash
rc-service mariadb status
```

O MariaDB precisa aceitar conexões pela rede, utilizando a porta `3306`, e o usuário `usuport_app` deve possuir as permissões necessárias para acessar o banco `usuport` a partir do computador Windows.

### 2. Preparar o ambiente Windows

Com o Python instalado, abra o terminal na pasta do projeto.

Instale as dependências:

```bash
python -m pip install -r requirements.txt
```

As bibliotecas instaladas são:

- Streamlit
- PyMySQL
- Pandas
- openpyxl (usado só pelo `gerar_dml.py`, para ler a planilha)

### 3. Criar e carregar o banco de dados

Todos os comandos abaixo são executados na pasta `Usuporte`. A ferramenta `ferramentas/carregar_sql.py` permite executar os scripts diretamente na máquina virtual, sem precisar transferir os arquivos SQL para o Alpine.

Execute os arquivos na seguinte ordem.

**Primeiro: criação da estrutura**

```bash
python ferramentas/carregar_sql.py sql/USUPORT_DDL_FINAL.sql
```

**Segundo: carga inicial dos dados**

```bash
python ferramentas/carregar_sql.py sql/USUPORT_DML.sql
```

Durante a execução, informe:

- IP da máquina virtual;
- usuário do banco (pressione Enter para utilizar `usuport_app`);
- senha do banco.

A criação das tabelas deve ser realizada antes da inserção dos dados, respeitando as dependências entre as chaves estrangeiras.

> Execute a carga inicial somente uma vez em cada banco recém-criado. Os scripts não foram preparados para duplicar a carga automaticamente.

### Banco provisório

Caso o banco ainda contenha tabelas dos primeiros testes, execute antes:

```bash
python ferramentas/carregar_sql.py sql/limpar_provisorio.sql
```

Esse arquivo remove somente as tabelas provisórias em letras minúsculas. Ele não apaga as tabelas oficiais do modelo.

### 4. Executar a aplicação

Na pasta do projeto, execute:

```bash
python -m streamlit run app/consulta.py
```

A aplicação será disponibilizada pelo navegador no endereço:

```text
http://localhost:8501
```

Na barra lateral:

1. Informe o IP da máquina virtual.
2. Confira a porta `3306` e o banco `usuport`.
3. Informe o usuário e a senha.
4. Clique em **Conectar**.

Após a conexão, a tela apresenta os chamados e seus respectivos filtros, indicadores e detalhes.

## Consultas e demonstração SQL

O projeto possui scripts específicos para demonstrar as operações de manipulação e consulta de dados.

### USUPORT_DQL.sql

Contém consultas que exploram recursos como:

- `JOIN`;
- `LEFT JOIN`;
- `GROUP BY`;
- `COUNT`;
- `AVG`;
- `SUM`;
- `HAVING`;
- `TIMESTAMPDIFF`;
- filtros por período;
- relacionamentos entre múltiplas tabelas.

As consultas abrangem três áreas: atendimento, acidentes da PRF e integração entre chamados e acidentes.

### USUPORT_DML_UPDATE_DELETE.sql

Contém exemplos de atualização e exclusão de registros, com consultas `SELECT` antes e depois das operações para facilitar a demonstração dos resultados.

Para a apresentação, recomenda-se seguir esta ordem:

1. Executar `USUPORT_DQL.sql` para visualizar os dados originais.
2. Executar `USUPORT_DML_UPDATE_DELETE.sql` para demonstrar `UPDATE` e `DELETE`.
3. Comparar os resultados das operações.

O script também apresenta um exemplo de exclusão de acidente dentro de uma transação, utilizando `ROLLBACK` para preservar os dados do teste.

> Algumas operações alteram ou removem registros da carga inicial. Para repetir a demonstração desde o início, recrie o banco oficial e execute novamente o DDL e o DML.

## Reutilização da conexão

O módulo `conexao.py` centraliza as funções utilizadas para acessar o banco de dados.

Ele disponibiliza:

```python
from conexao import barra_conexao, selecionar, executar
```

### Principais funções

| Função | Responsabilidade |
|---|---|
| `barra_conexao()` | Exibe o formulário de conexão na barra lateral. |
| `selecionar()` | Executa consultas SELECT e devolve os registros. |
| `executar()` | Executa operações INSERT, UPDATE e DELETE. |

### Exemplo de consulta

```python
from conexao import barra_conexao, selecionar, executar

con = barra_conexao()

if con is not None:
    linhas = selecionar(
        con,
        "SELECT * FROM CHAMADO WHERE id_status = %s",
        (1,)
    )
```

Para operações de escrita:

```python
ok, resultado = executar(
    con,
    "UPDATE CHAMADO SET id_status = %s WHERE id_chamado = %s",
    (2, 1)
)
```

A função `executar()` devolve uma tupla:

- `(True, resultado)` quando a operação é concluída.
- `(False, mensagem)` quando uma regra de integridade do banco impede a operação.

O segundo valor corresponde ao `lastrowid` disponibilizado pelo cursor, sendo útil principalmente em operações de INSERT.

## Equipe

Projeto desenvolvido em grupo para a disciplina Banco de Dados, como parte da avaliação A3 da UNIFACS.

- Gustavo Pitangueira
- Suzana Isis
- Radija Menezes
- Manuela Souza
- João Carvalho
- Cassio Bustamante
- Lucas Quezado

---

Trabalho acadêmico de Banco de Dados  
UNIFACS | 2026.2
