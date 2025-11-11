-- 0) CRIAÇÃO / REINICIALIZAÇÃO DO BANCO
DROP DATABASE IF EXISTS ecommerce;
CREATE DATABASE ecommerce;
USE ecommerce;
DROP USER IF EXISTS 'admin'@'localhost';
DROP USER IF EXISTS 'gerente'@'localhost';
DROP USER IF EXISTS 'funcionario'@'localhost';

-- 1) TABELAS

CREATE TABLE cliente (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(50) NOT NULL,
    idade INT,
    sexo CHAR(1) CHECK (sexo IN ('m', 'f', 'o')),
    data_nascimento DATE
);

CREATE TABLE cliente_especial (
    id_cliente INT PRIMARY KEY,
    cashback DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    FOREIGN KEY (id_cliente) REFERENCES cliente(id) ON DELETE CASCADE
);

CREATE TABLE vendedor (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(50) NOT NULL,
    causa_social VARCHAR(100),
    tipo VARCHAR(50),
    nota_media DECIMAL(3,2) DEFAULT 0.00,
    salario DECIMAL(10,2) NOT NULL
);

CREATE TABLE funcionario_especial(
    id INT PRIMARY KEY AUTO_INCREMENT,
    id_vendedor INT UNIQUE,
    bonus DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    FOREIGN KEY (id_vendedor) REFERENCES vendedor(id) ON DELETE CASCADE
);

CREATE TABLE produto (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(50),
    descricao TEXT,
    quantidade_estoque INT NOT NULL,
    valor DECIMAL(10,2) NOT NULL,
    observacoes TEXT,
    id_vendedor INT,
    FOREIGN KEY (id_vendedor) REFERENCES vendedor(id)
);

CREATE TABLE transportadora (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(50),
    cidade VARCHAR(50)
);

CREATE TABLE transporte (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_transportadora INT,
    id_venda INT,
    valor DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    FOREIGN KEY (id_transportadora) REFERENCES transportadora(id)
);

CREATE TABLE log_bonus (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mensagem VARCHAR(255),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE venda (
    id INT PRIMARY KEY AUTO_INCREMENT,
    data_venda DATE,
    hora_venda TIME,
    valor DECIMAL(10,2),
    endereco VARCHAR(100),
    id_cliente INT,
    id_transporte INT,
    FOREIGN KEY (id_cliente) REFERENCES cliente(id),
    FOREIGN KEY (id_transporte) REFERENCES transporte(id)
    
);

CREATE TABLE venda_produto(
    id INT PRIMARY KEY AUTO_INCREMENT,
    id_venda INT,
    id_produto INT,
    qtd INT NOT NULL DEFAULT 1,
    valor DECIMAL(10, 2) NOT NULL,
    obs VARCHAR(100),
    FOREIGN KEY (id_venda) REFERENCES venda(id),
    FOREIGN KEY (id_produto) REFERENCES produto(id)
);
CREATE TABLE log_cashback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mensagem VARCHAR(255),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE voucher (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT,
    valor DECIMAL(10,2),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_cliente) REFERENCES cliente(id)
);

-- 2) FUNÇÕES

DELIMITER $$

-- Calcula_idade(cliente_id)
CREATE FUNCTION Calcula_idade(cliente_id INT)
RETURNS INT
NOT DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE nasc DATE;
    DECLARE idade INT;
    SELECT data_nascimento INTO nasc FROM cliente WHERE id = cliente_id;
    SET idade = TIMESTAMPDIFF(YEAR, nasc, CURDATE());
    RETURN idade;
END$$

-- Soma_fretes(destino)
DROP FUNCTION IF EXISTS ecommerce.Soma_fretes;
DELIMITER $$
CREATE FUNCTION ecommerce.Soma_fretes(p_destino VARCHAR(100))
RETURNS DECIMAL(10,2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE total DECIMAL(10,2) DEFAULT 0.00;
    SELECT IFNULL(SUM(t.valor),0.00) INTO total
    FROM transporte t
    JOIN venda v ON v.id = t.id_venda
    -- normaliza e compara em lowercase e sem espaços nas extremidades
    WHERE LOWER(TRIM(v.endereco)) = LOWER(TRIM(p_destino));
    RETURN total;
END$$
DELIMITER ;

DELIMITER $$

-- Arrecadado(data, id_vendedor)
CREATE FUNCTION Arrecadado(p_data DATE, p_id_vendedor INT)
RETURNS DECIMAL(10,2)
NOT DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE total DECIMAL(10,2);
    SELECT IFNULL(SUM(vp.valor),0) INTO total
    FROM venda_produto vp
    JOIN produto p ON vp.id_produto = p.id
    JOIN venda v ON v.id = vp.id_venda
    WHERE v.data_venda = p_data AND p.id_vendedor = p_id_vendedor;
    RETURN total;
END$$

DELIMITER ;

-- 3) TRIGGERS

DELIMITER $$

-- 3.1 Trigger: vendedor_especial
CREATE TRIGGER trg_vendedor_especial
AFTER INSERT ON venda_produto
FOR EACH ROW
BEGIN
    DECLARE total_vendas DECIMAL(10,2);
    DECLARE bonus_total DECIMAL(10,2);
    DECLARE vendedor_id INT;

    SELECT id_vendedor INTO vendedor_id FROM produto WHERE id = NEW.id_produto;

    SELECT SUM(vp.valor)
    INTO total_vendas
    FROM venda_produto vp
    JOIN produto p ON vp.id_produto = p.id
    WHERE p.id_vendedor = vendedor_id;

    IF total_vendas > 1000 THEN
        SET bonus_total = total_vendas * 0.05;
        INSERT INTO funcionario_especial (id_vendedor, bonus)
        VALUES (vendedor_id, bonus_total)
        ON DUPLICATE KEY UPDATE bonus = bonus_total;

        INSERT INTO log_bonus (mensagem)
        VALUES (CONCAT('Bônus total necessário para custear: R$ ', ROUND(bonus_total,2)));
    END IF;
END$$

-- 3.2 Trigger: cliente_especial
CREATE TRIGGER trg_cliente_especial
AFTER INSERT ON venda
FOR EACH ROW
BEGIN
    DECLARE total_cliente DECIMAL(10,2);
    DECLARE cashback_total DECIMAL(10,2);

    SELECT SUM(valor)
    INTO total_cliente
    FROM venda
    WHERE id_cliente = NEW.id_cliente;

    IF total_cliente > 500 THEN
        SET cashback_total = total_cliente * 0.02;
        INSERT INTO cliente_especial (id_cliente, cashback)
        VALUES (NEW.id_cliente, cashback_total)
        ON DUPLICATE KEY UPDATE cashback = cashback_total;

        INSERT INTO log_cashback (mensagem)
        VALUES (CONCAT('Cashback total necessário: R$ ', ROUND(cashback_total,2)));
    END IF;
END$$

-- 3.3 Trigger: remover cliente especial com cashback zerado
CREATE TRIGGER trg_remove_cliente_especial
AFTER UPDATE ON cliente_especial
FOR EACH ROW
BEGIN
    IF NEW.cashback = 0 THEN
        DELETE FROM cliente_especial WHERE id_cliente = NEW.id_cliente;
    END IF;
END$$

DELIMITER ;

-- 5) VIEWS (3 views conforme solicitado)

-- 1) Total por produto (inclui vendedor)
CREATE OR REPLACE VIEW ecommerce.v_produto_vendas_totais AS
SELECT
  p.id                   AS produto_id,
  p.nome                 AS produto_nome,
  p.id_vendedor          AS vendedor_id,
  v.nome                 AS vendedor_nome,
  COALESCE(SUM(vp.qtd),0)    AS total_qtd_vendida,
  COALESCE(SUM(vp.valor),0.00) AS total_ganho
FROM produto p
LEFT JOIN venda_produto vp ON vp.id_produto = p.id
LEFT JOIN vendedor v      ON v.id = p.id_vendedor
GROUP BY p.id, p.nome, p.id_vendedor, v.nome;

-- 2) Cliente: resumo compras e se é especial
CREATE OR REPLACE VIEW ecommerce.v_cliente_compras_e_status AS
SELECT
  c.id                    AS cliente_id,
  c.nome                  AS cliente_nome,
  COUNT(v.id)             AS qtd_compras,
  COALESCE(SUM(v.valor),0.00) AS total_gasto,
  CASE WHEN ce.id_cliente IS NULL THEN 0 ELSE 1 END AS is_cliente_especial
FROM cliente c
LEFT JOIN venda v ON v.id_cliente = c.id
LEFT JOIN cliente_especial ce ON ce.id_cliente = c.id
GROUP BY c.id, c.nome, is_cliente_especial;

-- 3) Vendas mensais por produto (útil para descobrir mês maior/menor)
CREATE OR REPLACE VIEW ecommerce.v_vendas_mensais_produto AS
SELECT
  p.id                          AS produto_id,
  p.nome                        AS produto_nome,
  YEAR(v.data_venda)            AS ano,
  MONTH(v.data_venda)           AS mes,
  COALESCE(SUM(vp.qtd),0)       AS qtd_vendida_no_mes,
  COALESCE(SUM(vp.valor),0.00)  AS ganho_no_mes
FROM venda_produto vp
JOIN venda v       ON v.id = vp.id_venda
JOIN produto p     ON p.id = vp.id_produto
GROUP BY p.id, p.nome, YEAR(v.data_venda), MONTH(v.data_venda);

-- 4) PROCEDURES

DELIMITER $$

-- Reajuste salarial
CREATE PROCEDURE Reajuste(p_percentual DECIMAL(5,2), p_categoria VARCHAR(50))
BEGIN
    UPDATE vendedor
    SET salario = salario + (salario * p_percentual / 100)
    WHERE tipo = p_categoria;
END$$

-- Sorteio de cliente
DELIMITER $$
CREATE PROCEDURE Sorteio()
proc_label: BEGIN
    DECLARE v_id_cliente INT;

    SELECT id INTO v_id_cliente 
    FROM cliente 
    ORDER BY RAND() 
    LIMIT 1;

    IF v_id_cliente IS NULL THEN
        SELECT 'Sem clientes para sortear.' AS mensagem;
        LEAVE proc_label;
    END IF;

    IF EXISTS (SELECT 1 FROM cliente_especial WHERE id_cliente = v_id_cliente) THEN
        INSERT INTO voucher (id_cliente, valor) VALUES (v_id_cliente, 200.00);
        SELECT v_id_cliente AS cliente_sorteado, 200.00 AS valor_voucher;
    ELSE
        INSERT INTO voucher (id_cliente, valor) VALUES (v_id_cliente, 100.00);
        SELECT v_id_cliente AS cliente_sorteado, 100.00 AS valor_voucher;
    END IF;
END$$
DELIMITER ;

-- Venda: reduz estoque

DELIMITER $$

CREATE PROCEDURE Venda(
    IN p_id_produto INT,
    IN p_qtd INT,
    IN p_id_cliente INT,
    IN p_endereco VARCHAR(100)
)
BEGIN
    DECLARE v_valor_produto DECIMAL(10,2);
    DECLARE v_estoque INT;
    DECLARE v_id_venda INT;
    DECLARE v_valor_total DECIMAL(10,2);
    DECLARE v_valor_transporte DECIMAL(10,2);

    -- Verifica se o produto existe e pega valor + estoque
    SELECT quantidade_estoque, valor
    INTO v_estoque, v_valor_produto
    FROM produto
    WHERE id = p_id_produto
    FOR UPDATE;

    IF v_estoque IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Produto não existe.';
    END IF;

    IF v_estoque < p_qtd THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Estoque insuficiente.';
    END IF;

    -- Calcula valores
    SET v_valor_total = v_valor_produto * p_qtd;
    SET v_valor_transporte = v_valor_total * 0.05; -- frete = 5%

    -- Cria a venda
    INSERT INTO venda (data_venda, hora_venda, valor, endereco, id_cliente)
    VALUES (CURDATE(), CURTIME(), v_valor_total, p_endereco, p_id_cliente);

    SET v_id_venda = LAST_INSERT_ID();

    -- Relaciona o produto à venda
    INSERT INTO venda_produto (id_venda, id_produto, qtd, valor, obs)
    VALUES (v_id_venda, p_id_produto, p_qtd, v_valor_produto, CONCAT('Venda de ', p_qtd, ' unidade(s).'));

    -- Atualiza estoque
    UPDATE produto
    SET quantidade_estoque = quantidade_estoque - p_qtd
    WHERE id = p_id_produto;

    -- Registra transporte
    INSERT INTO transporte (id_venda, valor)
    VALUES (v_id_venda, v_valor_transporte);
END$$

DELIMITER ;


DROP PROCEDURE IF EXISTS EstatisticasCompletas
DELIMITER $$

CREATE PROCEDURE EstatisticasCompletas()
BEGIN
    -- tabela temporária com agregados por produto
    CREATE TEMPORARY TABLE IF NOT EXISTS tmp_produtos AS
    SELECT
        p.id AS produto_id,
        p.nome AS produto_nome,
        p.id_vendedor,
        IFNULL(SUM(vp.qtd), 0) AS total_qtd,
        IFNULL(SUM(vp.valor), 0.00) AS total_ganho
    FROM produto p
    LEFT JOIN venda_produto vp ON vp.id_produto = p.id
    GROUP BY p.id, p.nome, p.id_vendedor;

    -- produto mais vendido: prioridade por maior quantidade; em caso de empate, por maior ganho
    SELECT produto_id INTO @produto_mais_id
    FROM tmp_produtos
    ORDER BY total_qtd DESC, total_ganho DESC
    LIMIT 1;

    -- produto menos vendido: consideramos primeiro produtos com total_qtd > 0 (menor >0).
    -- Se não houver vendas (>0), pega o que tiver menor total (possivelmente 0).
    SELECT produto_id INTO @produto_menos_id
    FROM tmp_produtos
    WHERE total_qtd > 0
    ORDER BY total_qtd ASC, total_ganho ASC
    LIMIT 1;

    IF @produto_menos_id IS NULL THEN
        SELECT produto_id INTO @produto_menos_id
        FROM tmp_produtos
        ORDER BY total_qtd ASC, total_ganho ASC
        LIMIT 1;
    END IF;

    -- 1) Resultado: Produto MAIS vendido (com vendedor, total qtd e ganho)

    SELECT
        tp.produto_id,
        tp.produto_nome,
        tp.total_qtd AS total_qtd_vendida,
        tp.total_ganho AS valor_ganho_total,
        v.id   AS vendedor_id,
        v.nome AS vendedor_nome
    FROM tmp_produtos tp
    LEFT JOIN vendedor v ON v.id = tp.id_vendedor
    WHERE tp.produto_id = @produto_mais_id;

    -- 2) Mês de maior e mês de menor vendas do produto MAIS vendido

    -- Mês com maior qtd
    SELECT
        YEAR(venda.data_venda) AS ano,
        MONTH(venda.data_venda) AS mes,
        SUM(vp.qtd)   AS qtd_vendida_no_mes,
        SUM(vp.valor) AS ganho_no_mes
    FROM venda_produto vp
    JOIN venda ON venda.id = vp.id_venda
    WHERE vp.id_produto = @produto_mais_id
    GROUP BY YEAR(venda.data_venda), MONTH(venda.data_venda)
    ORDER BY qtd_vendida_no_mes DESC, ganho_no_mes DESC
    LIMIT 1;

    -- Mês com menor qtd (entre meses que tenham vendas para esse produto)
    SELECT
        YEAR(venda.data_venda) AS ano,
        MONTH(venda.data_venda) AS mes,
        SUM(vp.qtd)   AS qtd_vendida_no_mes,
        SUM(vp.valor) AS ganho_no_mes
    FROM venda_produto vp
    JOIN venda ON venda.id = vp.id_venda
    WHERE vp.id_produto = @produto_mais_id
    GROUP BY YEAR(venda.data_venda), MONTH(venda.data_venda)
    ORDER BY qtd_vendida_no_mes ASC, ganho_no_mes ASC
    LIMIT 1;

    -- 3) Resultado: Produto MENOS vendido (com vendedor, total qtd e ganho)
    
    SELECT
        tp.produto_id,
        tp.produto_nome,
        tp.total_qtd AS total_qtd_vendida,
        tp.total_ganho AS valor_ganho_total,
        v.id   AS vendedor_id,
        v.nome AS vendedor_nome
    FROM tmp_produtos tp
    LEFT JOIN vendedor v ON v.id = tp.id_vendedor
    WHERE tp.produto_id = @produto_menos_id;

    -- 4) Mês de maior e mês de menor vendas do produto MENOS vendido

    SELECT
        YEAR(venda.data_venda) AS ano,
        MONTH(venda.data_venda) AS mes,
        SUM(vp.qtd)   AS qtd_vendida_no_mes,
        SUM(vp.valor) AS ganho_no_mes
    FROM venda_produto vp
    JOIN venda ON venda.id = vp.id_venda
    WHERE vp.id_produto = @produto_menos_id
    GROUP BY YEAR(venda.data_venda), MONTH(venda.data_venda)
    ORDER BY qtd_vendida_no_mes DESC, ganho_no_mes DESC
    LIMIT 1;

    SELECT
        YEAR(venda.data_venda) AS ano,
        MONTH(venda.data_venda) AS mes,
        SUM(vp.qtd)   AS qtd_vendida_no_mes,
        SUM(vp.valor) AS ganho_no_mes
    FROM venda_produto vp
    JOIN venda ON venda.id = vp.id_venda
    WHERE vp.id_produto = @produto_menos_id
    GROUP BY YEAR(venda.data_venda), MONTH(venda.data_venda)
    ORDER BY qtd_vendida_no_mes ASC, ganho_no_mes ASC
    LIMIT 1;

    -- cleanup
    DROP TEMPORARY TABLE IF EXISTS tmp_produtos;
END$$

DELIMITER ;

-- USUÁRIOS, ROLES E PERMISSÕES

-- Cria roles
CREATE ROLE IF NOT EXISTS 'role_admin';
CREATE ROLE IF NOT EXISTS 'role_gerente';
CREATE ROLE IF NOT EXISTS 'role_funcionario';

-- Permissões para cada ROLE

-- Admin: total controle
GRANT ALL PRIVILEGES ON ecommerce.* TO 'role_admin';

-- Gerente: acesso de leitura e edição aos principais dados
GRANT SELECT, UPDATE, DELETE ON ecommerce.venda TO 'role_gerente';
GRANT SELECT, UPDATE, DELETE ON ecommerce.venda_produto TO 'role_gerente';
GRANT SELECT, UPDATE, DELETE ON ecommerce.produto TO 'role_gerente';
GRANT SELECT, UPDATE, DELETE ON ecommerce.cliente TO 'role_gerente';
GRANT SELECT, UPDATE, DELETE ON ecommerce.cliente_especial TO 'role_gerente';
GRANT SELECT, UPDATE, DELETE ON ecommerce.funcionario_especial TO 'role_gerente';
GRANT EXECUTE ON ecommerce.* TO 'role_gerente';

-- Views úteis para o gerente
GRANT SELECT ON ecommerce.v_produto_vendas_totais TO 'role_gerente';
GRANT SELECT ON ecommerce.v_cliente_compras_e_status TO 'role_gerente';
GRANT SELECT ON ecommerce.v_vendas_mensais_produto TO 'role_gerente';

-- Funcionário: acesso limitado (leitura e inserção)
GRANT INSERT, SELECT ON ecommerce.venda TO 'role_funcionario';
GRANT INSERT, SELECT ON ecommerce.venda_produto TO 'role_funcionario';
GRANT SELECT, UPDATE ON ecommerce.produto TO 'role_funcionario';
GRANT SELECT ON ecommerce.cliente TO 'role_funcionario';
GRANT EXECUTE ON ecommerce.* TO 'role_funcionario';
GRANT UPDATE (quantidade_estoque) ON ecommerce.produto TO 'role_funcionario';

-- Views úteis para funcionário
GRANT SELECT ON ecommerce.v_produto_vendas_totais TO 'role_funcionario';
GRANT SELECT ON ecommerce.v_vendas_mensais_produto TO 'role_funcionario';

-- Criação dos usuários e atribuição de roles

CREATE USER IF NOT EXISTS 'admin'@'localhost' IDENTIFIED BY 'Senhateste1!';
CREATE USER IF NOT EXISTS 'gerente'@'localhost' IDENTIFIED BY 'Senhateste1!';
CREATE USER IF NOT EXISTS 'funcionario'@'localhost' IDENTIFIED BY 'Senhateste1!';

GRANT 'role_admin' TO 'admin'@'localhost';
GRANT 'role_gerente' TO 'gerente'@'localhost';
GRANT 'role_funcionario' TO 'funcionario'@'localhost';

FLUSH PRIVILEGES;

-- 6) INSERÇÕES DE TESTE (opcional)

INSERT INTO vendedor (nome, salario) VALUES 
('João Gabriel', 1500.00),
('Maria Silva', 1800.00);

INSERT INTO cliente (nome, idade, sexo, data_nascimento)
VALUES ('Lucas', 20, 'm', '2004-12-05');

INSERT INTO produto (nome, valor, quantidade_estoque, id_vendedor)
VALUES ('Biscoito', 100.00, 10, 1);

INSERT INTO transportadora(nome, cidade) VALUES ('SEDEX', 'Olinda');

INSERT INTO venda (data_venda, hora_venda, valor, endereco, id_cliente)
VALUES (CURDATE(), CURTIME(), 100.00, 'Recife', 1);
INSERT INTO transporte(id_venda,id_transportadora,valor) VALUES (1,1,10.00);
-- clientes

INSERT INTO cliente (nome, idade, sexo, data_nascimento) VALUES
('Alice Silva', 25, 'f', '1998-07-14'),
('Bruno Costa', 32, 'm', '1991-03-22'),
('Carla Souza', 28, 'f', '1995-11-30'),
('Daniel Lima', 40, 'm', '1983-05-10'),
('Eduarda Fernandes', 19, 'f', '2004-02-05'),
('Fernando Alves', 35, 'm', '1988-09-17'),
('Gabriela Rocha', 23, 'f', '2000-12-03'),
('Henrique Martins', 30, 'm', '1993-06-18'),
('Isabela Pereira', 27, 'f', '1996-08-25'),
('João Santos', 33, 'm', '1990-01-09'),
('Karina Dias', 29, 'f', '1994-10-15'),
('Leonardo Melo', 38, 'm', '1985-04-02'),
('Mariana Castro', 26, 'f', '1997-07-21'),
('Nicolas Cardoso', 31, 'm', '1992-11-11'),
('Olívia Moreira', 24, 'f', '1999-03-29'),
('Pedro Almeida', 36, 'm', '1987-12-12'),
('Quésia Nunes', 22, 'f', '2001-05-07'),
('Rafael Teixeira', 39, 'm', '1984-08-23'),
('Sofia Ribeiro', 21, 'f', '2002-09-01'),
('Tiago Gomes', 34, 'm', '1989-02-28'),
('Ursula Carvalho', 27, 'f', '1996-06-14'),
('Victor Andrade', 28, 'm', '1995-10-30'),
('Wesley Santana', 37, 'm', '1986-01-19'),
('Ximena Pacheco', 23, 'f', '2000-04-06'),
('Yuri Lopes', 32, 'm', '1991-07-12'),
('Zara Moura', 25, 'f', '1998-11-09'),
('Arthur Campos', 29, 'm', '1994-03-21'),
('Bianca Faria', 30, 'f', '1993-12-05'),
('Caio Ribeiro', 31, 'm', '1992-06-17'),
('Diana Lopes', 24, 'f', '1999-09-29'),
('Emanuel Costa', 35, 'm', '1988-01-08'),
('Fabiana Martins', 26, 'f', '1997-04-19'),
('Gustavo Almeida', 33, 'm', '1990-10-02'),
('Helena Rocha', 28, 'f', '1995-02-23'),
('Igor Souza', 36, 'm', '1987-05-30'),
('Júlia Fernandes', 22, 'f', '2001-07-15'),
('Kevin Dias', 27, 'm', '1996-12-28'),
('Lara Melo', 25, 'f', '1998-08-10'),
('Mateus Castro', 38, 'm', '1985-03-03'),
('Natália Nunes', 23, 'f', '2000-01-21'),
('Otávio Teixeira', 29, 'm', '1994-11-11'),
('Patrícia Ribeiro', 31, 'f', '1992-05-25'),
('Quentin Gomes', 34, 'm', '1989-09-14'),
('Raquel Carvalho', 28, 'f', '1995-06-19'),
('Samuel Andrade', 37, 'm', '1986-12-07'),
('Tatiane Santana', 26, 'f', '1997-03-02'),
('Ulisses Pacheco', 32, 'm', '1991-07-26'),
('Vanessa Lopes', 24, 'f', '1999-10-04'),
('William Moura', 35, 'm', '1988-02-15'),
('Xavier Campos', 30, 'm', '1993-08-21'),
('Yasmin Faria', 27, 'f', '1996-11-30'),
('Zeca Ribeiro', 33, 'm', '1990-01-27'),
('Ana Souza', 25, 'f', '1998-05-11'),
('Bruno Fernandes', 36, 'm', '1987-09-09'),
('Carla Dias', 28, 'f', '1995-12-01'),
('Diego Melo', 31, 'm', '1992-04-17'),
('Elaine Castro', 29, 'f', '1994-07-28'),
('Fábio Nunes', 32, 'm', '1991-03-05'),
('Giovana Teixeira', 24, 'f', '1999-08-16'),
('Heitor Ribeiro', 27, 'm', '1996-11-20'),
('Isadora Gomes', 30, 'f', '1993-02-02'),
('Jonas Carvalho', 35, 'm', '1988-06-13'),
('Kelly Andrade', 23, 'f', '2000-09-09'),
('Leandro Santana', 38, 'm', '1985-12-22'),
('Marina Pacheco', 26, 'f', '1997-01-14'),
('Nathan Lopes', 31, 'm', '1992-05-30'),
('Olívia Moura', 25, 'f', '1998-08-07'),
('Paulo Campos', 34, 'm', '1989-11-18'),
('Quésia Faria', 29, 'f', '1994-03-29'),
('Ricardo Ribeiro', 36, 'm', '1987-07-03'),
('Sabrina Souza', 28, 'f', '1995-12-15'),
('Thiago Fernandes', 33, 'm', '1990-06-09'),
('Úrsula Dias', 27, 'f', '1996-01-26'),
('Vitor Melo', 32, 'm', '1991-09-10'),
('Wanda Castro', 24, 'f', '1999-04-21'),
('Xander Nunes', 30, 'm', '1993-11-05'),
('Yara Teixeira', 26, 'f', '1997-08-13'),
('Zion Ribeiro', 31, 'm', '1992-02-28'),
('Amanda Gomes', 23, 'f', '2000-07-07'),
('Bruno Carvalho', 35, 'm', '1988-10-20'),
('Caroline Andrade', 29, 'f', '1994-05-15'),
('Diego Santana', 28, 'm', '1995-01-02'),
('Evelyn Pacheco', 27, 'f', '1996-03-08'),
('Felipe Lopes', 34, 'm', '1989-07-23'),
('Gabriela Moura', 25, 'f', '1998-11-17'),
('Hugo Campos', 36, 'm', '1987-04-04'),
('Isabel Faria', 30, 'f', '1993-06-28'),
('João Ribeiro', 32, 'm', '1991-12-12'),
('Karina Souza', 24, 'f', '1999-09-30'),
('Lucas Fernandes', 33, 'm', '1990-05-06'),
('Mariana Dias', 26, 'f', '1997-02-19'),
('Natan Melo', 31, 'm', '1992-08-21'),
('Olívia Castro', 28, 'f', '1995-11-03'),
('Paulo Nunes', 35, 'm', '1988-01-29'),
('Queila Teixeira', 23, 'f', '2000-06-10'),
('Rafael Ribeiro', 30, 'm', '1993-03-25'),
('Sofia Gomes', 27, 'f', '1996-09-18'),
('Thiago Carvalho', 36, 'm', '1987-12-07'),
('Úrsula Andrade', 29, 'f', '1994-04-22'),
('Victor Santana', 32, 'm', '1991-08-11'),
('Wesley Pacheco', 25, 'm', '1998-02-14'),
('Yasmin Lopes', 26, 'f', '1997-10-30'),
('Zara Moura', 31, 'f', '1992-01-05');
