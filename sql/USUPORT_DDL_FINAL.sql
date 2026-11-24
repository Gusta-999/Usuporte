-- USUPORT | DDL completo conforme Dicionario de Dados atualizado
CREATE DATABASE IF NOT EXISTS usuport CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE usuport;

CREATE TABLE LOCALIZACAO (
 id_localizacao INT NOT NULL AUTO_INCREMENT,
 uf CHAR(2), br SMALLINT, km DECIMAL(10,3), municipio VARCHAR(100),
 latitude DECIMAL(10,7), longitude DECIMAL(10,7),
 PRIMARY KEY (id_localizacao)
) ENGINE=InnoDB;

CREATE TABLE UNIDADE_POLICIAL (
 id_unidade_policial INT NOT NULL AUTO_INCREMENT,
 regional VARCHAR(20), delegacia VARCHAR(100), uop VARCHAR(20),
 PRIMARY KEY (id_unidade_policial)
) ENGINE=InnoDB;

CREATE TABLE CONDICAO_VIA_AMBIENTE (
 id_condicao_via_ambiente INT NOT NULL AUTO_INCREMENT,
 condicao_meteorologica VARCHAR(100), tipo_pista VARCHAR(40),
 tracado_via VARCHAR(40), uso_solo BOOLEAN,
 PRIMARY KEY (id_condicao_via_ambiente)
) ENGINE=InnoDB;

CREATE TABLE ACIDENTE (
 id_acidente INT NOT NULL AUTO_INCREMENT,
 data_inversa DATE, horario TIME, classificacao_acidente VARCHAR(80),
 fase_dia VARCHAR(20), sentido_via VARCHAR(20),
 ilesos SMALLINT, feridos_leves SMALLINT, feridos_graves SMALLINT, mortos SMALLINT,
 id_localizacao INT NOT NULL, id_unidade_policial INT NOT NULL,
 id_condicao_via_ambiente INT NOT NULL,
 PRIMARY KEY (id_acidente),
 CONSTRAINT fk_acidente_localizacao FOREIGN KEY (id_localizacao) REFERENCES LOCALIZACAO(id_localizacao),
 CONSTRAINT fk_acidente_unidade FOREIGN KEY (id_unidade_policial) REFERENCES UNIDADE_POLICIAL(id_unidade_policial),
 CONSTRAINT fk_acidente_condicao FOREIGN KEY (id_condicao_via_ambiente) REFERENCES CONDICAO_VIA_AMBIENTE(id_condicao_via_ambiente)
) ENGINE=InnoDB;

CREATE TABLE PESSOA (
 pesid INT NOT NULL AUTO_INCREMENT, idade SMALLINT, sexo VARCHAR(20),
 PRIMARY KEY (pesid)
) ENGINE=InnoDB;

CREATE TABLE VEICULO (
 id_veiculo INT NOT NULL AUTO_INCREMENT, id_acidente INT NOT NULL,
 tipo_veiculo VARCHAR(80), marca VARCHAR(80), ano_fabricacao_veiculo SMALLINT,
 PRIMARY KEY (id_veiculo),
 CONSTRAINT fk_veiculo_acidente FOREIGN KEY (id_acidente) REFERENCES ACIDENTE(id_acidente)
) ENGINE=InnoDB;

CREATE TABLE ENVOLVIMENTO (
 id_acidente INT NOT NULL, pesid INT NOT NULL, id_veiculo INT NULL,
 tipo_envolvido VARCHAR(30), estado_fisico VARCHAR(30),
 PRIMARY KEY (id_acidente,pesid),
 CONSTRAINT fk_envolvimento_acidente FOREIGN KEY (id_acidente) REFERENCES ACIDENTE(id_acidente),
 CONSTRAINT fk_envolvimento_pessoa FOREIGN KEY (pesid) REFERENCES PESSOA(pesid),
 CONSTRAINT fk_envolvimento_veiculo FOREIGN KEY (id_veiculo) REFERENCES VEICULO(id_veiculo)
) ENGINE=InnoDB;

CREATE TABLE CAUSA_ACIDENTE (
 id_causa_acidente INT NOT NULL AUTO_INCREMENT, causa_acidente VARCHAR(160),
 PRIMARY KEY (id_causa_acidente), UNIQUE KEY uq_causa_acidente (causa_acidente)
) ENGINE=InnoDB;

CREATE TABLE ACIDENTE_CAUSA (
 id_acidente INT NOT NULL, id_causa_acidente INT NOT NULL, causa_principal BOOLEAN,
 PRIMARY KEY (id_acidente,id_causa_acidente),
 CONSTRAINT fk_acidente_causa_acidente FOREIGN KEY (id_acidente) REFERENCES ACIDENTE(id_acidente),
 CONSTRAINT fk_acidente_causa_causa FOREIGN KEY (id_causa_acidente) REFERENCES CAUSA_ACIDENTE(id_causa_acidente)
) ENGINE=InnoDB;

CREATE TABLE TIPO_ACIDENTE (
 id_tipo_acidente INT NOT NULL AUTO_INCREMENT, tipo_acidente VARCHAR(100),
 PRIMARY KEY (id_tipo_acidente), UNIQUE KEY uq_tipo_acidente (tipo_acidente)
) ENGINE=InnoDB;

CREATE TABLE ACIDENTE_TIPO (
 id_acidente INT NOT NULL, ordem_tipo_acidente SMALLINT NOT NULL, id_tipo_acidente INT NOT NULL,
 PRIMARY KEY (id_acidente,ordem_tipo_acidente),
 CONSTRAINT fk_acidente_tipo_acidente FOREIGN KEY (id_acidente) REFERENCES ACIDENTE(id_acidente),
 CONSTRAINT fk_acidente_tipo_tipo FOREIGN KEY (id_tipo_acidente) REFERENCES TIPO_ACIDENTE(id_tipo_acidente)
) ENGINE=InnoDB;

CREATE TABLE ASSOCIADO (
 id_associado INT NOT NULL AUTO_INCREMENT, nome VARCHAR(120), tipo VARCHAR(30),
 email VARCHAR(100), telefone VARCHAR(20),
 PRIMARY KEY (id_associado), UNIQUE KEY uq_associado_email (email)
) ENGINE=InnoDB;

CREATE TABLE STATUS_CHAMADO (
 id_status INT NOT NULL AUTO_INCREMENT, descricao VARCHAR(30),
 PRIMARY KEY (id_status), UNIQUE KEY uq_status_descricao (descricao)
) ENGINE=InnoDB;

CREATE TABLE ATENDENTE (
 id_atendente INT NOT NULL AUTO_INCREMENT, nome VARCHAR(120),
 email VARCHAR(100), setor VARCHAR(80),
 PRIMARY KEY (id_atendente), UNIQUE KEY uq_atendente_email (email)
) ENGINE=InnoDB;

CREATE TABLE CHAMADO (
 id_chamado INT NOT NULL AUTO_INCREMENT, id_associado INT NOT NULL,
 id_acidente INT NULL, id_atendente INT NULL, id_status INT NOT NULL,
 titulo VARCHAR(150), descricao TEXT, prioridade CHAR(1),
 data_abertura DATETIME, data_fechamento DATETIME NULL,
 PRIMARY KEY (id_chamado),
 CONSTRAINT chk_chamado_prioridade CHECK (prioridade IN ('B','M','A','C')),
 CONSTRAINT fk_chamado_associado FOREIGN KEY (id_associado) REFERENCES ASSOCIADO(id_associado),
 CONSTRAINT fk_chamado_acidente FOREIGN KEY (id_acidente) REFERENCES ACIDENTE(id_acidente),
 CONSTRAINT fk_chamado_atendente FOREIGN KEY (id_atendente) REFERENCES ATENDENTE(id_atendente),
 CONSTRAINT fk_chamado_status FOREIGN KEY (id_status) REFERENCES STATUS_CHAMADO(id_status)
) ENGINE=InnoDB;

CREATE TABLE HISTORICO_ATENDIMENTO (
 id_historico INT NOT NULL AUTO_INCREMENT, id_chamado INT NOT NULL,
 id_atendente INT NOT NULL, data_hora DATETIME, descricao TEXT,
 PRIMARY KEY (id_historico),
 CONSTRAINT fk_historico_chamado FOREIGN KEY (id_chamado) REFERENCES CHAMADO(id_chamado),
 CONSTRAINT fk_historico_atendente FOREIGN KEY (id_atendente) REFERENCES ATENDENTE(id_atendente)
) ENGINE=InnoDB;

-- Indices complementares para consultas por data e estado
CREATE INDEX idx_acidente_data ON ACIDENTE(data_inversa);
CREATE INDEX idx_chamado_data_abertura ON CHAMADO(data_abertura);
CREATE INDEX idx_chamado_prioridade ON CHAMADO(prioridade);

SHOW TABLES;
