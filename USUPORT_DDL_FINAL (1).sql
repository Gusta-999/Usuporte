-- USUPORT - Modelo fisico conforme DER enviado

-- MySQL 8.0+
CREATE DATABASE IF NOT EXISTS usuport CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE usuport;

CREATE TABLE IF NOT EXISTS LOCALIZACAO (
 id_localizacao INT AUTO_INCREMENT PRIMARY KEY,
 uf CHAR(2), br SMALLINT, km DECIMAL(10,3), municipio VARCHAR(100),
 latitude DECIMAL(10,7), longitude DECIMAL(10,7)
);
CREATE TABLE IF NOT EXISTS UNIDADE_POLICIAL (
 id_unidade_policial INT AUTO_INCREMENT PRIMARY KEY,
 regional VARCHAR(50), delegacia VARCHAR(80), uop VARCHAR(80)
);
CREATE TABLE IF NOT EXISTS CONDICAO_VIA_AMBIENTE (
 id_condicao_via_ambiente INT AUTO_INCREMENT PRIMARY KEY,
 condicao_meteorologica VARCHAR(40), tipo_pista VARCHAR(30),
 tracado_via VARCHAR(80), uso_solo BOOLEAN
);
CREATE TABLE IF NOT EXISTS ACIDENTE (
 id_acidente INT PRIMARY KEY,
 data_inversa DATE, horario TIME, classificacao_acidente VARCHAR(60),
 fase_dia VARCHAR(20), sentido_via VARCHAR(20), ilesos SMALLINT,
 feridos_leves SMALLINT, feridos_graves SMALLINT, mortos SMALLINT,
 id_localizacao INT, id_unidade_policial INT, id_condicao_via_ambiente INT,
 CONSTRAINT fk_acidente_localizacao FOREIGN KEY (id_localizacao) REFERENCES LOCALIZACAO(id_localizacao),
 CONSTRAINT fk_acidente_unidade FOREIGN KEY (id_unidade_policial) REFERENCES UNIDADE_POLICIAL(id_unidade_policial),
 CONSTRAINT fk_acidente_condicao FOREIGN KEY (id_condicao_via_ambiente) REFERENCES CONDICAO_VIA_AMBIENTE(id_condicao_via_ambiente)
);
CREATE TABLE IF NOT EXISTS CAUSA_ACIDENTE (
 id_causa_acidente INT AUTO_INCREMENT PRIMARY KEY,
 causa_acidente VARCHAR(160) UNIQUE
);
CREATE TABLE IF NOT EXISTS TIPO_ACIDENTE (
 id_tipo_acidente INT AUTO_INCREMENT PRIMARY KEY,
 tipo_acidente VARCHAR(100) UNIQUE
);
CREATE TABLE IF NOT EXISTS PESSOA (
 pesid INT PRIMARY KEY,
 idade SMALLINT, sexo VARCHAR(20)
);
CREATE TABLE IF NOT EXISTS VEICULO (
 id_veiculo INT AUTO_INCREMENT PRIMARY KEY,
 id_acidente INT NOT NULL, tipo_veiculo VARCHAR(60), marca VARCHAR(80),
 ano_fabricacao_veiculo SMALLINT,
 CONSTRAINT fk_veiculo_acidente FOREIGN KEY (id_acidente) REFERENCES ACIDENTE(id_acidente)
);
CREATE TABLE IF NOT EXISTS ACIDENTE_CAUSA (
 id_acidente INT NOT NULL,
 id_causa_acidente INT NOT NULL,
 causa_principal BOOLEAN,
 PRIMARY KEY (id_acidente,id_causa_acidente),
 CONSTRAINT fk_acausa_acidente FOREIGN KEY (id_acidente) REFERENCES ACIDENTE(id_acidente),
 CONSTRAINT fk_acausa_causa FOREIGN KEY (id_causa_acidente) REFERENCES CAUSA_ACIDENTE(id_causa_acidente)
);
CREATE TABLE IF NOT EXISTS ACIDENTE_TIPO (
 id_acidente INT NOT NULL,
 ordem_tipo_acidente SMALLINT NOT NULL,
 id_tipo_acidente INT NOT NULL,
 PRIMARY KEY (id_acidente,ordem_tipo_acidente),
 CONSTRAINT fk_atipo_acidente FOREIGN KEY (id_acidente) REFERENCES ACIDENTE(id_acidente),
 CONSTRAINT fk_atipo_tipo FOREIGN KEY (id_tipo_acidente) REFERENCES TIPO_ACIDENTE(id_tipo_acidente)
);
CREATE TABLE IF NOT EXISTS ENVOLVIMENTO (
 id_acidente INT NOT NULL,
 pesid INT NOT NULL,
 id_veiculo INT NULL,
 tipo_envolvido VARCHAR(30), estado_fisico VARCHAR(30),
 PRIMARY KEY (id_acidente,pesid),
 CONSTRAINT fk_env_acidente FOREIGN KEY (id_acidente) REFERENCES ACIDENTE(id_acidente),
 CONSTRAINT fk_env_pessoa FOREIGN KEY (pesid) REFERENCES PESSOA(pesid),
 CONSTRAINT fk_env_veiculo FOREIGN KEY (id_veiculo) REFERENCES VEICULO(id_veiculo)
);
CREATE TABLE IF NOT EXISTS ASSOCIADO (
 id_associado INT AUTO_INCREMENT PRIMARY KEY,
 nome VARCHAR(120), tipo VARCHAR(30), email VARCHAR(100) UNIQUE,
 telefone VARCHAR(20)
);
CREATE TABLE IF NOT EXISTS STATUS_CHAMADO (
 id_status INT AUTO_INCREMENT PRIMARY KEY,
 descricao VARCHAR(30) UNIQUE
);
CREATE TABLE IF NOT EXISTS ATENDENTE (
 id_atendente INT AUTO_INCREMENT PRIMARY KEY,
 nome VARCHAR(120), email VARCHAR(100) UNIQUE, setor VARCHAR(50)
);
CREATE TABLE IF NOT EXISTS CHAMADO (
 id_chamado INT AUTO_INCREMENT PRIMARY KEY,
 id_associado INT NOT NULL, id_acidente INT NULL, id_atendente INT NULL,
 id_status INT NOT NULL, titulo VARCHAR(150), descricao TEXT,
 prioridade VARCHAR(10), data_abertura DATETIME,
 data_fechamento DATETIME NULL,
 CONSTRAINT chk_chamado_prioridade CHECK (prioridade IN ('Baixa','Media','Alta','Critica')),
 CONSTRAINT fk_chamado_associado FOREIGN KEY (id_associado) REFERENCES ASSOCIADO(id_associado),
 CONSTRAINT fk_chamado_acidente FOREIGN KEY (id_acidente) REFERENCES ACIDENTE(id_acidente),
 CONSTRAINT fk_chamado_atendente FOREIGN KEY (id_atendente) REFERENCES ATENDENTE(id_atendente),
 CONSTRAINT fk_chamado_status FOREIGN KEY (id_status) REFERENCES STATUS_CHAMADO(id_status)
);
CREATE TABLE IF NOT EXISTS HISTORICO_ATENDIMENTO (
 id_historico INT AUTO_INCREMENT PRIMARY KEY,
 id_chamado INT NOT NULL, id_atendente INT NOT NULL,
 data_hora DATETIME, descricao TEXT,
 CONSTRAINT fk_hist_chamado FOREIGN KEY (id_chamado) REFERENCES CHAMADO(id_chamado),
 CONSTRAINT fk_hist_atendente FOREIGN KEY (id_atendente) REFERENCES ATENDENTE(id_atendente)
);

-- Indices para consultas frequentes
CREATE INDEX idx_acidente_data ON ACIDENTE(data_inversa);
CREATE INDEX idx_acidente_localizacao ON ACIDENTE(id_localizacao);
CREATE INDEX idx_chamado_abertura ON CHAMADO(data_abertura);
CREATE INDEX idx_chamado_prioridade ON CHAMADO(prioridade);

-- Exemplos didaticos de ALTER e DROP, sem alterar as 16 tabelas finais:
-- ALTER TABLE ASSOCIADO ADD COLUMN observacao VARCHAR(100);
-- ALTER TABLE ASSOCIADO DROP COLUMN observacao;
-- DROP TABLE IF EXISTS tabela_teste;

-- Conferencia:
SHOW TABLES;



USE usuport;

CREATE TABLE IF NOT EXISTS TESTE_DDL (
    id INT PRIMARY KEY,
    nome VARCHAR(100)
);

ALTER TABLE TESTE_DDL
ADD COLUMN observacao VARCHAR(100);

DROP TABLE IF EXISTS TESTE_DDL;