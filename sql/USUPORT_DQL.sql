-- USUPORT | DQL - consultas para a apresentacao (somente SELECT)
-- Recursos usados: JOIN, GROUP BY, COUNT, AVG e filtro por data.
-- Execute depois do USUPORT_DDL_FINAL.sql e do USUPORT_DML.sql.
-- Rode ANTES do USUPORT_DML_UPDATE_DELETE.sql (os resultados abaixo usam a carga inicial).
-- Obs.: todos os 43 acidentes da carga sao de 2024-01-01 e os chamados vao de
--       2024-02-10 a 2024-05-19; por isso os filtros de data dos chamados fazem mais diferenca.
USE usuport;
SET NAMES utf8mb4;

-- =====================================================================
-- BLOCO 1 - SUPORTE (CHAMADOS)
-- =====================================================================

-- 1) Chamados por status no periodo de marco a maio/2024
--    JOIN + COUNT + GROUP BY + filtro por data
--    Intervalo "meia-aberta" (>= inicio e < dia seguinte ao fim) para nao perder
--    chamados do ultimo dia, ja que data_abertura e DATETIME.
SELECT s.descricao AS status,
       COUNT(*)    AS total_chamados
FROM CHAMADO c
JOIN STATUS_CHAMADO s ON s.id_status = c.id_status
WHERE c.data_abertura >= '2024-03-01' AND c.data_abertura < '2024-06-01'
GROUP BY s.descricao
ORDER BY total_chamados DESC;

-- 2) Desempenho por atendente: chamados recebidos, encerrados e tempo medio de resolucao (horas)
--    LEFT JOIN (atendente sem chamado tambem aparece) + COUNT + AVG + filtro por data.
--    O filtro de data fica no ON para o LEFT JOIN nao virar INNER JOIN.
--    COUNT(c.data_fechamento) ignora NULL = so conta os encerrados; AVG tambem ignora NULL.
SELECT a.nome,
       a.setor,
       COUNT(c.id_chamado)      AS chamados_recebidos,
       COUNT(c.data_fechamento) AS chamados_encerrados,
       ROUND(AVG(TIMESTAMPDIFF(HOUR, c.data_abertura, c.data_fechamento)), 1) AS media_horas_resolucao
FROM ATENDENTE a
LEFT JOIN CHAMADO c
       ON c.id_atendente = a.id_atendente
      AND c.data_abertura >= '2024-02-01' AND c.data_abertura < '2024-06-01'
GROUP BY a.id_atendente, a.nome, a.setor
ORDER BY chamados_recebidos DESC, a.nome;

-- 3) Chamados por tipo de associado (Motorista, Transportadora, Seguradora...)
--    JOIN + COUNT (total e distintos) + GROUP BY + filtro por data
SELECT ass.tipo                          AS tipo_associado,
       COUNT(*)                          AS total_chamados,
       COUNT(DISTINCT ass.id_associado)  AS associados_distintos
FROM CHAMADO c
JOIN ASSOCIADO ass ON ass.id_associado = c.id_associado
WHERE c.data_abertura >= '2024-02-01' AND c.data_abertura < '2024-06-01'
GROUP BY ass.tipo
ORDER BY total_chamados DESC;

-- 4) Tempo medio de resolucao por prioridade (so chamados Resolvidos ou Fechados)
--    JOIN + COUNT + AVG + GROUP BY + filtro por data
--    Prioridade: B = Baixa, M = Media, A = Alta, C = Critica
SELECT c.prioridade,
       COUNT(*) AS chamados_encerrados,
       ROUND(AVG(TIMESTAMPDIFF(HOUR, c.data_abertura, c.data_fechamento)), 1) AS media_horas_resolucao
FROM CHAMADO c
JOIN STATUS_CHAMADO s ON s.id_status = c.id_status
WHERE s.descricao IN ('Resolvido', 'Fechado')
  AND c.data_fechamento IS NOT NULL
  AND c.data_abertura >= '2024-03-01' AND c.data_abertura < '2024-06-01'
GROUP BY c.prioridade
ORDER BY FIELD(c.prioridade, 'C', 'A', 'M', 'B');

-- 5) Interacoes registradas por chamado (historico de atendimento) a partir de fevereiro/2024
--    JOIN (3 tabelas) + COUNT + GROUP BY + HAVING + filtro por data
SELECT c.id_chamado,
       c.titulo,
       a.nome                    AS atendente,
       COUNT(h.id_historico)     AS interacoes
FROM HISTORICO_ATENDIMENTO h
JOIN CHAMADO   c ON c.id_chamado   = h.id_chamado
JOIN ATENDENTE a ON a.id_atendente = h.id_atendente
WHERE h.data_hora >= '2024-02-01'
GROUP BY c.id_chamado, c.titulo, a.nome
HAVING COUNT(h.id_historico) >= 2
ORDER BY interacoes DESC, c.id_chamado;

-- 6) Chamados abertos por mes
--    COUNT + GROUP BY (mes extraido da data) + filtro por data
SELECT DATE_FORMAT(c.data_abertura, '%Y-%m') AS mes,
       COUNT(*)                              AS chamados_abertos,
       SUM(c.prioridade IN ('A', 'C'))       AS alta_ou_critica
FROM CHAMADO c
WHERE c.data_abertura >= '2024-02-01' AND c.data_abertura < '2024-06-01'
GROUP BY DATE_FORMAT(c.data_abertura, '%Y-%m')
ORDER BY mes;

-- =====================================================================
-- BLOCO 2 - ACIDENTES (BASE PRF)
-- =====================================================================

-- 7) Acidentes por UF: total, mortos e media de feridos graves (janeiro/2024), so UFs com 2+ acidentes
--    JOIN + COUNT + SUM + AVG + GROUP BY + HAVING + filtro por data
SELECT l.uf,
       COUNT(*)                            AS total_acidentes,
       SUM(a.mortos)                       AS total_mortos,
       ROUND(AVG(a.feridos_graves), 2)     AS media_feridos_graves
FROM ACIDENTE a
JOIN LOCALIZACAO l ON l.id_localizacao = a.id_localizacao
WHERE a.data_inversa BETWEEN '2024-01-01' AND '2024-01-31'
GROUP BY l.uf
HAVING COUNT(*) >= 2
ORDER BY total_acidentes DESC, l.uf;

-- 8) Media de vitimas por condicao meteorologica
--    JOIN + COUNT + AVG + GROUP BY + filtro por data
SELECT cv.condicao_meteorologica,
       COUNT(*) AS total_acidentes,
       ROUND(AVG(a.feridos_leves + a.feridos_graves + a.mortos), 2) AS media_vitimas
FROM ACIDENTE a
JOIN CONDICAO_VIA_AMBIENTE cv ON cv.id_condicao_via_ambiente = a.id_condicao_via_ambiente
WHERE a.data_inversa BETWEEN '2024-01-01' AND '2024-01-31'
GROUP BY cv.condicao_meteorologica
ORDER BY total_acidentes DESC;

-- 9) Top 5 causas principais de acidente
--    JOIN (3 tabelas, N:N) + COUNT + GROUP BY + filtro por data
SELECT ca.causa_acidente,
       COUNT(*) AS ocorrencias
FROM ACIDENTE a
JOIN ACIDENTE_CAUSA ac ON ac.id_acidente       = a.id_acidente
JOIN CAUSA_ACIDENTE ca ON ca.id_causa_acidente = ac.id_causa_acidente
WHERE ac.causa_principal = TRUE
  AND a.data_inversa BETWEEN '2024-01-01' AND '2024-01-31'
GROUP BY ca.id_causa_acidente, ca.causa_acidente
ORDER BY ocorrencias DESC, ca.causa_acidente
LIMIT 5;

-- 10) Frota envolvida: quantidade e idade media dos veiculos por tipo
--     JOIN + COUNT + AVG + GROUP BY + filtro por data
--     Idade do veiculo = ano do acidente - ano de fabricacao.
SELECT v.tipo_veiculo,
       COUNT(*) AS total_veiculos,
       ROUND(AVG(YEAR(a.data_inversa) - v.ano_fabricacao_veiculo), 1) AS idade_media_anos
FROM VEICULO v
JOIN ACIDENTE a ON a.id_acidente = v.id_acidente
WHERE a.data_inversa BETWEEN '2024-01-01' AND '2024-01-31'
  AND v.ano_fabricacao_veiculo > 0
GROUP BY v.tipo_veiculo
HAVING COUNT(*) >= 3
ORDER BY total_veiculos DESC;

-- 11) Pessoas envolvidas: quantidade e idade media por tipo de envolvimento e estado fisico
--     JOIN (3 tabelas) + COUNT + AVG + GROUP BY + filtro por data
SELECT e.tipo_envolvido,
       e.estado_fisico,
       COUNT(*)                 AS total_pessoas,
       ROUND(AVG(p.idade), 1)   AS idade_media
FROM ENVOLVIMENTO e
JOIN PESSOA   p ON p.pesid        = e.pesid
JOIN ACIDENTE a ON a.id_acidente  = e.id_acidente
WHERE a.data_inversa BETWEEN '2024-01-01' AND '2024-01-31'
  AND p.idade > 0
GROUP BY e.tipo_envolvido, e.estado_fisico
ORDER BY total_pessoas DESC;

-- =====================================================================
-- BLOCO 3 - INTEGRACAO (CHAMADOS x ACIDENTES)
-- =====================================================================

-- 12) Chamados vinculados a acidentes, por UF
--     JOIN (3 tabelas) + COUNT + AVG + GROUP BY + filtro por data
--     Chamados sem acidente associado (id_acidente NULL) ficam de fora no INNER JOIN.
SELECT l.uf,
       COUNT(*)                         AS chamados,
       SUM(a.mortos)                    AS mortos_nos_acidentes,
       ROUND(AVG(a.feridos_graves), 2)  AS media_feridos_graves
FROM CHAMADO c
JOIN ACIDENTE    a ON a.id_acidente     = c.id_acidente
JOIN LOCALIZACAO l ON l.id_localizacao  = a.id_localizacao
WHERE c.data_abertura >= '2024-02-01' AND c.data_abertura < '2024-06-01'
GROUP BY l.uf
ORDER BY chamados DESC, l.uf;
