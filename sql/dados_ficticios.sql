-- ASSOCIADO (dados ficticios para demonstracao)
INSERT INTO ASSOCIADO (id_associado, nome, tipo, email, telefone) VALUES
(1,'Carlos Henrique Souza','Motorista','carlos.souza@email.com','(71) 99111-0001'),
(2,'Transportes Rota Sul Ltda','Transportadora','contato@rotasul.com.br','(41) 3322-0002'),
(3,'Mariana Alves Costa','Motorista','mariana.costa@email.com','(31) 99111-0003'),
(4,'Seguradora Horizonte S.A.','Seguradora','sinistros@horizonte.com.br','(11) 3000-0004'),
(5,'Joao Pedro Lima','Motorista','joao.lima@email.com','(62) 99111-0005'),
(6,'Logistica Brasil Central','Transportadora','atendimento@lbcentral.com.br','(61) 3200-0006'),
(7,'Fernanda Ribeiro','Motorista','fernanda.ribeiro@email.com','(21) 99111-0007'),
(8,'Prefeitura de Anapolis','Orgao Publico','transito@anapolis.go.gov.br','(62) 3300-0008'),
(9,'Ricardo Menezes','Motorista','ricardo.menezes@email.com','(48) 99111-0009'),
(10,'Cooperativa Cargas Minas','Transportadora','cooperativa@cargasminas.com.br','(31) 3400-0010');

-- STATUS_CHAMADO
INSERT INTO STATUS_CHAMADO (id_status, descricao) VALUES
(1,'Aberto'),(2,'Em Andamento'),(3,'Aguardando Cliente'),(4,'Resolvido'),(5,'Fechado'),(6,'Cancelado');

-- ATENDENTE (dados ficticios)
INSERT INTO ATENDENTE (id_atendente, nome, email, setor) VALUES
(1,'Paula Nogueira','paula.nogueira@usuport.com.br','Suporte N1'),
(2,'Rafael Duarte','rafael.duarte@usuport.com.br','Suporte N1'),
(3,'Camila Torres','camila.torres@usuport.com.br','Suporte N2'),
(4,'Bruno Azevedo','bruno.azevedo@usuport.com.br','Analise de Dados');

-- CHAMADO (dados ficticios)
INSERT INTO CHAMADO (id_chamado, id_associado, id_acidente, id_atendente, id_status, titulo, descricao, prioridade, data_abertura, data_fechamento) VALUES
(1, 2, 571778, NULL, 1, 'Consulta sobre acidente na rodovia', 'Chamado de exemplo 1: consulta sobre acidente na rodovia.', 'M', '2024-02-10 10:00:00', NULL),
(2, 3, 571781, 3, 2, 'Solicitacao de relatorio de sinistro', 'Chamado de exemplo 2: solicitacao de relatorio de sinistro.', 'B', '2024-02-19 11:00:00', NULL),
(3, 4, 571785, 4, 2, 'Divergencia no numero de vitimas', 'Chamado de exemplo 3: divergencia no numero de vitimas.', 'A', '2024-02-28 12:00:00', NULL),
(4, 5, NULL, 1, 3, 'Pedido de correcao de localizacao', 'Chamado de exemplo 4: pedido de correcao de localizacao.', 'M', '2024-03-08 13:00:00', NULL),
(5, 6, 571806, 2, 4, 'Acidente com vitima fatal - suporte urgente', 'Chamado de exemplo 5: acidente com vitima fatal - suporte urgente.', 'C', '2024-03-17 14:00:00', '2024-03-20 16:00:00'),
(6, 7, 571794, 3, 5, 'Duvida sobre causa principal', 'Chamado de exemplo 6: duvida sobre causa principal.', 'B', '2024-03-26 15:00:00', '2024-03-29 17:00:00'),
(7, 8, 571798, 4, 5, 'Atualizacao de dados do veiculo', 'Chamado de exemplo 7: atualizacao de dados do veiculo.', 'M', '2024-04-04 16:00:00', '2024-04-07 18:00:00'),
(8, 9, NULL, 1, 2, 'Reclamacao de atraso no atendimento', 'Chamado de exemplo 8: reclamacao de atraso no atendimento.', 'A', '2024-04-13 17:00:00', NULL),
(9, 10, 571804, NULL, 1, 'Pedido de historico de ocorrencias no trecho', 'Chamado de exemplo 9: pedido de historico de ocorrencias no trecho.', 'B', '2024-04-22 18:00:00', NULL),
(10, 1, 571808, 3, 4, 'Erro no horario registrado', 'Chamado de exemplo 10: erro no horario registrado.', 'M', '2024-05-01 19:00:00', '2024-05-04 21:00:00'),
(11, 2, 571812, 4, 5, 'Solicitacao de laudo complementar', 'Chamado de exemplo 11: solicitacao de laudo complementar.', 'A', '2024-05-10 20:00:00', '2024-05-13 22:00:00'),
(12, 3, NULL, NULL, 1, 'Consulta geral sobre o sistema', 'Chamado de exemplo 12: consulta geral sobre o sistema.', 'B', '2024-05-19 21:00:00', NULL);

-- HISTORICO_ATENDIMENTO (dados ficticios)
INSERT INTO HISTORICO_ATENDIMENTO (id_historico, id_chamado, id_atendente, data_hora, descricao) VALUES
(1, 2, 3, '2024-02-19 13:00:00', 'Chamado assumido pelo atendente e analise iniciada.'),
(2, 3, 4, '2024-02-28 14:00:00', 'Chamado assumido pelo atendente e analise iniciada.'),
(3, 4, 1, '2024-03-08 15:00:00', 'Chamado assumido pelo atendente e analise iniciada.'),
(4, 4, 1, '2024-03-09 13:00:00', 'Retorno enviado ao associado com as informacoes solicitadas.'),
(5, 5, 2, '2024-03-17 16:00:00', 'Chamado assumido pelo atendente e analise iniciada.'),
(6, 5, 2, '2024-03-18 14:00:00', 'Retorno enviado ao associado com as informacoes solicitadas.'),
(7, 5, 2, '2024-03-20 16:00:00', 'Demanda concluida e chamado encerrado.'),
(8, 6, 3, '2024-03-26 17:00:00', 'Chamado assumido pelo atendente e analise iniciada.'),
(9, 6, 3, '2024-03-27 15:00:00', 'Retorno enviado ao associado com as informacoes solicitadas.'),
(10, 6, 3, '2024-03-29 17:00:00', 'Demanda concluida e chamado encerrado.'),
(11, 7, 4, '2024-04-04 18:00:00', 'Chamado assumido pelo atendente e analise iniciada.'),
(12, 7, 4, '2024-04-05 16:00:00', 'Retorno enviado ao associado com as informacoes solicitadas.'),
(13, 7, 4, '2024-04-07 18:00:00', 'Demanda concluida e chamado encerrado.'),
(14, 8, 1, '2024-04-13 19:00:00', 'Chamado assumido pelo atendente e analise iniciada.'),
(15, 10, 3, '2024-05-01 21:00:00', 'Chamado assumido pelo atendente e analise iniciada.'),
(16, 10, 3, '2024-05-02 19:00:00', 'Retorno enviado ao associado com as informacoes solicitadas.'),
(17, 10, 3, '2024-05-04 21:00:00', 'Demanda concluida e chamado encerrado.'),
(18, 11, 4, '2024-05-10 22:00:00', 'Chamado assumido pelo atendente e analise iniciada.'),
(19, 11, 4, '2024-05-11 20:00:00', 'Retorno enviado ao associado com as informacoes solicitadas.'),
(20, 11, 4, '2024-05-13 22:00:00', 'Demanda concluida e chamado encerrado.');
