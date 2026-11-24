-- ============================================================
-- limpar_provisorio.sql
-- Apaga as tabelas do banco PROVISÓRIO (teste_provisorio.sql),
-- que tinham nomes em minúsculas e não fazem parte do modelo oficial.
-- Rode UMA vez, antes do USUPORT_DDL_FINAL.sql.
-- Não mexe nas tabelas oficiais (em MAIÚSCULAS): no MariaDB da VM,
-- 'chamado' e 'CHAMADO' são tabelas diferentes.
-- ============================================================
USE usuport;
DROP TABLE IF EXISTS andamento, chamado, usuario, associado, porto, categoria;
