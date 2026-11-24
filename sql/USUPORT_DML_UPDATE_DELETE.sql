-- USUPORT | DML - exemplos de UPDATE e DELETE (para a apresentacao)
-- Execute depois do USUPORT_DDL_FINAL.sql e do USUPORT_DML.sql (carga inicial).
-- Cada exemplo tem um SELECT antes e outro depois, para mostrar o efeito do comando.
-- Para repetir a demonstracao, recrie o banco com o DDL e rode a carga de novo.
USE usuport;
SET NAMES utf8mb4;

-- =====================================================================
-- UPDATE
-- =====================================================================

-- 1) Atribuir atendente e mudar status de um chamado aberto
SELECT id_chamado, id_atendente, id_status FROM CHAMADO WHERE id_chamado = 1;
UPDATE CHAMADO SET id_atendente = 2, id_status = 2 WHERE id_chamado = 1;
SELECT id_chamado, id_atendente, id_status FROM CHAMADO WHERE id_chamado = 1;

-- 2) Encerrar um chamado que ja esta resolvido
SELECT id_chamado, id_status FROM CHAMADO WHERE id_chamado = 5;
UPDATE CHAMADO SET id_status = 5 WHERE id_chamado = 5 AND id_status = 4;
SELECT id_chamado, id_status FROM CHAMADO WHERE id_chamado = 5;

-- 3) Elevar prioridade de chamados antigos ainda em aberto
SELECT id_chamado, prioridade, id_status, data_abertura FROM CHAMADO
 WHERE id_status IN (1,2) AND prioridade = 'B' AND data_abertura < '2024-04-01';
UPDATE CHAMADO SET prioridade = 'A' WHERE id_status IN (1,2) AND prioridade = 'B' AND data_abertura < '2024-04-01';
SELECT id_chamado, prioridade FROM CHAMADO WHERE id_chamado = 2;

-- 4) Corrigir dado de um atendente
SELECT id_atendente, nome, setor FROM ATENDENTE WHERE id_atendente = 2;
UPDATE ATENDENTE SET setor = 'Suporte N2' WHERE id_atendente = 2;
SELECT id_atendente, nome, setor FROM ATENDENTE WHERE id_atendente = 2;

-- 5) Corrigir o horario registrado de um acidente
SELECT id_acidente, horario FROM ACIDENTE WHERE id_acidente = 571772;
UPDATE ACIDENTE SET horario = '00:10:00' WHERE id_acidente = 571772;
SELECT id_acidente, horario FROM ACIDENTE WHERE id_acidente = 571772;

-- 6) Padronizar texto: marca de veiculo em maiusculas
--    BINARY forca comparacao diferenciando maiusculas/minusculas (collation _ci ignora a diferenca)
SELECT id_veiculo, marca FROM VEICULO WHERE BINARY marca <> UPPER(marca);
UPDATE VEICULO SET marca = UPPER(marca) WHERE BINARY marca <> UPPER(marca);
SELECT id_veiculo, marca FROM VEICULO WHERE id_veiculo = 1018281;

-- =====================================================================
-- DELETE - respeitam a ordem das chaves estrangeiras (filho antes do pai)
-- =====================================================================

-- 1) Excluir um chamado: primeiro o historico (filho), depois o chamado
SELECT COUNT(*) AS historico_chamado_11 FROM HISTORICO_ATENDIMENTO WHERE id_chamado = 11;
DELETE FROM HISTORICO_ATENDIMENTO WHERE id_chamado = 11;
DELETE FROM CHAMADO WHERE id_chamado = 11;
SELECT COUNT(*) AS chamados_restantes FROM CHAMADO;

-- 2) Excluir um status nao utilizado
SELECT * FROM STATUS_CHAMADO;
DELETE FROM STATUS_CHAMADO WHERE descricao = 'Cancelado' AND id_status NOT IN (SELECT id_status FROM CHAMADO);
SELECT * FROM STATUS_CHAMADO;

-- 3) Excluir o envolvimento de testemunhas de um acidente (a pessoa continua em PESSOA)
SELECT id_acidente, pesid, tipo_envolvido FROM ENVOLVIMENTO WHERE tipo_envolvido = 'Testemunha' AND id_acidente = 571782;
DELETE FROM ENVOLVIMENTO WHERE tipo_envolvido = 'Testemunha' AND id_acidente = 571782;
SELECT COUNT(*) AS envolvimentos_restantes FROM ENVOLVIMENTO;

-- 4) Excluir um acidente completo (todos os filhos antes). Em transacao com ROLLBACK
--    para nao perder os dados de teste; troque ROLLBACK por COMMIT para efetivar.
START TRANSACTION;
UPDATE CHAMADO SET id_acidente = NULL WHERE id_acidente = 571821;
DELETE FROM ENVOLVIMENTO   WHERE id_acidente = 571821;
DELETE FROM VEICULO        WHERE id_acidente = 571821;
DELETE FROM ACIDENTE_CAUSA WHERE id_acidente = 571821;
DELETE FROM ACIDENTE_TIPO  WHERE id_acidente = 571821;
DELETE FROM ACIDENTE       WHERE id_acidente = 571821;
SELECT COUNT(*) AS acidente_571821_dentro_da_transacao FROM ACIDENTE WHERE id_acidente = 571821;
ROLLBACK;
SELECT COUNT(*) AS acidente_571821_apos_rollback FROM ACIDENTE WHERE id_acidente = 571821;
